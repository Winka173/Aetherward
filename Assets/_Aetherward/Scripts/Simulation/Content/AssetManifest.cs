using System.Collections.Generic;

namespace Aetherward.Sim.Content
{
    /// <summary>
    /// Every art/audio path the game loads by naming convention, derived from content. Used by the
    /// editor validator (with import checks) and by headless tests (file existence), so new content
    /// cannot ship without its sprites and sounds. Paths are relative to Resources/Art and Resources/Audio.
    /// </summary>
    public static class AssetManifest
    {
        public static readonly string[] HeroPoses = { "idle", "cast", "downed", "evoA", "evoB", "evoA_cast", "evoB_cast" };

        public static IEnumerable<string> RequiredArt(ContentDatabase db)
        {
            foreach (HeroDef h in db.HeroList)
            {
                foreach (string pose in HeroPoses) yield return "Heroes/" + h.Id + "_" + pose;
                yield return "Portraits/" + h.Id;
            }
            foreach (EnemyDef e in db.Enemies.Values)
            {
                yield return "Enemies/" + e.Id + "_a";
                yield return "Enemies/" + e.Id + "_b";
            }
            foreach (ReactionDef r in db.Reactions.Values)
                yield return r.AutoNamed ? "Icons/reaction_generic" : "Icons/reaction_" + r.Id;
            foreach (RelicDef r in db.RelicList) yield return "Relics/" + r.Id;
            foreach (CardDef c in db.CardList) yield return "Cards/" + c.Id;
            foreach (Element el in ElementUtil.All)
            {
                string k = ElementUtil.Key(el);
                yield return "Icons/element_" + k;
                yield return "Vfx/projectile_" + k;
                yield return "Vfx/impact_" + k;
                yield return "Icons/status_" + db.ElementDef(el).StatusKey;
            }
            foreach (FieldDef f in db.Fields.Values) yield return "Vfx/field_" + f.Id;
            foreach (string s in new[] { "World/arena_background", "World/crystal_intact", "World/crystal_cracked", "World/crystal_critical",
                         "World/node_empty", "World/node_occupied", "World/node_highlight", "World/lane_arrow", "World/shadow",
                         "UI/panel_dark", "UI/button_primary_normal", "UI/bar_bg", "UI/bar_fill", "UI/title_emblem" })
                yield return s;
        }

        public static IEnumerable<string> RequiredAudio(ContentDatabase db)
        {
            foreach (string clip in new[] { "Music/menu_loop", "Music/battle_loop", "Music/boss_loop", "Sfx/ui_click", "Sfx/wave_start", "Sfx/react_generic" })
                yield return clip;
            foreach (Element el in ElementUtil.All)
            {
                yield return "Sfx/hit_" + ElementUtil.Key(el);
                yield return "Sfx/cast_" + ElementUtil.Key(el);
            }
            foreach (ReactionDef r in db.Reactions.Values)
                if (!string.IsNullOrEmpty(r.Sound)) yield return "Sfx/" + r.Sound;
        }
    }
}
