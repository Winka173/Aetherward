using System;
using System.Collections.Generic;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Run
{
    /// <summary>A scripted build plan used by the headless simulator and integration tests.</summary>
    public sealed class Strategy
    {
        public string Name;
        public string[] Starters;
        public string[] RecruitPriority;     // preferred heroes, in order
        public string[] RelicPriority;
        public string[] CardPriority;        // preferred cards (else scored generically)
        public string[] EvolutionPriority;   // preferred evolution ids
        public bool TakePacts;
        public float RepairBelow = 0.5f;

        public static readonly Strategy[] Archetypes =
        {
            new Strategy
            {
                Name = "thunderstorm",
                Starters = new[] { "marina", "volt" },
                RecruitPriority = new[] { "zephyr", "sylph", "tidal", "terra", "raiden", "glacius" },
                RelicPriority = new[] { "thunder_relay", "storm_caller", "chain_conductor", "spark_of_genesis", "mana_battery" },
                CardPriority = new[] { "static_field", "storm_front", "storm_choir", "spec_volt_arc_lattice", "catalyst_surge", "steam_engine", "tidebound" },
                EvolutionPriority = new[] { "volt_circuit_conductor", "marina_torrent_caller", "zephyr_cyclone_sage", "sylph_tempest_archer" }
            },
            new Strategy
            {
                Name = "frozen_fortress",
                Starters = new[] { "terra", "freya" },
                RecruitPriority = new[] { "glacius", "marina", "tidal", "magnus", "volt", "sylph" },
                RelicPriority = new[] { "frozen_crown", "frozen_heart", "stoneheart", "crystal_growth", "iron_bulwark" },
                CardPriority = new[] { "permafrost", "glacial_vow", "bedrock_oath", "spec_freya_whiteout", "spec_terra_sanctum", "crystal_lattice" },
                EvolutionPriority = new[] { "freya_crystalbinder", "terra_bedrock_warden", "glacius_permafrost_sentinel", "marina_tide_saint" }
            },
            new Strategy
            {
                Name = "magma_engine",
                Starters = new[] { "cinder", "ignis" },
                RecruitPriority = new[] { "magnus", "terra", "zephyr", "marina", "freya", "sylph" },
                RelicPriority = new[] { "eternal_ember", "steam_reactor", "war_drum", "spark_of_genesis", "iron_bulwark" },
                CardPriority = new[] { "magma_core", "pyre_covenant", "bedrock_oath", "spec_ignis_pyroclasm", "spec_cinder_wildfire", "spec_magnus_fault_line" },
                EvolutionPriority = new[] { "ignis_ember_weaver", "cinder_ash_guardian", "magnus_quake_champion" }
            },
            new Strategy
            {
                Name = "mixed_burst",
                Starters = new[] { "ignis", "marina" },
                RecruitPriority = new[] { "raiden", "terra", "volt", "sylph", "tidal", "zephyr" },
                RelicPriority = new[] { "steam_reactor", "executioners_lens", "war_drum", "spark_of_genesis" },
                CardPriority = new[] { "steam_engine", "keen_edge", "catalyst_surge", "pyre_covenant", "spec_raiden_afterimage" },
                EvolutionPriority = new[] { "ignis_meteor_archmage", "marina_tide_saint", "raiden_static_executioner" }
            },
            new Strategy
            {
                Name = "glass_cannon",
                Starters = new[] { "sylph", "volt" },
                RecruitPriority = new[] { "ignis", "freya", "zephyr", "marina", "tidal", "terra" },
                RelicPriority = new[] { "glass_cannon", "quiver_of_gales", "war_drum", "mana_battery" },
                CardPriority = new[] { "long_reach", "sharpened_focus", "keen_edge", "swift_hands", "spec_sylph_volley" },
                EvolutionPriority = new[] { "sylph_tempest_archer", "volt_tempest_lord", "ignis_meteor_archmage" },
                TakePacts = true,
                RepairBelow = 0.6f
            },
            new Strategy
            {
                Name = "balanced",
                Starters = new[] { "terra", "ignis" },
                RecruitPriority = new[] { "marina", "volt", "freya", "sylph", "cinder", "zephyr" },
                RelicPriority = new[] { "crystal_growth", "spark_of_genesis", "war_drum", "stoneheart" },
                CardPriority = new[] { "sharpened_focus", "reinforced_plate", "catalyst_surge", "quick_cast" },
                EvolutionPriority = new string[0]
            }
        };

        public static Strategy Find(string name)
        {
            foreach (Strategy s in Archetypes) if (s.Name == name) return s;
            return null;
        }
    }

    /// <summary>
    /// Plays the between-wave decisions of a run according to a <see cref="Strategy"/>. It only uses
    /// the public RunController commands, exactly like the UI, so it doubles as an integration test.
    /// </summary>
    public sealed class AutoPilot
    {
        private readonly RunController _rc;
        private readonly Strategy _strategy;
        private readonly Pcg32 _rng;

        public AutoPilot(RunController rc, Strategy strategy)
        {
            _rc = rc;
            _strategy = strategy;
            _rng = Pcg32.Derive(rc.State.Seed, "autopilot:" + strategy.Name);
        }

        /// <summary>Plays the whole run headlessly. Returns false if it got stuck (should never happen).</summary>
        public bool PlayToEnd(int maxSteps = 2000)
        {
            for (int step = 0; step < maxSteps; step++)
            {
                RunState s = _rc.State;
                switch (s.Phase)
                {
                    case RunPhase.Prepare:
                        Prepare();
                        if (_rc.StartWave() == null) return false;
                        break;
                    case RunPhase.Battle:
                        _rc.Battle.RunToEnd();
                        _rc.ResolveBattle();
                        break;
                    case RunPhase.Reward:
                        HandleReward();
                        break;
                    case RunPhase.Victory:
                    case RunPhase.Defeat:
                        return true;
                }
            }
            return false;
        }

        public void Prepare()
        {
            RunState s = _rc.State;
            foreach (HeroRunState h in s.Heroes)
                if (h.Downed && s.Gold >= _rc.ReviveCost) _rc.Revive(h.Uid);
            if (s.CrystalHp < _rc.CrystalMaxHp * _strategy.RepairBelow)
                for (int i = 0; i < 3 && s.CrystalHp < _rc.CrystalMaxHp * _strategy.RepairBelow; i++)
                    if (!_rc.RepairCrystal()) break;
            foreach (HeroRunState h in s.Heroes)
            {
                if (!_rc.CanEvolve(h)) continue;
                _rc.Evolve(h.Uid, PickEvolution(h));
            }
            Formation.AutoArrange(_rc);
        }

        private string PickEvolution(HeroRunState h)
        {
            List<string> options = _rc.Content.Heroes[h.DefId].Evolutions;
            foreach (string pref in _strategy.EvolutionPriority) if (options.Contains(pref)) return pref;
            return options[_rng.Range(0, options.Count)];
        }

        private void HandleReward()
        {
            RunState s = _rc.State;
            List<Offer> offers = s.Offers;
            switch (s.CurrentReward)
            {
                case RewardKind.Draft:
                    _rc.Choose(BestCard(offers));
                    break;
                case RewardKind.Pact:
                    if (_strategy.TakePacts && offers.Count > 0) _rc.Choose(0);
                    else _rc.Skip();
                    break;
                case RewardKind.Recruit:
                {
                    int pick = BestHero(offers);
                    if (pick < 0 || !_rc.Choose(pick)) _rc.Skip();
                    break;
                }
                case RewardKind.Relic:
                    _rc.Choose(BestRelic(offers));
                    break;
                case RewardKind.Evolution:
                {
                    bool any = false;
                    foreach (HeroRunState h in s.Heroes)
                    {
                        if (!_rc.CanEvolve(h)) continue;
                        any |= _rc.Evolve(h.Uid, PickEvolution(h));
                    }
                    _rc.Skip();
                    break;
                }
                case RewardKind.Event:
                {
                    // Take the first affordable option (events always offer a free last option).
                    for (int i = 0; i < offers.Count; i++)
                        if (_rc.Choose(i)) return;
                    break;
                }
                case RewardKind.Shop:
                    Shop();
                    _rc.Skip();
                    break;
            }
            if (s.Phase == RunPhase.Reward && ReferenceEquals(offers, s.Offers) && s.CurrentReward == RewardKind.Draft) _rc.Skip();
        }

        private void Shop()
        {
            RunState s = _rc.State;
            for (int pass = 0; pass < 6; pass++)
            {
                int best = -1;
                float bestScore = 0f;
                for (int i = 0; i < s.Offers.Count; i++)
                {
                    Offer o = s.Offers[i];
                    if (o.Sold || o.Price > s.Gold) continue;
                    float score = 0f;
                    switch (o.Kind)
                    {
                        case OfferKind.Hero: score = s.Heroes.Count < 6 ? 10f + Priority(_strategy.RecruitPriority, o.Id) : 0f; break;
                        case OfferKind.Revive: score = 9f; break;
                        case OfferKind.Repair: score = s.CrystalHp < _rc.CrystalMaxHp * _strategy.RepairBelow ? 8f : 0f; break;
                        case OfferKind.Relic: score = 5f + Priority(_strategy.RelicPriority, o.Id); break;
                        case OfferKind.Card: score = 3f + Priority(_strategy.CardPriority, o.Id); break;
                    }
                    if (score > bestScore) { bestScore = score; best = i; }
                }
                if (best < 0 || !_rc.Choose(best)) break;
            }
        }

        private static float Priority(string[] list, string id)
        {
            for (int i = 0; i < list.Length; i++) if (list[i] == id) return 5f - i * 0.5f;
            return 0f;
        }

        private int BestCard(List<Offer> offers)
        {
            int best = 0;
            float bestScore = float.MinValue;
            for (int i = 0; i < offers.Count; i++)
            {
                CardDef c = _rc.Content.Cards[offers[i].Id];
                float score = Priority(_strategy.CardPriority, c.Id) * 2f + (int)c.Rarity * 0.6f + (DraftGenerator.IsSynergy(c) ? 1.5f : 0f) + _rng.NextFloat();
                if (c.DrawbackKey != null && !_strategy.TakePacts) score -= 2f;
                if (score > bestScore) { bestScore = score; best = i; }
            }
            return best;
        }

        private int BestHero(List<Offer> offers)
        {
            int best = -1;
            float bestScore = float.MinValue;
            for (int i = 0; i < offers.Count; i++)
            {
                if (offers[i].Price > _rc.State.Gold) continue;
                float score = Priority(_strategy.RecruitPriority, offers[i].Id) + _rng.NextFloat();
                if (score > bestScore) { bestScore = score; best = i; }
            }
            return best;
        }

        private int BestRelic(List<Offer> offers)
        {
            int best = 0;
            float bestScore = float.MinValue;
            for (int i = 0; i < offers.Count; i++)
            {
                RelicDef r = _rc.Content.Relics[offers[i].Id];
                float score = Priority(_strategy.RelicPriority, r.Id) * 2f + (int)r.Rarity * 0.5f + (_rc.CompletesFusion(r.Id) ? 4f : 0f) + _rng.NextFloat();
                if (r.Id == "glass_cannon" && !_strategy.TakePacts) score -= 3f;
                if (score > bestScore) { bestScore = score; best = i; }
            }
            return best;
        }
    }

    /// <summary>Formation helper shared by the auto-pilot and the UI "auto arrange" button.</summary>
    public static class Formation
    {
        /// <summary>
        /// Melee heroes guard the inner ring facing the telegraphed lanes; ranged heroes take outer
        /// nodes closest to the upcoming lanes. Deterministic.
        /// </summary>
        public static void AutoArrange(RunController rc)
        {
            RunState s = rc.State;
            ArenaDef arena = rc.Content.Arena;
            WaveDef wave = rc.Content.Waves[Math.Min(s.Wave, rc.Content.Waves.Count) - 1];
            List<int> lanes = Battle.LanesForWave(wave);
            var taken = new HashSet<int>();
            var melee = new List<HeroRunState>();
            var ranged = new List<HeroRunState>();
            foreach (HeroRunState h in s.Heroes)
            {
                HeroDef d = rc.Content.Heroes[h.DefId];
                bool isMelee = d.Melee;
                if (!string.IsNullOrEmpty(h.EvolutionId) && rc.Content.Evolutions[h.EvolutionId].MeleeOverride.HasValue)
                    isMelee = rc.Content.Evolutions[h.EvolutionId].MeleeOverride.Value;
                (isMelee ? melee : ranged).Add(h);
            }
            foreach (HeroRunState h in melee) h.Node = PickNode(arena, lanes, taken, true, rc.Content.Heroes[h.DefId].Role == HeroRole.Guardian);
            foreach (HeroRunState h in ranged) h.Node = PickNode(arena, lanes, taken, false, false);
        }

        private static int PickNode(ArenaDef arena, List<int> lanes, HashSet<int> taken, bool melee, bool guardian)
        {
            int best = -1;
            float bestScore = float.MaxValue;
            for (int n = 0; n < arena.Nodes.Count; n++)
            {
                if (taken.Contains(n)) continue;
                Vec2 p = arena.Nodes[n];
                float laneDist = float.MaxValue;
                foreach (int l in lanes)
                {
                    LaneDef lane = arena.Lanes[l % arena.Lanes.Count];
                    for (int i = 0; i < lane.Points.Count - 1; i++)
                        laneDist = Math.Min(laneDist, Vec2.DistanceToSegment(p, lane.Points[i], lane.Points[i + 1]));
                }
                float radius = p.Length;
                // Melee: stand on/near a lane close to the crystal. Ranged: outer ring, near lanes but not on them.
                float score = melee
                    ? laneDist * 2f + radius * (guardian ? 0.6f : 0.3f)
                    : Math.Abs(laneDist - 1.2f) + Math.Abs(radius - 4f) * 0.5f;
                // Spread out: penalise nodes adjacent to already-taken ones.
                foreach (int t in taken) if (Vec2.Distance(arena.Nodes[t], p) < 2.2f) score += 0.8f;
                if (score < bestScore) { bestScore = score; best = n; }
            }
            if (best >= 0) taken.Add(best);
            return best;
        }
    }
}
