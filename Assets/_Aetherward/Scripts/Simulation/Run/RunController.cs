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

        public RunController(ContentDatabase content, RunState state, RunUnlocks unlocks)
        {
            Content = content;
            State = state;
            Unlocks = unlocks ?? RunUnlocks.Everything(content);
        }

        public static RunController NewRun(ContentDatabase content, ulong seed, IList<string> starters, int ascension, RunUnlocks unlocks)
        {
            var s = new RunState
            {
                Seed = seed,
                Ascension = ascension,
                Gold = content.Economy.StartGold,
                CrystalBaseMaxHp = content.Economy.CrystalHp * (ascension >= 3 ? 0.85f : 1f)
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

        public int FreeNode()
        {
            int[] preference = { 4, 8, 0, 2, 1, 3, 6, 10, 5, 7, 9, 11 };
            foreach (int n in preference) if (State.HeroOnNode(n) == null) return n;
            return -1;
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

        public float PriceScale => (1f + Eco.ShopPriceGrowthPerWave * (State.Wave - 1)) * Math.Max(0.4f, 1f - EconomyParam("shopDiscount"));

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
            if (node < 0 || node >= Content.Arena.Nodes.Count) return false;
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
            if (State.Ascension >= 2) m.EnemySpeedPct += 0.08f;
            if (State.Ascension >= 4) m.EnemyDamagePct += 0.1f;
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
                MaxActiveEnemies = Eco.MaxActiveEnemies
            };
            setup.CrystalHp = Math.Min(State.CrystalHp, setup.CrystalMaxHp);
            setup.ExtraWaveModifiers.AddRange(State.NextWaveModifiers);
            if (State.Ascension >= 1) setup.ExtraWaveModifiers.Add("ascension_frenzy");
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
                    Downed = h.Downed
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
                if (!State.SeenEnemies.Contains(g.Enemy)) State.SeenEnemies.Add(g.Enemy);

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
                    if (State.Heroes.Count >= Eco.MaxHeroes) break;
                    foreach (string id in PickHeroes(OfferRng("recruit"), 3))
                        State.Offers.Add(new Offer { Kind = OfferKind.Hero, Id = id, Price = HeroPrice(id) });
                    break;
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
                    State.Offers.Add(new Offer { Kind = OfferKind.Hero, Id = id, Price = HeroPrice(id) });
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
                    AddRecruit(o.Id);
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

        private void AddRecruit(string id)
        {
            int avg = 0;
            foreach (HeroRunState h in State.Heroes) avg += h.Level;
            int level = State.Heroes.Count > 0 ? Math.Max(1, avg / State.Heroes.Count - 1) : 1;
            HeroRunState hero = AddHero(id, level);
            hero.Node = FreeNode();
            State.Trace("recruit " + id + " lvl" + level);
        }

        private bool ApplyEventOption(string eventId, int option)
        {
            if (!Content.Events.TryGetValue(eventId, out EventDef ev) || option < 0 || option >= ev.Options.Count) return false;
            EventOption o = ev.Options[option];
            if (o.Gold < 0 && State.Gold < -o.Gold) return false;
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
            }
            return true;
        }
    }
}
