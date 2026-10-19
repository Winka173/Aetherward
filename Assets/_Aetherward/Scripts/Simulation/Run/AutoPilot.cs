using System;
using System.Collections.Generic;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Run
{
    /// <summary>A scripted build plan used by the headless simulator and integration tests.</summary>
    public enum DraftPolicy
    {
        Scripted,
        Random,
        Synergy,
        Greedy
    }

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
        /// <summary>Draft policy (Phase 10 simulator): Scripted follows the priority lists; Random picks any
        /// affordable offer; Synergy ignores priorities and scores synergy/roles; Greedy takes the rarest.</summary>
        public DraftPolicy Policy = DraftPolicy.Scripted;

        /// <summary>A copy of this strategy with another draft policy (starters kept).</summary>
        public Strategy WithPolicy(DraftPolicy p)
        {
            var s = (Strategy)MemberwiseClone();
            s.Policy = p;
            s.Name = p == DraftPolicy.Scripted ? Name : Name + "/" + p.ToString().ToLowerInvariant();
            if (p != DraftPolicy.Scripted)
            {
                s.RecruitPriority = s.RelicPriority = s.CardPriority = s.EvolutionPriority = new string[0];
            }
            return s;
        }

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
                Name = "eclipse",
                Starters = new[] { "seren", "nyxara" },
                RecruitPriority = new[] { "ashara", "nerissa", "terra", "volt", "marina", "kael" },
                RelicPriority = new[] { "dawnstone", "nightfall_censer", "eclipse_engine", "verdict_scale", "radiant_lens", "sunforged_aegis" },
                CardPriority = new[] { "eclipse_theory", "night_oath", "dawn_vigil", "spec_nyxara_dread", "spec_seren_lightwell", "catalyst_surge" },
                EvolutionPriority = new[] { "nyxara_final_verdict", "seren_purifier", "ashara_vengeance_flames", "nerissa_catalyst_conductor" }
            },
            new Strategy
            {
                Name = "engineers",
                Starters = new[] { "borun", "voltrix" },
                RecruitPriority = new[] { "eirwen", "nerissa", "freya", "marina", "seren", "zephyr" },
                RelicPriority = new[] { "masons_level", "overclock_coil", "glacier_plate", "warding_bell", "thunder_relay" },
                CardPriority = new[] { "spec_voltrix_capacitor", "spec_borun_buttress", "spec_eirwen_rimeguard", "static_field", "permafrost" },
                EvolutionPriority = new[] { "voltrix_electric_network", "borun_fortifier", "eirwen_ice_bulwark", "nerissa_pure_healer" }
            },
            new Strategy
            {
                Name = "phoenix_gale",
                Starters = new[] { "ashara", "kael" },
                RecruitPriority = new[] { "ignis", "zephyr", "nerissa", "seren", "sylph", "cinder" },
                RelicPriority = new[] { "pyre_heart", "zephyr_sash", "executioners_oath", "eternal_ember", "war_drum" },
                CardPriority = new[] { "spec_ashara_ember_heart", "spec_kael_tailwind", "pyre_covenant", "gale_banner", "keen_edge" },
                EvolutionPriority = new[] { "ashara_rebirth_ward", "kael_storm_shepherd", "ignis_ember_weaver" }
            },
            new Strategy
            {
                Name = "verdant_plague",
                Starters = new[] { "liora", "vesper" },
                RecruitPriority = new[] { "marina", "volt", "thalen", "sable", "ignis", "terra" },
                RelicPriority = new[] { "verdant_seed", "venom_vial", "blight_lantern", "plague_bell", "worldroot_heart", "chain_conductor" },
                CardPriority = new[] { "wild_growth", "toxic_pact", "spec_liora_bramble", "spec_vesper_potency", "toxic_shock_theory", "overgrowth_theory" },
                EvolutionPriority = new[] { "liora_wildwood", "vesper_lingering_miasma", "sable_pandemic", "thalen_bramble_fortress" }
            },
            new Strategy
            {
                Name = "thorn_doctor",
                Starters = new[] { "thalen", "sable" },
                RecruitPriority = new[] { "liora", "ignis", "volt", "vesper", "marina", "seren" },
                RelicPriority = new[] { "thornmail", "antidote_flask", "venom_vial", "gardeners_trowel", "warding_bell", "chain_conductor" },
                CardPriority = new[] { "spec_thalen_heartwood", "spec_sable_triage", "toxic_pact", "wild_growth", "toxic_shock_theory" },
                EvolutionPriority = new[] { "thalen_bramble_fortress", "sable_remedy", "liora_spore_garden", "vesper_volatile_mixture" }
            },
            new Strategy
            {
                Name = "arcane_void",
                Starters = new[] { "caelis", "zerith" },
                RecruitPriority = new[] { "volt", "ignis", "oriane", "maelis", "zephyr", "marina" },
                RelicPriority = new[] { "echo_prism", "rune_inkwell", "void_lodestone", "null_shard", "infinite_codex", "event_horizon_core" },
                CardPriority = new[] { "arcane_accord", "void_covenant", "spec_caelis_resonant_echo", "spec_zerith_event_pull" },
                EvolutionPriority = new[] { "caelis_arcane_barrage", "zerith_singularity_lord", "oriane_grand_conductor", "maelis_null_bastion" }
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
                RunPhase p = _rc.State.Phase;
                if (p == RunPhase.Victory || p == RunPhase.Defeat) return true;
                if (!Step()) return false;
            }
            return false;
        }

        /// <summary>Advances one decision or battle; false when the run cannot continue (failed wave start).</summary>
        public bool Step()
        {
            switch (_rc.State.Phase)
            {
                case RunPhase.Prepare:
                    Prepare();
                    return _rc.StartWave() != null;
                case RunPhase.Battle:
                    _rc.Battle.RunToEnd();
                    _rc.ResolveBattle();
                    return true;
                case RunPhase.Reward:
                    HandleReward();
                    return true;
            }
            return true;
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
                case RewardKind.CrystalEvolution:
                {
                    // Hurt Crystal -> Bastion; otherwise Pulse (Random policy rolls). Thorn is left to players.
                    string want = _strategy.Policy == DraftPolicy.Random ? Combat.CrystalPaths.All[_rng.Range(0, 3)]
                        : s.CrystalHp < _rc.CrystalMaxHp * 0.6f ? Combat.CrystalPaths.Bastion : Combat.CrystalPaths.Pulse;
                    int idx = offers.FindIndex(o => o.Id == want);
                    if (idx < 0 || !_rc.Choose(idx)) _rc.Skip();
                    break;
                }
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
                score = PolicyScore(score, (int)c.Rarity);
                if (score > bestScore) { bestScore = score; best = i; }
            }
            return best;
        }

        /// <summary>Relics that weaken the Crystal or strengthen enemies are risk-reward picks.</summary>
        private static bool HasDrawback(List<EffectOp> ops)
        {
            foreach (EffectOp op in ops)
            {
                if (op.Op == "enemy") return true;
                if (op.Op == "crystal" && op.Params.Get("maxHpPct") < 0f) return true;
                if (op.Op == "stat" && op.Value < 0f) return true;
            }
            return false;
        }

        /// <summary>Random ignores the judgement entirely; Greedy only looks at rarity; others keep the score.</summary>
        private float PolicyScore(float judged, int rarity)
        {
            switch (_strategy.Policy)
            {
                case DraftPolicy.Random: return _rng.NextFloat();
                case DraftPolicy.Greedy: return rarity + _rng.NextFloat() * 0.5f;
                default: return judged;
            }
        }

        private int BestHero(List<Offer> offers)
        {
            int best = -1;
            float bestScore = float.MinValue;
            for (int i = 0; i < offers.Count; i++)
            {
                if (offers[i].Price > _rc.State.Gold) continue;
                HeroDef d = _rc.Content.Heroes[offers[i].Id];
                // Off-plan recruits are judged like a player would: synergy and filling missing roles.
                float score = Priority(_strategy.RecruitPriority, offers[i].Id) + 0.8f * Math.Min(3, _rc.SignatureCount(d.Element))
                              + RoleNeed(d.Role) + (_rc.BondFor(d.Id) != null ? 1.5f : 0f) + _rng.NextFloat();
                score = PolicyScore(score, 0);
                if (score > bestScore) { bestScore = score; best = i; }
            }
            return best;
        }

        /// <summary>A front-liner first, then sustain: what a player looks for when the plan's heroes are not offered.</summary>
        private float RoleNeed(HeroRole role)
        {
            bool guard = false, sustain = false;
            foreach (HeroRunState h in _rc.State.Heroes)
            {
                HeroRole r = _rc.Content.Heroes[h.DefId].Role;
                guard |= r == HeroRole.Guardian || r == HeroRole.Bruiser;
                sustain |= r == HeroRole.Healer || r == HeroRole.Support;
            }
            if (!guard && (role == HeroRole.Guardian || role == HeroRole.Bruiser)) return 1.2f;
            if (!sustain && (role == HeroRole.Healer || role == HeroRole.Support)) return 0.8f;
            return 0f;
        }

        private int BestRelic(List<Offer> offers)
        {
            int best = 0;
            float bestScore = float.MinValue;
            for (int i = 0; i < offers.Count; i++)
            {
                RelicDef r = _rc.Content.Relics[offers[i].Id];
                float score = Priority(_strategy.RelicPriority, r.Id) * 2f + (int)r.Rarity * 0.5f + (_rc.CompletesFusion(r.Id) ? 4f : 0f)
                              + (_rc.ElementRelevance(r) - 1f) * 1.5f + _rng.NextFloat();
                if (!_strategy.TakePacts && HasDrawback(r.Effects)) score -= 3f; // risk relics only for risk-taking plans
                score = PolicyScore(score, (int)r.Rarity);
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
            ArenaDef arena = rc.Arena;
            WaveDef wave = rc.CurrentWave;
            List<int> lanes = Battle.LanesForWave(wave, rc.Biome);
            var taken = new HashSet<int>();
            if (s.BlockedNode >= 0) taken.Add(s.BlockedNode);
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
