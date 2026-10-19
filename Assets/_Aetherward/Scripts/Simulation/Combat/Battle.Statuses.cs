using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    /// <summary>
    /// Shared status vocabulary for elements, reactions, skills and relics. Every status is bounded:
    /// stack caps, diminishing returns on control, and boss-specific alternatives (no permanent lock).
    /// </summary>
    public sealed partial class Battle
    {
        public const float DoomThresholdPerStack = 0.04f;
        public const int DoomMaxStacks = 5;
        public const int PoisonMaxStacks = 10;
        public const int UnstableThreshold = 3;
        public const int MaxContagionDepth = 2;

        /// <summary>Applies one named status. <paramref name="scale"/> multiplies amounts/durations from reaction status mods.</summary>
        public void ApplyStatus(EnemyUnit e, string status, ParamBag p, float scale, HeroUnit src, int gen)
        {
            if (e == null || !e.Alive || string.IsNullOrEmpty(status)) return;
            switch (status)
            {
                case "burn":
                    ApplyBurn(e, src, p.Get("duration", 3f) * scale);
                    break;
                case "armor_crack":
                    ApplyArmorCrack(e, p.Get("duration", 4f), (int)p.Get("stacks", 1f), (int)p.Get("max", 1f));
                    break;
                case "slow":
                    Slow(e, p.Get("amount", 0.3f) * scale, p.Get("duration", 2f));
                    break;
                case "stun":
                    Stun(e, p.Get("duration", 0.5f) * scale);
                    break;
                case "vulnerable":
                    e.VulnerableTimer = SimMath.Max(e.VulnerableTimer, p.Get("duration", 3f));
                    e.VulnerableAmount = SimMath.Max(e.VulnerableAmount, p.Get("amount", 0.15f) * scale);
                    break;
                case "brittle":
                    e.BrittleTimer = SimMath.Max(e.BrittleTimer, p.Get("duration", 3f));
                    e.BrittleAmount = SimMath.Max(e.BrittleAmount, p.Get("amount", 0.2f) * scale);
                    break;
                case "reaction_vuln":
                    e.ReactionVulnTimer = SimMath.Max(e.ReactionVulnTimer, p.Get("duration", 4f));
                    e.ReactionVulnAmount = SimMath.Max(e.ReactionVulnAmount, p.Get("amount", 0.2f) * scale);
                    break;
                case "illuminate":
                    Illuminate(e, p.Get("duration", 4f) * scale, p.Get("weaken", 0.15f), p.Get("purge", 0.5f));
                    break;
                case "doom":
                    AddDoom(e, (int)p.Get("stacks", 1f), src);
                    break;
                case "root":
                    Root(e, p.Get("duration", 0.8f) * scale);
                    break;
                case "poison":
                    AddPoison(e, (int)p.Get("stacks", 1f), p.Get("duration", 5f), src);
                    break;
                case "resonant":
                    e.ResonantTimer = SimMath.Max(e.ResonantTimer, p.Get("duration", 5f) * scale);
                    break;
                case "unstable":
                    AddUnstable(e, (int)p.Get("stacks", 1f), src, gen);
                    break;
                case "mark":
                    AddMark(e, (int)p.Get("stacks", 1f), src);
                    break;
                case "seal":
                    Seal(e, p.Get("duration", 2f) * scale);
                    break;
            }
        }

        /// <summary>Runs element-status ops (elements.json onApply/onRefresh) on one enemy.</summary>
        private void RunElementStatusOps(List<ActionOp> ops, EnemyUnit e, HeroUnit src, int gen)
        {
            for (int i = 0; i < ops.Count; i++)
            {
                ActionOp op = ops[i];
                if (op.Op == "status") ApplyStatus(e, op.Status, op.Params, 1f, src, gen);
            }
        }

        // ------------------------------------------------------------------ individual statuses

        public void Illuminate(EnemyUnit e, float duration, float weaken, float purge)
        {
            bool fresh = e.IlluminatedTimer <= 0f;
            if (e.Latched) Detach(e);
            e.IlluminatedTimer = SimMath.Max(e.IlluminatedTimer, duration);
            e.IlluminatedWeaken = SimMath.Max(e.IlluminatedWeaken, SimMath.Clamp(weaken, 0f, 0.5f));
            if (!fresh) return;
            // Purify: strips enemy shields and support buffs (Banner, Arcane Mimic copies).
            if (purge > 0f && e.Shield > 0f) e.Shield *= 1f - SimMath.Clamp01(purge);
            e.SpeedBuff = 0f;
            e.ArmorBuff = 0f;
            e.BuffAuraTimer = 0f;
        }

        public void AddDoom(EnemyUnit e, int stacks, HeroUnit src)
        {
            int max = DoomMaxStacks + (int)Mods.Rule("doom_max");
            e.DoomStacks = SimMath.Clamp(e.DoomStacks + stacks, 0, max);
            e.DoomTimer = 8f;
            if (src != null) e.DoomSource = src;
        }

        /// <summary>Execute threshold from Doom: non-bosses only, halved on elites.</summary>
        public float DoomThreshold(EnemyUnit e)
        {
            if (e.DoomStacks <= 0 || e.IsBoss) return 0f;
            float per = DoomThresholdPerStack + Mods.Rule("doom_threshold");
            float t = e.DoomStacks * per;
            if (e.Elite) t *= 0.5f;
            return SimMath.Min(0.4f, t);
        }

        public void Root(EnemyUnit e, float duration)
        {
            if (e.IsBoss)
            {
                Slow(e, 0.3f, duration * 1.5f); // bosses are never rooted in place
                return;
            }
            if (e.RootImmune > 0f || e.Def.Params.Flag("flying")) return;
            float d = duration * (1f - e.Tenacity);
            if (d <= 0.05f) return;
            e.RootTimer = SimMath.Max(e.RootTimer, d);
        }

        public void AddPoison(EnemyUnit e, int stacks, float duration, HeroUnit src)
        {
            if (stacks <= 0) return;
            int max = PoisonMaxStacks + (int)Mods.Rule("poison_max");
            e.PoisonStacks = SimMath.Clamp(e.PoisonStacks + stacks, 0, max);
            e.PoisonTimer = SimMath.Max(e.PoisonTimer, duration);
            float atk = src != null ? src.Stat(StatId.Attack) : 14f * WaveLevelScale;
            float sp = src != null ? src.Stat(StatId.StatusPower) : 0f;
            float dps = atk * 0.05f * (1f + sp) * (1f + Mods.Rule("poison_power"));
            if (dps >= e.PoisonDpsPerStack || e.PoisonSource == null)
            {
                e.PoisonDpsPerStack = dps;
                e.PoisonSource = src;
            }
        }

        public void AddUnstable(EnemyUnit e, int stacks, HeroUnit src, int gen)
        {
            if (e.UnstableCooldown > 0f) return;
            e.UnstableStacks += stacks;
            if (src != null) e.UnstableSource = src;
            if (e.UnstableStacks < UnstableThreshold) return;
            e.UnstableStacks = 0;
            e.UnstableCooldown = 2f;
            Collapse(e.Pos, 1.6f * (1f + Mods.Rule("collapse_radius")), e.UnstableSource, 0.55f * (1f + Mods.Rule("collapse_power")), gen, "unstable_collapse");
        }

        /// <summary>Bounded void collapse: short pull toward the point (never bosses) plus Void damage.</summary>
        public void Collapse(Vec2 pos, float radius, HeroUnit src, float mult, int gen, string tag)
        {
            List<EnemyUnit> c = RentList();
            QueryEnemies(pos, radius, c);
            Emit(SimEventType.Strike, pos, Element.Void, 0f, src?.Uid ?? 0, 0, tag, false, radius, gen);
            float atk = src != null ? src.Stat(StatId.Attack) : 18f * WaveLevelScale;
            for (int i = 0; i < c.Count; i++)
            {
                EnemyUnit t = c[i];
                Pull(t, pos, 2.4f, 0.3f);
                DealDamage(t, new DamageRequest
                {
                    Source = src,
                    Attack = atk,
                    Multiplier = mult,
                    Element = Element.Void,
                    Kind = DamageKind.Trigger,
                    Generation = MaxProcGeneration,
                    SourceTag = tag
                });
            }
            ReturnList(c);
        }

        public void AddMark(EnemyUnit e, int stacks, HeroUnit src)
        {
            e.MarkStacks = SimMath.Clamp(e.MarkStacks + stacks, 0, 5 + (int)Mods.Rule("mark_max"));
            e.MarkTimer = 6f;
            if (src != null) e.MarkOwner = src;
        }

        /// <summary>Suppresses summons/specials. Bosses get half duration and never a full lock.</summary>
        public void Seal(EnemyUnit e, float duration)
        {
            float d = e.IsBoss ? duration * 0.5f : duration;
            e.SealTimer = SimMath.Max(e.SealTimer, d);
            e.SpecialTimer = SimMath.Max(e.SpecialTimer, 0f) + d;
        }

        // ------------------------------------------------------------------ ticking

        private void TickExpansionStatuses(EnemyUnit e, float dt)
        {
            if (e.IlluminatedTimer > 0f)
            {
                e.IlluminatedTimer -= dt;
                if (e.IlluminatedTimer <= 0f) e.IlluminatedWeaken = 0f;
            }
            if (e.DoomTimer > 0f)
            {
                e.DoomTimer -= dt;
                if (e.DoomTimer <= 0f) e.DoomStacks = 0;
            }
            if (e.RootTimer > 0f)
            {
                e.RootTimer -= dt;
                if (e.RootTimer <= 0f) e.RootImmune = 1.5f; // diminishing return: no permanent root
            }
            else if (e.RootImmune > 0f) e.RootImmune -= dt;
            if (e.ResonantTimer > 0f) e.ResonantTimer -= dt;
            if (e.UnstableCooldown > 0f) e.UnstableCooldown -= dt;
            if (e.BrittleTimer > 0f)
            {
                e.BrittleTimer -= dt;
                if (e.BrittleTimer <= 0f) e.BrittleAmount = 0f;
            }
            if (e.ReactionVulnTimer > 0f)
            {
                e.ReactionVulnTimer -= dt;
                if (e.ReactionVulnTimer <= 0f) e.ReactionVulnAmount = 0f;
            }
            if (e.MarkTimer > 0f)
            {
                e.MarkTimer -= dt;
                if (e.MarkTimer <= 0f) e.MarkStacks = 0;
            }
            if (e.FieldTimer > 0f)
            {
                e.FieldTimer -= dt;
                if (e.FieldTimer <= 0f) e.FieldVuln = e.FieldWeaken = e.FieldReactionAmp = 0f;
            }
            if (e.SealTimer > 0f) e.SealTimer -= dt;

            if (e.PoisonTimer > 0f)
            {
                e.PoisonTimer -= dt;
                e.PoisonTick -= dt;
                if (e.PoisonTick <= 0f && e.PoisonStacks > 0)
                {
                    e.PoisonTick = 0.5f;
                    DealDamage(e, new DamageRequest
                    {
                        Source = e.PoisonSource,
                        Attack = e.PoisonDpsPerStack * e.PoisonStacks * 0.5f,
                        Multiplier = 1f,
                        Element = Element.Poison,
                        Kind = DamageKind.Dot,
                        Generation = 1,
                        IgnoreDefense = true
                    });
                }
                if (e.PoisonTimer <= 0f)
                {
                    e.PoisonStacks = 0;
                    e.PoisonDpsPerStack = 0f;
                }
            }
        }

        /// <summary>Doom execution check after a hit (called while the enemy is still alive).</summary>
        private bool TryDoomExecute(EnemyUnit e, HeroUnit hitter)
        {
            float t = DoomThreshold(e);
            if (t <= 0f || e.HpFraction > t) return false;
            HeroUnit credit = e.DoomSource ?? hitter;
            Emit(SimEventType.Strike, e.Pos, Element.Shadow, e.Hp, credit?.Uid ?? 0, e.Uid, "doom_execute", false, 0.6f);
            Stats.AddSource("doom_execute", e.Hp);
            if (credit != null) credit.DamageDealt += e.Hp;
            KillEnemy(e, credit);
            OnDoomExecuted(credit, e);
            FireTrigger("doom_execute", credit, e, e.Pos, null);
            return true;
        }

        /// <summary>Poison contagion: half the stacks jump to the nearest enemy, at most two hops deep.</summary>
        private void SpreadContagion(EnemyUnit dead)
        {
            if (dead.PoisonStacks < 2 || dead.ContagionDepth >= MaxContagionDepth) return;
            int targets = 1 + (int)Mods.Rule("contagion_targets");
            int stacks = dead.PoisonStacks / 2 + (int)Mods.Rule("contagion_stacks");
            List<EnemyUnit> c = RentList();
            QueryEnemies(dead.Pos, 2.2f, c);
            // Deterministic: nearest first, uid tie-break.
            c.Sort((a, b) =>
            {
                int d = Vec2.SqrDistance(a.Pos, dead.Pos).CompareTo(Vec2.SqrDistance(b.Pos, dead.Pos));
                return d != 0 ? d : a.Uid.CompareTo(b.Uid);
            });
            for (int i = 0; i < c.Count && targets > 0; i++)
            {
                EnemyUnit t = c[i];
                if (t == dead || !t.Alive) continue;
                AddPoison(t, stacks, 5f, dead.PoisonSource);
                t.ContagionDepth = System.Math.Max(t.ContagionDepth, dead.ContagionDepth + 1);
                Emit(SimEventType.Strike, t.Pos, Element.Poison, 0f, dead.PoisonSource?.Uid ?? 0, t.Uid, "contagion", false, 0.4f);
                targets--;
            }
            ReturnList(c);
        }

        private static void ResetExpansionStatuses(EnemyUnit e)
        {
            e.IlluminatedTimer = e.IlluminatedWeaken = 0f;
            e.DoomStacks = 0;
            e.DoomTimer = 0f;
            e.DoomSource = null;
            e.RootTimer = e.RootImmune = 0f;
            e.PoisonStacks = 0;
            e.PoisonTimer = e.PoisonTick = e.PoisonDpsPerStack = 0f;
            e.PoisonSource = null;
            e.ContagionDepth = 0;
            e.ResonantTimer = 0f;
            e.UnstableStacks = 0;
            e.UnstableCooldown = 0f;
            e.UnstableSource = null;
            e.BrittleTimer = e.BrittleAmount = 0f;
            e.ReactionVulnTimer = e.ReactionVulnAmount = 0f;
            e.MarkStacks = 0;
            e.MarkTimer = 0f;
            e.MarkOwner = null;
            e.FieldTimer = e.FieldVuln = e.FieldWeaken = e.FieldReactionAmp = 0f;
            e.SealTimer = 0f;
            e.SpecialCooldownMult = 1f;
            e.Latched = false;
            e.Timer2 = 0f;
            e.Enraged = false;
            e.Burrowed = false;
            e.SurfaceTimer = e.SprintTimer = e.ChannelTimer = e.Stoke = 0f;
            e.LinkedTo = null;
        }
    }
}
