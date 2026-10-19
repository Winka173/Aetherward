using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    /// <summary>
    /// Data-driven boss modules ("boss": "generic"): telegraphed hero marks, add summons, crystal
    /// volleys, guard adds, a phase shift and periodic exposed windows. Each module is enabled by its
    /// params, so new bosses are authored in enemies.json. Rules: never invulnerable, every heavy hit
    /// telegraphed, adds capped, an exposed window always follows a volley/phase.
    /// Also Phase 4 enemy mechanics: reflect, chaos element cycling, regeneration, mimic shields.
    /// </summary>
    public sealed partial class Battle
    {
        private const int TMark = 0, TSummon = 1, TVolley = 2, TExpose = 3;

        private void UpdateGenericBoss(EnemyUnit e, float dt)
        {
            ParamBag p = e.Def.Params;
            float[] t = e.BossTimers;
            for (int i = 0; i < t.Length; i++) t[i] -= dt;

            if (e.Phase == 0 && p.Has("phaseAt") && e.HpFraction <= p.Get("phaseAt"))
            {
                e.Phase = 1;
                e.Speed *= 1f + p.Get("phaseSpeed");
                e.Attack *= 1f + p.Get("phaseAttack");
                Emit(SimEventType.BossPhase, e.Pos, e.Def.Params.GetString("phaseElement") != null ? ContentDatabase.ParseElement(p.GetString("phaseElement")) : Element.None,
                     1f, e.Uid, 0, e.Def.Id + "_phase", false, 2f);
                SummonAdds(e, p.GetString("phaseSummon"), (int)p.Get("phaseSummonCount"));
                Expose(e);
            }
            if (p.Has("guardAt") && e.BossFlags == 0 && e.HpFraction <= p.Get("guardAt"))
            {
                e.BossFlags = 1;
                SummonAdds(e, p.GetString("guardAdd"), (int)p.Get("guardCount", 2f));
                Emit(SimEventType.BossPhase, e.Pos, Element.None, 1f, e.Uid, 0, e.Def.Id + "_guard", false, 2f);
            }
            if (e.SealTimer > 0f || e.Stunned) return;

            if (p.Has("markInterval") && t[TMark] <= 0f)
            {
                t[TMark] = p.Get("markInterval");
                Element el = ContentDatabase.ParseElement(p.GetString("markElement", "none"));
                int placed = 0;
                for (int i = 0; i < Heroes.Count && placed < (int)p.Get("markCount", 2f); i++)
                {
                    HeroUnit h = Heroes[(i + TickCount) % Heroes.Count];
                    if (!h.Alive) continue;
                    AddStrike(new DelayedStrike
                    {
                        Kind = StrikeKind.BossSlam, Pos = h.Pos, Delay = p.Get("markDelay", 1.6f), Radius = p.Get("markRadius", 1.1f),
                        EnemySource = e, Power = e.Attack * p.Get("markMult", 0.8f), Element = el, HeroStun = p.Get("markStun")
                    });
                    placed++;
                }
            }
            if (p.Has("summonInterval") && t[TSummon] <= 0f)
            {
                t[TSummon] = p.Get("summonInterval");
                SummonAdds(e, p.GetString("summon"), (int)p.Get("summonCount", 2f));
            }
            if (p.Has("volleyInterval") && t[TVolley] <= 0f)
            {
                t[TVolley] = p.Get("volleyInterval");
                float delay = p.Get("volleyDelay", 1.8f);
                for (int k = 0; k < (int)p.Get("volleyCount", 3f); k++)
                {
                    Vec2 pos = Crystal.Pos + Vec2.FromAngle(k * 2.094f + Rng.Range(0f, 0.6f)) * 2.3f;
                    AddStrike(new DelayedStrike
                    {
                        Kind = StrikeKind.BossSlam, Pos = pos, Delay = delay + k * 0.25f, Radius = p.Get("volleyRadius", 1.2f),
                        EnemySource = e, Power = e.Attack * p.Get("volleyMult", 1.2f), Element = Element.None
                    });
                }
                t[TExpose] = SimMath.Min(t[TExpose], delay + 1f); // the counter window follows the volley
            }
            if ((p.Has("exposeEvery") || p.Has("volleyInterval")) && t[TExpose] <= 0f)
            {
                t[TExpose] = p.Get("exposeEvery", 999f); // volley-only bosses re-arm on the next volley
                Expose(e);
            }
        }

        private void Expose(EnemyUnit e)
        {
            ParamBag p = e.Def.Params;
            if (!p.Has("exposeAmount")) return;
            e.VulnerableTimer = SimMath.Max(e.VulnerableTimer, p.Get("exposeDuration", 3.5f));
            e.VulnerableAmount = SimMath.Max(e.VulnerableAmount, p.Get("exposeAmount"));
            Emit(SimEventType.BossPhase, e.Pos, Element.None, 2f, e.Uid, 0, "boss_exposed", false, 2f);
        }

        /// <summary>Spawns adds around a boss, respecting "summonCap" (alive adds of that id).</summary>
        private void SummonAdds(EnemyUnit e, string id, int count)
        {
            if (string.IsNullOrEmpty(id) || count <= 0 || !Content.Enemies.TryGetValue(id, out EnemyDef def)) return;
            int alive = 0;
            for (int i = 0; i < Enemies.Count; i++) if (Enemies[i].Alive && Enemies[i].Def == def) alive++;
            int cap = (int)e.Def.Params.Get("summonCap", 8f);
            for (int k = 0; k < count && alive < cap; k++, alive++)
            {
                Vec2 off = Vec2.FromAngle(k * 6.283f / count + 0.4f) * 1.4f;
                SpawnEnemy(def, e.Lane, false, null, e.Pos + off);
            }
            Emit(SimEventType.Strike, e.Pos, Element.Void, 0f, e.Uid, 0, "summon", false, 1.6f);
        }

        /// <summary>Guard adds (e.g. Mirror Knights) shield their boss while any of them stands.</summary>
        private bool GuardAlive(EnemyUnit boss)
        {
            string id = boss.Def.Params.GetString("guardAdd");
            if (id == null) return false;
            for (int i = 0; i < Enemies.Count; i++) if (Enemies[i].Alive && Enemies[i].Def.Id == id) return true;
            return false;
        }

        // ------------------------------------------------------------------ Phase 4 enemy mechanics

        /// <summary>Extra damage-taken multiplier: chaos element cycling and boss guard adds.</summary>
        private float MechanicDamageTakenP4(EnemyUnit target, DamageRequest req)
        {
            ParamBag p = target.Def.Params;
            float m = 1f;
            if (p.Has("chaosCycle") && req.Element != Element.None)
                m *= req.Element == target.ChaosElement ? 1f - p.Get("chaosResist", 0.6f) : 1f + p.Get("chaosWeak", 0.15f);
            if (p.Get("guardReduction") > 0f && GuardAlive(target)) m *= 1f - p.Get("guardReduction");
            return m;
        }

        private void UpdateEnemyMechanicsP4(EnemyUnit e, float dt)
        {
            ParamBag p = e.Def.Params;
            if (p.Has("chaosCycle"))
            {
                e.ChaosTimer -= dt;
                if (e.ChaosTimer <= 0f)
                {
                    e.ChaosTimer = p.Get("chaosCycle");
                    Element[] els = ElementUtil.All;
                    e.ChaosElement = els[(System.Array.IndexOf(els, e.ChaosElement) + 1 + Rng.Range(0, els.Length - 1)) % els.Length];
                    Emit(SimEventType.StatusApplied, e.Pos, e.ChaosElement, 0f, e.Uid, e.Uid, "chaos_shift");
                }
            }
            // Regeneration stops while the enemy Burns or is Poisoned (the intended counter).
            float regen = p.Get("regenPct");
            if (regen > 0f && e.BurnTimer <= 0f && e.PoisonStacks == 0 && e.Hp < e.MaxHp)
                e.Hp = SimMath.Min(e.MaxHp, e.Hp + e.MaxHp * regen * dt);
        }

        /// <summary>Mirror enemies reflect a share of hero skill damage back at the caster (never lethal).</summary>
        private void ReflectSkill(EnemyUnit target, DamageRequest req, float dealt)
        {
            float reflect = target.Def.Params.Get("reflect");
            if (reflect <= 0f || req.Kind != DamageKind.Skill || req.Source == null || !req.Source.Alive || req.Generation > 0) return;
            HeroUnit h = req.Source;
            float amount = SimMath.Min(dealt * reflect, h.Hp - 1f);
            if (amount <= 0f) return;
            DamageHero(h, amount, target);
        }

        /// <summary>Arcane Mimics near a casting hero copy the magic as a shield.</summary>
        private void MimicOnHeroCast(HeroUnit caster)
        {
            for (int i = 0; i < Enemies.Count; i++)
            {
                EnemyUnit e = Enemies[i];
                float pct = e.Def.Params.Get("mimicShield");
                if (pct <= 0f || !e.Alive || Vec2.Distance(e.Pos, caster.Pos) > e.Def.Params.Get("mimicRange", 4.5f)) continue;
                e.Shield = SimMath.Min(e.MaxHp * pct * 3f, e.Shield + e.MaxHp * pct);
                Emit(SimEventType.StatusApplied, e.Pos, Element.Arcane, 0f, caster.Uid, e.Uid, "mimic");
            }
        }
    }
}
