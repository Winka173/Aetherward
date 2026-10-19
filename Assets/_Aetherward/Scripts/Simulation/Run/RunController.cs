using System;
using System.Collections.Generic;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Run
{
    /// <summary>Content the player has unlocked through meta progression (what can appear in a run).</summary>
    public sealed class RunUnlocks
    {
        public readonly HashSet<string> Heroes = new HashSet<string>();
        public readonly HashSet<string> Relics = new HashSet<string>();

        public static RunUnlocks Everything(ContentDatabase db)
        {
            var u = new RunUnlocks();
            foreach (HeroDef h in db.HeroList) u.Heroes.Add(h.Id);
            foreach (RelicDef r in db.RelicList) u.Relics.Add(r.Id);
            return u;
        }

        public static RunUnlocks Starter(ContentDatabase db)
        {
            var u = new RunUnlocks();
            foreach (HeroDef h in db.HeroList) if (h.StarterUnlocked) u.Heroes.Add(h.Id);
            foreach (RelicDef r in db.RelicList) if (r.StarterUnlocked) u.Relics.Add(r.Id);
            return u;
        }
    }

    /// <summary>
    /// Run orchestrator and the only writer of <see cref="RunState"/>. The UI reads state and calls
    /// these commands; every command validates phase/cost and returns false instead of throwing.
    /// Flow: Prepare -> Battle -> Reward* -> Prepare ... -> Victory/Defeat.
    /// </summary>
    public sealed class RunController
    {
        public readonly ContentDatabase Content;
        public readonly RunState State;
        public readonly RunUnlocks Unlocks;
        public Battle Battle { get; private set; }
        public event Action<string> Notice; // localized-key notices (fusion formed, level up...)

        private EconomyDef Eco => Content.Economy;
        public BiomeDef Biome => Content.BiomeOrDefault(State.BiomeId);
        public ArenaDef Arena => Biome.Arena;

        public RunController(ContentDatabase content, RunState state, RunUnlocks unlocks)
        {
            Content = content;
            State = state;
            Unlocks = unlocks ?? RunUnlocks.Everything(content);
        }

        public static RunController NewRun(ContentDatabase content, ulong seed, IList<string> starters, int ascension, RunUnlocks unlocks, string biomeId = null)
        {
            var s = new RunState
            {
                BiomeId = biomeId != null && content.Biomes.ContainsKey(biomeId) ? biomeId : null,
                Seed = seed,
                Ascension = ascension,
                Gold = content.Economy.StartGold,
                CrystalBaseMaxHp = content.Economy.CrystalHp * (1f + content.Difficulty.Value("crystal_max", ascension))
            };
            s.CrystalHp = s.CrystalBaseMaxHp;
            s.CrystalKnownMax = s.CrystalBaseMaxHp;
            var rc = new RunController(content, s, unlocks);
            int[] innerNodes = { 0, 2, 1, 3 };
            int[] outerNodes = { 4, 8, 6, 10 };
            int inner = 0, outer = 0;
            for (int i = 0; i < starters.Count; i++)
            {
                if (!content.Heroes.ContainsKey(starters[i])) throw new ArgumentException("Unknown starter hero " + starters[i]);
                HeroRunState h = rc.AddHero(starters[i], 1);
                // Melee starters guard the inner ring by default, ranged ones take the outer ring.
                h.Node = content.Heroes[starters[i]].Melee ? innerNodes[inner++ % innerNodes.Length] : outerNodes[outer++ % outerNodes.Length];
            }
            rc.RollBlockedNode();
            s.Trace("new run seed=" + Pcg32.FormatSeed(seed) + " starters=" + string.Join(",", starters) + " asc=" + ascension);
            return rc;
        }

        private HeroRunState AddHero(string defId, int level)
        {
            var h = new HeroRunState { Uid = State.NextHeroUid++, DefId = defId, Level = level, JoinedWave = State.Wave };
            h.Xp = level > 1 ? Eco.XpToLevel[Math.Min(level - 1, Eco.XpToLevel.Length - 1)] : 0;
            State.Heroes.Add(h);
            if (!State.SeenEnemies.Contains("hero:" + defId)) State.SeenEnemies.Add("hero:" + defId);
            return h;
        }

        /// <summary>Boss of a pooled wave for this run (chosen once from the seed, persisted in the save).</summary>
        public string BossFor(WaveDef wave)
        {
            if (wave.BossPool.Count == 0) return null;
            if (State.BossChoices.TryGetValue(wave.Number, out string id) && Content.Enemies.ContainsKey(id)) return id;
            Pcg32 rng = Pcg32.Derive(State.Seed, "boss:" + wave.Number);
            // A biome may restrict the wave's boss to its own faction bosses.
            List<string> pool = Biome.BossPools.TryGetValue(wave.Number, out List<string> bp) && bp.Count > 0 ? bp : wave.BossPool;
            id = pool[rng.Range(0, pool.Count)];
            State.BossChoices[wave.Number] = id;
            return id;
        }

        /// <summary>The enemy actually fought for an authored wave entry (after boss substitution).</summary>
        public string EnemyFor(WaveDef wave, string enemyId)
        {
            string boss = BossFor(wave);
            return boss != null && enemyId == wave.BossPool[0] ? boss : enemyId;
        }

        /// <summary>Enemies a wave will actually field in this run (boss choice, biome extras and swaps), for previews.</summary>
        public List<KeyValuePair<string, int>> PreviewEnemies(WaveDef wave)
        {
            var groups = new List<SpawnGroup>(wave.Groups);
            for (int i = 0; i < Biome.Extra.Count; i++)
                if (wave.Number >= Biome.ExtraWaves[i][0] && wave.Number <= Biome.ExtraWaves[i][1]) groups.Add(Biome.Extra[i]);
            var counts = new List<KeyValuePair<string, int>>();
            foreach (SpawnGroup g in groups)
            {
                string id = EnemyFor(wave, g.Enemy);
                if (Biome.Substitutions.TryGetValue(id, out string sub) && Content.Enemies.ContainsKey(sub)) id = sub;
                int idx = counts.FindIndex(k => k.Key == id);
                if (idx >= 0) counts[idx] = new KeyValuePair<string, int>(id, counts[idx].Value + g.Count);
                else counts.Add(new KeyValuePair<string, int>(id, g.Count));
            }
            return counts;
        }

        public int FreeNode()
        {
            int[] preference = { 4, 8, 0, 2, 1, 3, 6, 10, 5, 7, 9, 11 };
            foreach (int n in preference) if (n != State.BlockedNode && State.HeroOnNode(n) == null) return n;
            return -1;
        }

        /// <summary>
        /// Ascension: telegraph one blocked node for the coming wave (deterministic per seed/wave). Heroes on
        /// it are moved to a free node; the player sees it during preparation and can rearrange.
        /// </summary>
        public void RollBlockedNode()
        {
            State.BlockedNode = -1;
            if (!Content.Difficulty.Has("blocked_node", State.Ascension)) return;
            Pcg32 rng = Pcg32.Derive(State.Seed, "block:" + State.Wave);
            State.BlockedNode = rng.Range(0, Arena.Nodes.Count);
            HeroRunState on = State.HeroOnNode(State.BlockedNode);
            if (on != null)
            {
                on.Node = -1;
                on.Node = FreeNode();
            }
        }

        // ================================================================== economy helpers

        private float EconomyParam(string key)
        {
            float total = 0f;
            foreach (EffectOp op in ActiveOps())
                if (op.Op == "economy") total += op.Params.Get(key);
            return total;
        }

        /// <summary>All effect ops from relics, card stacks and pacts (economy ops included).</summary>
        public IEnumerable<EffectOp> ActiveOps()
        {
            foreach (string id in State.Relics)
                if (Content.Relics.TryGetValue(id, out RelicDef r))
                    foreach (EffectOp op in r.Effects) yield return op;
            foreach (var kv in State.Cards)
                if (Content.Cards.TryGetValue(kv.Key, out CardDef c))
                    for (int s = 0; s < kv.Value; s++)
                        foreach (EffectOp op in c.Effects) yield return op;
        }

        public float CrystalMaxHp
        {
            get
            {
                float pct = 0f, flat = 0f;
                foreach (EffectOp op in ActiveOps())
                {
                    if (op.Op != "crystal") continue;
                    pct += op.Params.Get("maxHpPct");
                    flat += op.Params.Get("maxHp");
                }
                return Math.Max(100f, State.CrystalBaseMaxHp * (1f + pct) + flat);
            }
        }

        public float PriceScale => (1f + Eco.ShopPriceGrowthPerWave * (State.Wave - 1)) * Math.Max(0.4f, 1f - EconomyParam("shopDiscount"))
                                   * (1f + Content.Difficulty.Value("shop_prices", State.Ascension));

        public int ReviveCost => (int)Math.Ceiling((Eco.ReviveBaseCost + Eco.ReviveCostPerWave * State.Wave) * Math.Max(0.3f, 1f - EconomyParam("reviveDiscount")));
        public int RepairCost => (int)Math.Ceiling(Eco.RepairCost * PriceScale);

        public int RerollCost
        {
            get
            {
                if (State.FreeRerollsLeft > 0) return 0;
                return Eco.RerollBaseCost + Eco.RerollCostStep * State.RerollsThisScreen;
            }
        }

        private bool Spend(int amount)
        {
            if (amount < 0 || State.Gold < amount) return false;
            State.Gold -= amount;
            State.GoldSpentTotal += amount;
            return true;
        }

        // ================================================================== preparation commands

        public bool PlaceHero(int heroUid, int node)
        {
            if (State.Phase != RunPhase.Prepare) return false;
            if (node < 0 || node >= Arena.Nodes.Count || node == State.BlockedNode) return false;
            HeroRunState h = State.Hero(heroUid);
            if (h == null) return false;
            HeroRunState occupant = State.HeroOnNode(node);
            if (occupant == h) return true;
            if (occupant != null) occupant.Node = h.Node; // swap, free of cost
            h.Node = node;
            return true;
        }

        public bool Revive(int heroUid)
        {
            if (State.Phase != RunPhase.Prepare && !(State.Phase == RunPhase.Reward && State.CurrentReward == RewardKind.Shop)) return false;
            HeroRunState h = State.Hero(heroUid);
            if (h == null || !h.Downed) return false;
            if (!Spend(ReviveCost)) return false;
            h.Downed = false;
            h.HpFraction = 0.6f;
            State.Trace("revive " + h.DefId);
            return true;
        }

        public bool RepairCrystal()
        {
            if (State.Phase != RunPhase.Prepare && !(State.Phase == RunPhase.Reward && State.CurrentReward == RewardKind.Shop)) return false;
            float max = CrystalMaxHp;
            if (State.CrystalHp >= max - 0.5f) return false;
            if (!Spend(RepairCost)) return false;
            State.CrystalHp = Math.Min(max, State.CrystalHp + max * Eco.RepairPct);
            State.Trace("repair crystal");
            return true;
        }

        public bool CanEvolve(HeroRunState h)
        {
            return h != null && string.IsNullOrEmpty(h.EvolutionId) && h.Level >= Eco.LevelCap && State.Essence >= Eco.EvolutionEssence;
        }

        public bool Evolve(int heroUid, string evolutionId)
        {
            if (State.Phase != RunPhase.Prepare && !(State.Phase == RunPhase.Reward && State.CurrentReward == RewardKind.Evolution)) return false;
            HeroRunState h = State.Hero(heroUid);
            if (!CanEvolve(h)) return false;
            HeroDef def = Content.Heroes[h.DefId];
            if (!def.Evolutions.Contains(evolutionId)) return false;
            State.Essence -= Eco.EvolutionEssence;
            h.EvolutionId = evolutionId;
            h.HpFraction = 1f;
            State.Trace("evolve " + h.DefId + " -> " + evolutionId);
            Notice?.Invoke("notice.evolved");
            if (State.Phase == RunPhase.Reward) RefreshEvolutionOffers();
            return true;
        }

        /// <summary>Ends the run as a defeat at the player's request (counts as a finished run).</summary>
        public void Abandon()
        {
            if (State.Finished) return;
            Battle = null;
            State.DefeatSource = "abandoned";
            State.Phase = RunPhase.Defeat;
            State.Trace("abandoned at wave " + State.Wave);
        }

        // ================================================================== battle

        public BattleModifiers BuildModifiers()
        {
            var m = new BattleModifiers();
            foreach (string id in State.Relics)
                if (Content.Relics.TryGetValue(id, out RelicDef r))
                    foreach (EffectOp op in r.Effects) m.Add(op, id);
            foreach (string id in State.CardOrder)
                if (Content.Cards.TryGetValue(id, out CardDef c))
                    foreach (EffectOp op in c.Effects) m.Add(op, id, State.CardStacks(id));
            DifficultyDef d = Content.Difficulty;
            m.EnemySpeedPct += d.Value("enemy_speed", State.Ascension);
            m.EnemyDamagePct += d.Value("enemy_damage", State.Ascension);
            m.EnemyHpPct += d.Value("enemy_hp", State.Ascension);
            return m;
        }

        public BattleSetup BuildBattleSetup()
        {
            WaveDef wave = Content.Waves[State.Wave - 1];
            var setup = new BattleSetup
            {
                Content = Content,
                Wave = wave,
                Seed = State.Seed,
                Modifiers = BuildModifiers(),
                CrystalMaxHp = CrystalMaxHp,
                Ascension = State.Ascension,
                MaxActiveEnemies = Eco.MaxActiveEnemies,
                Biome = Biome
            };
            setup.CrystalHp = Math.Min(State.CrystalHp, setup.CrystalMaxHp);
            string boss = BossFor(wave);
            if (boss != null && boss != wave.BossPool[0]) setup.Substitutions[wave.BossPool[0]] = boss;
            setup.ExtraWaveModifiers.AddRange(State.NextWaveModifiers);
            if (Content.Difficulty.Has("frenzy", State.Ascension)) setup.ExtraWaveModifiers.Add("ascension_frenzy");
            setup.EliteExtraAffix = Content.Difficulty.Has("elite_affix", State.Ascension);
            setup.BossEnrage = Content.Difficulty.Value("boss_enrage", State.Ascension);
            foreach (HeroRunState h in State.Heroes)
            {
                if (h.Node < 0) continue;
                setup.Heroes.Add(new HeroLoadout
                {
                    Def = Content.Heroes[h.DefId],
                    RosterIndex = State.Heroes.IndexOf(h),
                    NodeIndex = h.Node,
                    Level = h.Level,
                    EvolutionId = h.EvolutionId,
                    HpFraction = h.HpFraction,
                    Downed = h.Downed,
                    TraitId = h.TraitId,
                    Awakened = h.Awakened != null && ElementUtil.TryParse(h.Awakened, out Element aw) ? aw : Element.None
                });
            }
            return setup;
        }

        public Battle StartWave()
        {
            if (State.Phase != RunPhase.Prepare) return null;
            bool anyPlaced = false;
            foreach (HeroRunState h in State.Heroes) if (h.Node >= 0) anyPlaced = true;
            if (!anyPlaced) return null;
            Battle = new Battle(BuildBattleSetup());
            State.Phase = RunPhase.Battle;
            State.Trace("start wave " + State.Wave);
            return Battle;
        }

        /// <summary>Call once the battle outcome is no longer Running. Applies rewards and advances.</summary>
        public void ResolveBattle()
        {
            if (State.Phase != RunPhase.Battle || Battle == null || Battle.Outcome == BattleOutcome.Running) return;
            Battle b = Battle;
            WaveDef wave = b.Wave;
            State.ActiveSeconds += b.Time;
            State.NextWaveModifiers.Clear();

            foreach (HeroUnit u in b.Heroes)
            {
                HeroRunState h = State.Heroes[u.RosterIndex];
                h.DamageDealt += u.DamageDealt;
                h.HealingDone += u.HealingDone;
                h.DamageTaken += u.DamageTaken;
                h.Kills += u.Kills;
                h.Reactions += u.ReactionsTriggered;
                h.SkillCasts += u.SkillCasts;
                if (!u.Alive && !h.Downed) h.TimesDowned++;
                h.Downed = !u.Alive;
                h.HpFraction = u.Alive ? Math.Min(1f, u.HpFraction + Eco.SurvivorHealPct) : 0f;
            }
            MergeStats(b.Stats);

            var record = new WaveRecord
            {
                Wave = wave.Number,
                Duration = b.Time,
                CrystalDamage = b.Crystal.DamageTakenThisWave,
                CrystalHpAfter = Math.Max(0f, b.Crystal.Hp),
                Kills = b.Stats.Kills,
                Leaks = b.Stats.Leaks,
                Reactions = b.Stats.TotalReactions,
                HeroDowns = b.Stats.HeroDowns,
                PeakEnemies = b.Stats.PeakEnemies,
                PeakReactionsPerSecond = b.Stats.PeakReactionsPerSecond,
                Cleared = b.Outcome == BattleOutcome.Cleared
            };
            State.CrystalHp = Math.Max(0f, b.Crystal.Hp);

            if (b.Outcome == BattleOutcome.CrystalDestroyed)
            {
                State.DefeatSource = b.DefeatSource;
                State.WaveLog.Add(record);
                State.Phase = RunPhase.Defeat;
                State.Trace("defeat wave " + wave.Number + " by " + b.DefeatSource);
                Battle = null;
                return;
            }

            // Gold: wave reward + kills + interest on unspent gold, plus economy modifiers.
            int interestCap = Eco.InterestCap + (int)EconomyParam("interestCap");
            int interest = Math.Min(interestCap, (int)(State.Gold / 10f * Eco.InterestPer10));
            float goldMult = 1f + EconomyParam("goldPct");
            int gold = (int)Math.Round((wave.Gold + b.Stats.GoldFromKills + EconomyParam("waveGold")) * goldMult) + interest;
            State.Gold += gold;
            State.GoldEarnedTotal += gold;
            record.GoldEarned = gold;
            int essence = wave.Essence + b.Stats.EssenceFromKills + (wave.Boss || wave.Elite ? (int)EconomyParam("essenceOnElite") : 0);
            State.Essence += essence;
            State.WaveLog.Add(record);

            int xp = Eco.XpPerWave + (wave.Boss ? Eco.XpBossBonus : 0) + (int)EconomyParam("xpBonus");
            foreach (HeroRunState h in State.Heroes) GrantXp(h, xp);

            foreach (string id in Battle.Content.Enemies.Keys)
                if (b.Stats.CrystalDamageByEnemy.ContainsKey(id) && !State.SeenEnemies.Contains(id)) State.SeenEnemies.Add(id);
            foreach (SpawnGroup g in wave.Groups)
            {
                string id = EnemyFor(wave, g.Enemy);
                if (!State.SeenEnemies.Contains(id)) State.SeenEnemies.Add(id);
            }

            State.Trace("cleared wave " + wave.Number + " gold+" + gold + " essence+" + essence);
            Battle = null;

            if (wave.Number >= Content.Waves.Count)
            {
                State.Phase = RunPhase.Victory;
                return;
            }

            State.PendingRewards.Clear();
            State.PendingRewards.AddRange(wave.Rewards);
            // Guarantee a recruitment path: if the roster is small and no recruit/shop is scheduled
            // for a long stretch, add a recruit offer (no softlock on RNG).
            if (State.Heroes.Count < 3 && wave.Number >= 3 && !State.PendingRewards.Contains(RewardKind.Recruit) && !State.PendingRewards.Contains(RewardKind.Shop))
                State.PendingRewards.Add(RewardKind.Recruit);
            AdvanceReward();
        }

        private void GrantXp(HeroRunState h, int xp)
        {
            if (h.Level >= Eco.LevelCap) return;
            h.Xp += xp;
            while (h.Level < Eco.LevelCap && h.Xp >= Eco.XpToLevel[h.Level])
            {
                h.Level++;
                State.Trace("level " + h.DefId + " -> " + h.Level);
                Notice?.Invoke("notice.level_up");
            }
        }

        private void MergeStats(BattleStats s)
        {
            foreach (var kv in s.ReactionCounts)
            {
                State.ReactionCounts.TryGetValue(kv.Key, out int c);
                State.ReactionCounts[kv.Key] = c + kv.Value;
            }
            foreach (var kv in s.ReactionDamage)
            {
                State.ReactionDamage.TryGetValue(kv.Key, out float d);
                State.ReactionDamage[kv.Key] = d + kv.Value;
            }
            foreach (var kv in s.SourceActivations)
            {
                State.SourceActivations.TryGetValue(kv.Key, out int c);
                State.SourceActivations[kv.Key] = c + kv.Value;
            }
            foreach (var kv in s.SourceDamage)
            {
                State.SourceDamage.TryGetValue(kv.Key, out float d);
                State.SourceDamage[kv.Key] = d + kv.Value;
            }
            for (int i = 0; i < s.ElementDamage.Length; i++) State.ElementDamage[i] += s.ElementDamage[i];
        }

        // ================================================================== rewards

        /// <summary>Moves to the next pending reward screen, skipping screens with nothing to offer.</summary>
        public void AdvanceReward()
        {
            while (State.PendingRewards.Count > 0)
            {
                RewardKind kind = State.PendingRewards[0];
                State.PendingRewards.RemoveAt(0);
                State.CurrentReward = kind;
                State.RerollsThisScreen = 0;
                State.FreeRerollsLeft = (int)EconomyParam("freeRerolls");
                State.Offers.Clear();
                GenerateOffers(kind);
                if (State.Offers.Count > 0)
                {
                    State.Phase = RunPhase.Reward;
                    return;
                }
            }
            State.Offers.Clear();
            State.Phase = RunPhase.Prepare;
            State.Wave++;
            RollBlockedNode();
            AutoPlaceNewHeroes();
        }

        private void AutoPlaceNewHeroes()
        {
            foreach (HeroRunState h in State.Heroes)
                if (h.Node < 0) h.Node = FreeNode();
        }

        private Pcg32 OfferRng(string screen)
        {
            return Pcg32.Derive(State.Seed, screen + ":" + State.Wave + ":" + State.TotalRerolls);
        }

        private void GenerateOffers(RewardKind kind)
        {
            switch (kind)
            {
                case RewardKind.Draft:
                    foreach (CardDef c in DraftGenerator.Generate(this, OfferRng("draft"), 3, false))
                        State.Offers.Add(new Offer { Kind = OfferKind.Card, Id = c.Id, Tag = DraftGenerator.TagFor(this, c) });
                    break;
                case RewardKind.Pact:
                    foreach (CardDef c in DraftGenerator.Generate(this, OfferRng("pact"), 2, true))
                        State.Offers.Add(new Offer { Kind = OfferKind.Pact, Id = c.Id, Tag = "cursed" });
                    break;
                case RewardKind.Recruit:
                {
                    if (State.Heroes.Count >= Eco.MaxHeroes) break;
                    // Four choices: the expansion roster is large, so recruitment needs more agency.
                    foreach (string id in PickHeroes(OfferRng("recruit"), 4))
                        State.Offers.Add(new Offer { Kind = OfferKind.Hero, Id = id, Price = HeroPrice(id), TraitId = RollTrait(id) });
                    break;
                }
                case RewardKind.Relic:
                    foreach (string id in PickRelics(OfferRng("relic"), 3))
                        State.Offers.Add(new Offer { Kind = OfferKind.Relic, Id = id });
                    break;
                case RewardKind.Shop:
                    GenerateShop();
                    break;
                case RewardKind.Evolution:
                    RefreshEvolutionOffers();
                    break;
                case RewardKind.Event:
                {
                    var ids = new List<string>(Content.Events.Keys);
                    ids.Sort(string.CompareOrdinal);
                    if (ids.Count == 0) break;
                    string eventId = ids[OfferRng("event").Range(0, ids.Count)];
                    State.CurrentEventId = eventId;
                    EventDef ev = Content.Events[eventId];
                    for (int i = 0; i < ev.Options.Count; i++)
                        State.Offers.Add(new Offer { Kind = OfferKind.EventOption, Id = eventId, OptionIndex = i });
                    break;
                }
            }
            foreach (Offer o in State.Offers) State.Trace("offer " + kind + " " + o.Kind + ":" + o.Id + " $" + o.Price);
        }

        private void GenerateShop()
        {
            Pcg32 rng = OfferRng("shop");
            if (State.Heroes.Count < Eco.MaxHeroes)
                foreach (string id in PickHeroes(rng, 2))
                    State.Offers.Add(new Offer { Kind = OfferKind.Hero, Id = id, Price = HeroPrice(id), TraitId = RollTrait(id) });
            foreach (string id in PickRelics(rng, 2))
                State.Offers.Add(new Offer { Kind = OfferKind.Relic, Id = id, Price = RelicPrice(id) });
            foreach (CardDef c in DraftGenerator.Generate(this, rng, 2, false))
                State.Offers.Add(new Offer { Kind = OfferKind.Card, Id = c.Id, Price = CardPrice(c), Tag = DraftGenerator.TagFor(this, c) });
            State.Offers.Add(new Offer { Kind = OfferKind.Repair, Id = "repair", Price = RepairCost });
            foreach (HeroRunState h in State.Heroes)
                if (h.Downed) State.Offers.Add(new Offer { Kind = OfferKind.Revive, Id = h.DefId, HeroUid = h.Uid, Price = ReviveCost });
        }

        private void RefreshEvolutionOffers()
        {
            State.Offers.Clear();
            foreach (HeroRunState h in State.Heroes)
            {
                if (!CanEvolve(h)) continue;
                foreach (string evo in Content.Heroes[h.DefId].Evolutions)
                    State.Offers.Add(new Offer { Kind = OfferKind.Evolution, Id = evo, HeroUid = h.Uid, Price = Eco.EvolutionEssence });
            }
        }

        public int HeroPrice(string id)
        {
            return (int)Math.Ceiling(Content.Heroes[id].RecruitCost * PriceScale);
        }

        public int RelicPrice(string id)
        {
            RelicDef r = Content.Relics[id];
            return (int)Math.Ceiling(r.Price * PriceScale);
        }

        public int CardPrice(CardDef c)
        {
            int baseCost;
            switch (c.Rarity)
            {
                case Rarity.Rare: baseCost = 8; break;
                case Rarity.Epic: baseCost = 11; break;
                case Rarity.Legendary: baseCost = 15; break;
                case Rarity.Cursed: baseCost = 6; break;
                default: baseCost = 5; break;
            }
            return (int)Math.Ceiling(baseCost * PriceScale);
        }

        private List<string> PickHeroes(Pcg32 rng, int count)
        {
            var pool = new List<string>();
            foreach (HeroDef h in Content.HeroList)
                if (Unlocks.Heroes.Contains(h.Id) && !State.HasHero(h.Id)) pool.Add(h.Id);
            // Prefer elements/roles the roster lacks so recruitment broadens options.
            var result = new List<string>();
            while (result.Count < count && pool.Count > 0)
            {
                float total = 0f;
                var weights = new float[pool.Count];
                for (int i = 0; i < pool.Count; i++)
                {
                    HeroDef d = Content.Heroes[pool[i]];
                    float w = 1f;
                    bool hasElement = false, hasRole = false;
                    foreach (HeroRunState o in State.Heroes)
                    {
                        HeroDef od = Content.Heroes[o.DefId];
                        if (od.Element == d.Element) hasElement = true;
                        if (od.Role == d.Role) hasRole = true;
                    }
                    if (!hasElement) w += 0.6f;
                    if (!hasRole) w += 0.4f;
                    // Larger roster: favour heroes whose element forms a signature reaction with the team.
                    w += 0.6f * System.Math.Min(3, SignatureCount(d.Element));
                    weights[i] = w;
                    total += w;
                }
                float roll = rng.NextFloat() * total;
                int pick = pool.Count - 1;
                for (int i = 0; i < pool.Count; i++)
                {
                    roll -= weights[i];
                    if (roll <= 0f) { pick = i; break; }
                }
                result.Add(pool[pick]);
                pool.RemoveAt(pick);
            }
            return result;
        }

        /// <summary>Distinct roster elements an element would form an authored (signature) reaction with.</summary>
        public int SignatureCount(Element el)
        {
            int n = 0;
            ulong seen = 0;
            foreach (HeroRunState o in State.Heroes)
            {
                Element other = Content.Heroes[o.DefId].Element;
                if (other == el || (seen & (1UL << (int)other)) != 0) continue;
                seen |= 1UL << (int)other;
                ReactionDef r = Content.ReactionFor(el, other);
                if (r != null && r.Category == ReactionCategory.Signature) n++;
            }
            return n;
        }

        /// <summary>True when an element would create an authored (signature) reaction with someone already in the roster.</summary>
        public bool SignatureSynergy(Element el)
        {
            foreach (HeroRunState o in State.Heroes)
            {
                Element other = Content.Heroes[o.DefId].Element;
                if (other == el) continue;
                ReactionDef r = Content.ReactionFor(el, other);
                if (r != null && r.Category == ReactionCategory.Signature) return true;
            }
            return false;
        }

        private List<string> PickRelics(Pcg32 rng, int count)
        {
            var pool = new List<RelicDef>();
            foreach (RelicDef r in Content.RelicList)
                if (!r.Fusion && Unlocks.Relics.Contains(r.Id) && !State.Relics.Contains(r.Id) && !FusedAway(r.Id)) pool.Add(r);
            var result = new List<string>();
            while (result.Count < count && pool.Count > 0)
            {
                float total = 0f;
                var weights = new float[pool.Count];
                for (int i = 0; i < pool.Count; i++)
                {
                    float w = DraftGenerator.RarityWeight(pool[i].Rarity, State.Wave);
                    if (CompletesFusion(pool[i].Id)) w *= 1.8f; // gently surface curated fusions
                    w *= ElementRelevance(pool[i]);
                    weights[i] = w;
                    total += w;
                }
                float roll = rng.NextFloat() * total;
                int pick = pool.Count - 1;
                for (int i = 0; i < pool.Count; i++)
                {
                    roll -= weights[i];
                    if (roll <= 0f) { pick = i; break; }
                }
                result.Add(pool[pick].Id);
                pool.RemoveAt(pick);
            }
            return result;
        }

        /// <summary>
        /// Element-tagged relics lean toward the team's elements (x2 when one matches, x0.5 when none
        /// does) so a large catalog keeps offers relevant; untagged relics are unaffected.
        /// </summary>
        private float ElementRelevance(RelicDef r)
        {
            bool tagged = false;
            foreach (string tag in r.Tags)
            {
                if (!ElementUtil.TryParse(tag, out Element el) || el == Element.None) continue;
                tagged = true;
                foreach (HeroRunState h in State.Heroes)
                    if (Content.Heroes[h.DefId].Element == el) return 2f;
            }
            return tagged ? 0.5f : 1f;
        }

        private bool FusedAway(string relicId)
        {
            foreach (FusionDef f in Content.Fusions)
                if ((f.A == relicId || f.B == relicId) && State.Relics.Contains(f.Result)) return true;
            return false;
        }

        public bool CompletesFusion(string relicId)
        {
            foreach (FusionDef f in Content.Fusions)
            {
                if (f.A == relicId && State.Relics.Contains(f.B)) return true;
                if (f.B == relicId && State.Relics.Contains(f.A)) return true;
            }
            return false;
        }

        /// <summary>Selects/buys the offer at index. Draft/relic/recruit/pact/event screens end on choice.</summary>
        public bool Choose(int index)
        {
            if (State.Phase != RunPhase.Reward || index < 0 || index >= State.Offers.Count) return false;
            Offer o = State.Offers[index];
            if (o.Sold) return false;
            bool endsScreen = State.CurrentReward != RewardKind.Shop && State.CurrentReward != RewardKind.Evolution;

            switch (o.Kind)
            {
                case OfferKind.Card:
                case OfferKind.Pact:
                    if (!Spend(o.Price)) return false;
                    AddCard(o.Id);
                    break;
                case OfferKind.Hero:
                    if (State.Heroes.Count >= Eco.MaxHeroes || State.HasHero(o.Id)) return false;
                    if (!Spend(o.Price)) return false;
                    AddRecruit(o.Id, o.TraitId);
                    break;
                case OfferKind.Relic:
                    if (!Spend(o.Price)) return false;
                    AddRelic(o.Id);
                    break;
                case OfferKind.Repair:
                {
                    float max = CrystalMaxHp;
                    if (State.CrystalHp >= max - 0.5f) return false;
                    if (!Spend(o.Price)) return false;
                    State.CrystalHp = Math.Min(max, State.CrystalHp + max * Eco.RepairPct);
                    o.Price = RepairCost;
                    return true; // repair can be bought repeatedly
                }
                case OfferKind.Revive:
                {
                    HeroRunState h = State.Hero(o.HeroUid);
                    if (h == null || !h.Downed || !Spend(o.Price)) return false;
                    h.Downed = false;
                    h.HpFraction = 0.6f;
                    break;
                }
                case OfferKind.Evolution:
                    return Evolve(o.HeroUid, o.Id);
                case OfferKind.EventOption:
                    if (!ApplyEventOption(o.Id, o.OptionIndex)) return false;
                    break;
            }
            o.Sold = true;
            State.Trace("choose " + o.Kind + ":" + o.Id);
            if (endsScreen) AdvanceReward();
            return true;
        }

        public bool Reroll()
        {
            if (State.Phase != RunPhase.Reward) return false;
            RewardKind k = State.CurrentReward;
            if (k != RewardKind.Draft && k != RewardKind.Shop && k != RewardKind.Recruit) return false;
            int cost = RerollCost;
            if (!Spend(cost)) return false;
            if (State.FreeRerollsLeft > 0) State.FreeRerollsLeft--;
            else State.RerollsThisScreen++;
            State.TotalRerolls++;
            if (k == RewardKind.Shop)
            {
                // Rerolling the shop keeps repair/revive, replaces stock.
                State.Offers.Clear();
                GenerateShop();
            }
            else
            {
                State.Offers.Clear();
                GenerateOffers(k);
            }
            return true;
        }

        /// <summary>Leave the current screen (skip draft, leave shop, decline pact, finish evolving).</summary>
        public bool Skip()
        {
            if (State.Phase != RunPhase.Reward) return false;
            if (State.CurrentReward == RewardKind.Event) return false; // events always require a choice
            State.Trace("skip " + State.CurrentReward);
            AdvanceReward();
            return true;
        }

        public void AddCard(string id)
        {
            CardDef c = Content.Cards[id];
            int stacks = State.CardStacks(id);
            if (stacks >= c.MaxStacks) return;
            State.Cards[id] = stacks + 1;
            if (!State.CardOrder.Contains(id)) State.CardOrder.Add(id);
            if (c.Type == CardType.CursedPact) State.Pacts.Add(id);
            State.DraftsTaken++;
            ApplyImmediateCrystalChange();
        }

        public void AddRelic(string id)
        {
            if (State.Relics.Contains(id)) return;
            State.Relics.Add(id);
            foreach (FusionDef f in Content.Fusions)
            {
                if (!State.Relics.Contains(f.A) || !State.Relics.Contains(f.B)) continue;
                State.Relics.Remove(f.A);
                State.Relics.Remove(f.B);
                State.Relics.Add(f.Result);
                State.Trace("fusion " + f.A + " + " + f.B + " -> " + f.Result);
                Notice?.Invoke("notice.fusion");
            }
            ApplyImmediateCrystalChange();
        }

        /// <summary>Max HP changes from relics/pacts: gains add the delta to current HP, losses clamp.</summary>
        private void ApplyImmediateCrystalChange()
        {
            float max = CrystalMaxHp;
            float delta = max - State.CrystalKnownMax;
            if (delta > 0f) State.CrystalHp += delta;
            State.CrystalHp = Math.Min(State.CrystalHp, max);
            State.CrystalKnownMax = max;
        }

        private void AddRecruit(string id, string traitId)
        {
            int avg = 0;
            foreach (HeroRunState h in State.Heroes) avg += h.Level;
            int level = State.Heroes.Count > 0 ? Math.Max(1, avg / State.Heroes.Count - 1) : 1;
            HeroRunState hero = AddHero(id, level);
            hero.Node = FreeNode();
            if (traitId != null && Content.Traits.TryGetValue(traitId, out TraitDef t) && t.EligibleFor(Content.Heroes[id])) hero.TraitId = traitId;
            State.Trace("recruit " + id + " lvl" + level + (hero.TraitId != null ? " trait=" + hero.TraitId : ""));
        }

        /// <summary>Rarity-weighted trait for a recruit; only traits eligible for that hero's element/role.</summary>
        public string RollTrait(string heroId)
        {
            // Own RNG stream per offer: trait rolls never shift the hero/relic/card offer sequences.
            Pcg32 rng = Pcg32.Derive(State.Seed, "trait:" + State.Wave + ":" + State.TotalRerolls + ":" + heroId);
            HeroDef def = Content.Heroes[heroId];
            var pool = new List<TraitDef>();
            foreach (TraitDef t in Content.TraitList) if (t.EligibleFor(def)) pool.Add(t);
            if (pool.Count == 0) return null;
            float total = 0f;
            var weights = new float[pool.Count];
            for (int i = 0; i < pool.Count; i++)
            {
                float rw = pool[i].Rarity == Rarity.Common ? 1f : pool[i].Rarity == Rarity.Rare ? 0.6f : 0.3f;
                weights[i] = rw * pool[i].Weight;
                total += weights[i];
            }
            float roll = rng.NextFloat() * total;
            for (int i = 0; i < pool.Count; i++)
            {
                roll -= weights[i];
                if (roll <= 0f) return pool[i].Id;
            }
            return pool[pool.Count - 1].Id;
        }

        public const int MaxAwakenings = 2;

        /// <summary>
        /// Elemental Awakening (run-only): the highest-level eligible hero (level 2+, not yet awakened)
        /// gains a secondary element that forms a signature reaction with its own. At most
        /// <see cref="MaxAwakenings"/> per run. Deterministic per seed/wave. Returns the hero or null.
        /// </summary>
        public HeroRunState Awaken()
        {
            int awakened = 0;
            HeroRunState best = null;
            foreach (HeroRunState h in State.Heroes)
            {
                if (h.Awakened != null) { awakened++; continue; }
                if (h.Level < 2) continue;
                if (best == null || h.Level > best.Level || (h.Level == best.Level && h.Uid < best.Uid)) best = h;
            }
            if (best == null || awakened >= MaxAwakenings) return null;
            List<Element> options = AwakeningOptions(Content.Heroes[best.DefId].Element);
            if (options.Count == 0) return null;
            Pcg32 rng = Pcg32.Derive(State.Seed, "awaken:" + State.Wave + ":" + best.Uid);
            best.Awakened = ElementUtil.Key(options[rng.Range(0, options.Count)]);
            return best;
        }

        public bool CanAwaken()
        {
            int awakened = 0;
            bool eligible = false;
            foreach (HeroRunState h in State.Heroes)
            {
                if (h.Awakened != null) awakened++;
                else if (h.Level >= 2) eligible = true;
            }
            return eligible && awakened < MaxAwakenings;
        }

        /// <summary>Secondary elements that form an authored (signature) reaction with the primary.</summary>
        public List<Element> AwakeningOptions(Element primary)
        {
            var list = new List<Element>();
            foreach (Element el in ElementUtil.All)
            {
                if (el == primary) continue;
                ReactionDef r = Content.ReactionFor(primary, el);
                if (r != null && r.Category == ReactionCategory.Signature) list.Add(el);
            }
            return list;
        }

        private bool ApplyEventOption(string eventId, int option)
        {
            if (!Content.Events.TryGetValue(eventId, out EventDef ev) || option < 0 || option >= ev.Options.Count) return false;
            EventOption o = ev.Options[option];
            if (o.Gold < 0 && State.Gold < -o.Gold) return false;
            if (o.Essence < 0 && State.Essence < -o.Essence) return false;
            foreach (EffectOp op in o.Effects) if (op.Op == "awaken" && !CanAwaken()) return false;
            State.Gold += o.Gold;
            if (o.Gold > 0) State.GoldEarnedTotal += o.Gold;
            State.Essence += o.Essence;
            if (o.CrystalHpPct != 0f)
            {
                float max = CrystalMaxHp;
                State.CrystalHp = Math.Max(1f, Math.Min(max, State.CrystalHp + max * o.CrystalHpPct));
            }
            if (!string.IsNullOrEmpty(o.GrantRelic) && Content.Relics.ContainsKey(o.GrantRelic)) AddRelic(o.GrantRelic);
            if (!string.IsNullOrEmpty(o.WaveModifier)) State.NextWaveModifiers.Add(o.WaveModifier);
            foreach (EffectOp op in o.Effects)
            {
                if (op.Op == "card" && Content.Cards.ContainsKey(op.Params.GetString("id"))) AddCard(op.Params.GetString("id"));
                if (op.Op == "awaken") Awaken();
            }
            return true;
        }
    }
}
