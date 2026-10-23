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

        // ------------------------------------------------------------------ modes

        /// <summary>Waves in this run: 20 (Classic/Daily), the boss count (Boss Rush), 0 = unbounded (Endless).</summary>
        /// <summary>Ascension "rarity_shift": epic/legendary offers become rarer.</summary>
        public float RarityShift(Rarity r) =>
            r == Rarity.Epic || r == Rarity.Legendary ? Math.Max(0.1f, 1f - Content.Difficulty.Value("rarity_shift", State.Ascension)) : 1f;

        public const int RunHeroPoolSize = 18;
        public const int RunRelicPoolSize = 45;

        private bool InHeroPool(string id) => State.HeroPool.Count == 0 || State.HeroPool.Contains(id);
        private bool InRelicPool(string id) => State.RelicPool.Count == 0 || State.RelicPool.Contains(id);

        /// <summary>
        /// Run pools keep a large catalog coherent: each run offers a seeded subset of heroes and relics,
        /// weighted toward the starters' elements and their signature partners (bond partners always in).
        /// Small unlock sets (new players) are left whole. Different seeds explore different subsets.
        /// </summary>
        internal void DrawRunPools()
        {
            State.HeroPool.Clear();
            State.RelicPool.Clear();
            Pcg32 rng = Pcg32.Derive(State.Seed, "runpool");
            var heroes = new List<string>();
            foreach (HeroDef h in Content.HeroList) if (Unlocks.Heroes.Contains(h.Id) && !State.HasHero(h.Id)) heroes.Add(h.Id);
            if (heroes.Count > RunHeroPoolSize)
            {
                var must = new List<string>();
                foreach (string id in heroes) if (BondFor(id) != null) must.Add(id);
                State.HeroPool.AddRange(must);
                var rest = heroes.FindAll(id => !must.Contains(id));
                WeightedFill(rng, rest, State.HeroPool, RunHeroPoolSize, id =>
                {
                    HeroDef d = Content.Heroes[id];
                    float w = 1f + 1.2f * Math.Min(2, SignatureCount(d.Element));
                    foreach (HeroRunState o in State.Heroes) if (Content.Heroes[o.DefId].Element == d.Element) w += 0.8f;
                    return w;
                });
                foreach (HeroRunState o in State.Heroes) State.HeroPool.Add(o.DefId);
            }
            var relics = new List<string>();
            foreach (RelicDef r in Content.RelicList) if (!r.Fusion && Unlocks.Relics.Contains(r.Id)) relics.Add(r.Id);
            if (relics.Count > RunRelicPoolSize)
            {
                WeightedFill(rng, relics, State.RelicPool, RunRelicPoolSize, id => ElementRelevance(Content.Relics[id]));
                // Keep fusion recipes completable: a pooled half pulls its partner in.
                foreach (FusionDef f in Content.Fusions)
                {
                    bool a = State.RelicPool.Contains(f.A), b = State.RelicPool.Contains(f.B);
                    if (a && !b && Unlocks.Relics.Contains(f.B)) State.RelicPool.Add(f.B);
                    if (b && !a && Unlocks.Relics.Contains(f.A)) State.RelicPool.Add(f.A);
                }
            }
            State.HeroPool.Sort(string.CompareOrdinal);
            State.RelicPool.Sort(string.CompareOrdinal);
        }

        private static void WeightedFill(Pcg32 rng, List<string> candidates, List<string> into, int size, Func<string, float> weight)
        {
            var pool = new List<string>(candidates);
            while (into.Count < size && pool.Count > 0)
            {
                float total = 0f;
                var w = new float[pool.Count];
                for (int i = 0; i < pool.Count; i++) { w[i] = Math.Max(0.05f, weight(pool[i])); total += w[i]; }
                float roll = rng.NextFloat() * total;
                int pick = pool.Count - 1;
                for (int i = 0; i < pool.Count; i++) { roll -= w[i]; if (roll <= 0f) { pick = i; break; } }
                if (!into.Contains(pool[pick])) into.Add(pool[pick]);
                pool.RemoveAt(pick);
            }
        }

        /// <summary>Compact, copyable build summary: seed, mode, difficulty, biome, heroes (+evolution), relics.</summary>
        public string ShareCode()
        {
            var heroes = new List<string>();
            foreach (HeroRunState h in State.Heroes) heroes.Add(h.DefId + (h.EvolutionId != null ? "+" + h.EvolutionId : ""));
            return "AW1 seed=" + Pcg32.FormatSeed(State.Seed) + " mode=" + State.Mode + " asc=" + State.Ascension + " biome=" + (State.BiomeId ?? "default") +
                   " heroes=" + string.Join(",", heroes) + " relics=" + string.Join(",", State.Relics);
        }

        public int TotalWaves => State.Mode == GameMode.Endless ? 0 : State.Mode == GameMode.BossRush ? BossRushBosses().Count : Content.Waves.Count;

        public WaveDef CurrentWave => WaveAt(State.Wave);

        /// <summary>The wave definition for a wave number in this run's mode (deterministic, never saved).</summary>
        public WaveDef WaveAt(int number)
        {
            number = Math.Max(1, number);
            switch (State.Mode)
            {
                case GameMode.Endless:
                {
                    if (number <= Content.Waves.Count) return Content.Waves[number - 1];
                    // Loop the second half (waves 11-20) with +30% enemy HP per loop; wave 20 (final boss) gets rewards.
                    int over = number - Content.Waves.Count - 1;
                    WaveDef t = Content.Waves[10 + over % 10];
                    WaveDef w = t.CloneAs(number);
                    w.Level = Content.Waves.Count + over + 1;   // keeps climbing the authored HP curve
                    w.ScalePct = 0.25f * (over / 10 + 1);
                    if (w.Rewards.Count == 0) { w.Rewards.Add(RewardKind.Relic); w.Rewards.Add(RewardKind.Draft); }
                    if (w.Gold <= 0) w.Gold = 30;
                    return w;
                }
                case GameMode.BossRush:
                {
                    List<string> bosses = BossRushBosses();
                    int i = Math.Min(number, bosses.Count) - 1;
                    // Stage template: the authored mid boss wave first, the final boss wave for the last third.
                    WaveDef t = Content.Waves[i < bosses.Count * 2 / 3 ? 9 : Content.Waves.Count - 1];
                    WaveDef w = t.CloneAs(number);
                    w.Level = 6 + (int)Math.Round(14f * i / Math.Max(1, bosses.Count - 1));
                    w.BossPool = new List<string> { bosses[i] };
                    w.Groups = new List<SpawnGroup>();
                    foreach (SpawnGroup g in t.Groups)
                    {
                        if (Content.Enemies.TryGetValue(g.Enemy, out EnemyDef ed) && ed.Boss)
                            w.Groups.Add(new SpawnGroup { Enemy = bosses[i], Count = 1, Lane = g.Lane, Start = g.Start, Interval = g.Interval });
                        else w.Groups.Add(g);
                    }
                    w.Rewards = new List<RewardKind> { RewardKind.Relic, RewardKind.Recruit, RewardKind.Evolution };
                    w.Gold = 25;
                    w.Essence = 2;
                    return w;
                }
                default:
                    return Content.Waves[Math.Min(number, Content.Waves.Count) - 1];
            }
        }

        /// <summary>Boss Rush order: every boss, weakest first (by HP), ties by id. Deterministic.</summary>
        public List<string> BossRushBosses()
        {
            var list = new List<EnemyDef>();
            foreach (EnemyDef e in Content.Enemies.Values) if (e.Boss) list.Add(e);
            list.Sort((a, b) => { int d = a.Hp.CompareTo(b.Hp); return d != 0 ? d : string.CompareOrdinal(a.Id, b.Id); });
            return list.ConvertAll(e => e.Id);
        }

        /// <summary>Daily key and seed for a UTC date: everyone gets the same run that day.</summary>
        public static string DailyKeyFor(DateTime utc) => utc.ToString("yyyyMMdd", System.Globalization.CultureInfo.InvariantCulture);

        public static ulong DailySeed(string key) => Pcg32.Hash64("daily:" + key);

        public static readonly string[] DailyModifierPool = { "haste", "armored", "swarm" };

        /// <summary>Starts a mode run. Daily derives seed, biome and two modifiers from the date key.</summary>
        public static RunController NewModeRun(ContentDatabase content, GameMode mode, ulong seed, IList<string> starters, int ascension,
                                               RunUnlocks unlocks, string biomeId = null, string dailyKey = null)
        {
            if (mode == GameMode.Daily)
            {
                dailyKey ??= DailyKeyFor(DateTime.UtcNow);
                seed = DailySeed(dailyKey);
                Pcg32 rng = Pcg32.Derive(seed, "daily");
                var biomes = content.BiomeList;
                biomeId = biomes[rng.Range(0, biomes.Count)].Id;
            }
            RunController rc = NewRun(content, seed, starters, ascension, unlocks, biomeId);
            rc.State.Mode = mode;
            if (mode == GameMode.Daily)
            {
                rc.State.DailyKey = dailyKey;
                Pcg32 rng = Pcg32.Derive(seed, "daily:mods");
                var pool = new List<string>(DailyModifierPool);
                for (int k = 0; k < 2 && pool.Count > 0; k++)
                {
                    int i = rng.Range(0, pool.Count);
                    rc.State.ModeModifiers.Add(pool[i]);
                    pool.RemoveAt(i);
                }
                rc.State.ModeModifiers.Sort(string.CompareOrdinal); // a set: stable order (matches saves)
            }
            if (mode == GameMode.BossRush)
            {
                // Bosses from stage 1: start with a seasoned squad of four (two extra recruits from the unlocked pool) and a war chest.
                Pcg32 rng = Pcg32.Derive(seed, "bossrush:squad");
                foreach (string id in rc.PickHeroes(rng, 2)) rc.AddHero(id, 1).Node = rc.FreeNode();
                foreach (HeroRunState h in rc.State.Heroes) h.Level = Math.Min(content.Economy.LevelCap, 3);
                rc.State.Gold += 30;
            }
            return rc;
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
            rc.RollSealedGate();
            rc.DrawRunPools();
            s.Trace("new run seed=" + Pcg32.FormatSeed(seed) + " starters=" + string.Join(",", starters) + " asc=" + ascension);
            return rc;
        }

        internal HeroRunState AddHero(string defId, int level)
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
            if (State.Mode == GameMode.BossRush) return wave.BossPool[0];
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
            for (int n = 0; n < System.Math.Max(Arena.Nodes.Count, Eco.MaxHeroes); n++)
                if (State.HeroOnNode(n) == null) return n;
            return -1;
        }

        /// <summary>
        /// Ascension: seal one active entrance for the coming wave (deterministic per seed/wave).
        /// Enemy groups redirect to another entrance; preparation displays the sealed gate.
        /// </summary>
        public void RollSealedGate()
        {
            State.BlockedNode = -1;
            State.SealedGate = -1;
            if (!Content.Difficulty.Has("sealed_gate", State.Ascension)) return;
            var gates = new List<int>();
            foreach (int lane in Battle.LanesForWave(CurrentWave, Biome))
            {
                int gate = Battle.GateLane(Arena, lane);
                if (!gates.Contains(gate)) gates.Add(gate);
            }
            // At least one other entrance remains open; groups concentrate there.
            if (gates.Count > 1)
                State.SealedGate = gates[Pcg32.Derive(State.Seed, "seal:" + State.Wave).Range(0, gates.Count)];
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
            foreach (BondDef b in ActiveBonds())
                foreach (EffectOp op in b.Effects) yield return op;
        }

        /// <summary>Bonds whose two heroes are both in the roster.</summary>
        public List<BondDef> ActiveBonds()
        {
            var list = new List<BondDef>();
            foreach (BondDef b in Content.Bonds)
                if (State.HasHero(b.A) && State.HasHero(b.B)) list.Add(b);
            return list;
        }

        /// <summary>The bond an offered hero would complete with the current roster, if any.</summary>
        public BondDef BondFor(string heroId)
        {
            foreach (BondDef b in Content.Bonds)
                if (b.Involves(heroId) && State.HasHero(b.Partner(heroId))) return b;
            return null;
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
                return Eco.RerollBaseCost + Eco.RerollCostStep * State.RerollsThisScreen + (int)Content.Difficulty.Value("reroll_cost", State.Ascension);
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
            foreach (BondDef b in ActiveBonds())
                foreach (EffectOp op in b.Effects) m.Add(op, "bond:" + b.Id);
            DifficultyDef d = Content.Difficulty;
            m.EnemySpeedPct += d.Value("enemy_speed", State.Ascension);
            m.EnemyDamagePct += d.Value("enemy_damage", State.Ascension);
            m.EnemyHpPct += d.Value("enemy_hp", State.Ascension);
            return m;
        }

        public BattleSetup BuildBattleSetup()
        {
            WaveDef wave = CurrentWave;
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
            setup.ExtraWaveModifiers.AddRange(State.ModeModifiers);
            if (Content.Difficulty.Has("frenzy", State.Ascension)) setup.ExtraWaveModifiers.Add("ascension_frenzy");
            setup.EliteExtraAffix = Content.Difficulty.Has("elite_affix", State.Ascension);
            setup.BossEnrage = Content.Difficulty.Value("boss_enrage", State.Ascension);
            setup.EliteEvery = (int)Content.Difficulty.Value("double_elite", State.Ascension);
            setup.Tactic = State.Tactic;
            setup.Stance = State.Stance;
            setup.Formation = State.Formation;
            setup.SealedGate = State.SealedGate;
            setup.CrystalPath = State.CrystalPath;
            setup.UtilityTargeting = FeatureFlags.UtilityTargeting;
            setup.DynamicParty = FeatureFlags.DynamicParty;
            setup.HazardShift = Content.Difficulty.Value("hazard_shift", State.Ascension);
            foreach (HeroRunState h in State.Heroes)
            {
                if (!FeatureFlags.DynamicParty && h.Node < 0) continue;
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
            if (FeatureFlags.DynamicParty) anyPlaced = State.Heroes.Exists(h => !h.Downed);
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
                HeroTravel = b.Stats.HeroTravel,
                CrystalHits = b.Stats.CrystalHits,
                Cleared = b.Outcome == BattleOutcome.Cleared
            };
            record.Insights.AddRange(BattleInsights.ForWave(b));
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

            if (TotalWaves > 0 && wave.Number >= TotalWaves)
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
            if (State.CrystalEvolutionEnabled && State.CrystalPath == null && wave.Number >= Combat.CrystalPaths.OfferAfterWave)
                State.PendingRewards.Insert(0, RewardKind.CrystalEvolution);
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
            for (int i = 0; i < s.DamageByKind.Length; i++) State.DamageByKind[i] += s.DamageByKind[i];
            State.ShieldAbsorbed += s.HeroShieldAbsorbed;
            if (s.MaxProcDepth > State.MaxProcDepth) State.MaxProcDepth = s.MaxProcDepth;
            foreach (var kv in s.CrystalDamageByEnemy)
            {
                State.CrystalDamageByEnemy.TryGetValue(kv.Key, out float d);
                State.CrystalDamageByEnemy[kv.Key] = d + kv.Value;
            }
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
            RollSealedGate();
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
                case RewardKind.CrystalEvolution:
                    foreach (string id in Combat.CrystalPaths.All) State.Offers.Add(new Offer { Kind = OfferKind.CrystalPath, Id = id });
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

        /// <summary>Locks (or unlocks) one shop offer so it survives rerolls and waits in the next shop.</summary>
        public bool ToggleLock(int index)
        {
            if (State.Phase != RunPhase.Reward || State.CurrentReward != RewardKind.Shop || index < 0 || index >= State.Offers.Count) return false;
            Offer o = State.Offers[index];
            if (o.Sold || (o.Kind != OfferKind.Hero && o.Kind != OfferKind.Relic && o.Kind != OfferKind.Card)) return false;
            bool same = State.LockedOffer != null && State.LockedOffer.Kind == o.Kind && State.LockedOffer.Id == o.Id;
            State.LockedOffer = same ? null : new Offer { Kind = o.Kind, Id = o.Id, Price = o.Price, TraitId = o.TraitId, Tag = "locked" };
            return true;
        }

        public bool IsLocked(Offer o) => State.LockedOffer != null && State.LockedOffer.Kind == o.Kind && State.LockedOffer.Id == o.Id;

        private bool LockStillValid(Offer o)
        {
            switch (o.Kind)
            {
                case OfferKind.Hero: return Content.Heroes.ContainsKey(o.Id) && !State.HasHero(o.Id) && State.Heroes.Count < Eco.MaxHeroes;
                case OfferKind.Relic: return Content.Relics.ContainsKey(o.Id) && !State.Relics.Contains(o.Id);
                case OfferKind.Card: return Content.Cards.TryGetValue(o.Id, out CardDef c) && State.CardStacks(o.Id) < c.MaxStacks;
                default: return false;
            }
        }

        private void GenerateShop()
        {
            if (State.LockedOffer != null)
            {
                if (LockStillValid(State.LockedOffer))
                    State.Offers.Add(new Offer { Kind = State.LockedOffer.Kind, Id = State.LockedOffer.Id, Price = State.LockedOffer.Price, TraitId = State.LockedOffer.TraitId, Tag = "locked" });
                else State.LockedOffer = null;
            }
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

        internal List<string> PickHeroes(Pcg32 rng, int count)
        {
            var pool = new List<string>();
            foreach (HeroDef h in Content.HeroList)
                if (Unlocks.Heroes.Contains(h.Id) && !State.HasHero(h.Id) && InHeroPool(h.Id)) pool.Add(h.Id);
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
                    if (BondFor(d.Id) != null) w += 1.0f; // completing a bond is worth surfacing
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
            // Synergy guarantee: at least one recruit forms a signature reaction with the roster when any can.
            if (result.Count > 1 && !result.Exists(id => SignatureCount(Content.Heroes[id].Element) > 0))
            {
                var synergy = pool.FindAll(id => SignatureCount(Content.Heroes[id].Element) > 0);
                if (synergy.Count > 0) result[result.Count - 1] = synergy[rng.Range(0, synergy.Count)];
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
                if (!r.Fusion && Unlocks.Relics.Contains(r.Id) && !State.Relics.Contains(r.Id) && !FusedAway(r.Id) && InRelicPool(r.Id)) pool.Add(r);
            var result = new List<string>();
            while (result.Count < count && pool.Count > 0)
            {
                float total = 0f;
                var weights = new float[pool.Count];
                for (int i = 0; i < pool.Count; i++)
                {
                    float w = DraftGenerator.RarityWeight(pool[i].Rarity, State.Wave) * RarityShift(pool[i].Rarity);
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
            // Relevance guarantee: if nothing offered matches the team's elements but something could, swap the last pick.
            if (result.Count > 1 && !result.Exists(id => ElementRelevance(Content.Relics[id]) > 1f))
            {
                var relevant = pool.FindAll(r => ElementRelevance(r) > 1f);
                if (relevant.Count > 0) result[result.Count - 1] = relevant[rng.Range(0, relevant.Count)].Id;
            }
            return result;
        }

        /// <summary>
        /// Element-tagged relics lean toward the team's elements (x3 when one matches, x0.3 when none
        /// does) so a large catalog keeps offers relevant; untagged relics are unaffected.
        /// </summary>
        public float ElementRelevance(RelicDef r)
        {
            bool tagged = false;
            foreach (string tag in r.Tags)
            {
                if (!ElementUtil.TryParse(tag, out Element el) || el == Element.None) continue;
                tagged = true;
                foreach (HeroRunState h in State.Heroes)
                    if (Content.Heroes[h.DefId].Element == el) return 3f;
            }
            return tagged ? 0.3f : 1f;
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
                case OfferKind.CrystalPath:
                    // Permanent and exclusive: the first choice sticks for the whole run.
                    if (State.CrystalPath != null || !Combat.CrystalPaths.IsValid(o.Id)) return false;
                    State.CrystalPath = o.Id;
                    break;
            }
            o.Sold = true;
            if (IsLocked(o)) State.LockedOffer = null;
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
