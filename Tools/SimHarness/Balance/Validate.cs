using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using Aetherward.Sim.Content;
using Aetherward.Sim.Meta;

namespace Aetherward.Balance
{
    /// <summary>
    /// Phase 9 content validation for CI: blocking errors (ContentValidator: ids, references, bounds,
    /// localization, matrix) plus non-blocking warnings (unreachable content, outlier multipliers,
    /// element coverage gaps) and content statistics. Never mutates data. Exit code 1 on errors.
    /// Writes Reports/ContentValidation/{report.md, report.json}.
    /// </summary>
    public static class Validate
    {
        public static int Run(ContentDatabase db, string root)
        {
            List<string> errors = ContentValidator.Validate(db);
            var warnings = new List<string>();

            // Reachability: every hero/relic must be a starter, unlockable by a meta rule, or a fusion result.
            var unlockable = new HashSet<string>(MetaProfile.Rules.Select(r => r.Id));
            foreach (HeroDef h in db.HeroList)
                if (!h.StarterUnlocked && !unlockable.Contains("hero:" + h.Id)) warnings.Add("unreachable hero: " + h.Id + " (not a starter and no unlock rule)");
            var fusionResults = new HashSet<string>(db.Fusions.Select(f => f.Result));
            foreach (RelicDef r in db.RelicList)
            {
                if (r.Fusion && !fusionResults.Contains(r.Id)) warnings.Add("unreachable fusion relic: " + r.Id + " (no recipe)");
                if (!r.Fusion && !r.StarterUnlocked && !unlockable.Contains("relic:" + r.Id)) warnings.Add("unreachable relic: " + r.Id + " (no unlock rule)");
            }
            foreach (BiomeDef b in db.BiomeList)
                if (!b.Default && !unlockable.Contains("biome:" + b.Id)) warnings.Add("unreachable biome: " + b.Id);

            // Outlier multipliers (allowed but suspicious) and reaction coverage.
            void Scan(string owner, IEnumerable<EffectOp> ops)
            {
                foreach (EffectOp op in ops)
                {
                    if (op.Op == "stat" && op.Percent && op.Value > 0.5f) warnings.Add(owner + ": large stat bonus " + op.Stat + " +" + (op.Value * 100f).ToString("F0") + "%");
                    if (op.Op == "reaction" && op.Params.Get("damagePct") > 0.75f) warnings.Add(owner + ": large reaction damage bonus on " + op.Reaction);
                }
            }
            foreach (RelicDef r in db.RelicList) Scan("relic " + r.Id, r.Effects);
            foreach (CardDef c in db.CardList) Scan("card " + c.Id, c.Effects);
            foreach (BondDef b in db.Bonds) Scan("bond " + b.Id, b.Effects);

            var heroesPerElement = ElementUtil.All.ToDictionary(e => e, e => db.HeroList.Count(h => h.Element == e));
            var relicsPerElement = ElementUtil.All.ToDictionary(e => e, e => db.RelicList.Count(r => r.Tags.Contains(ElementUtil.Key(e))));
            foreach (var kv in heroesPerElement) if (kv.Value < 2) warnings.Add("element gap: only " + kv.Value + " hero(es) for " + ElementUtil.Key(kv.Key));
            foreach (var kv in relicsPerElement) if (kv.Value < 2) warnings.Add("element gap: only " + kv.Value + " relic(s) tagged " + ElementUtil.Key(kv.Key));
            foreach (ReactionDef r in db.Reactions.Values)
                if (r.Category == ReactionCategory.Signature && (heroesPerElement[r.A] == 0 || heroesPerElement[r.B] == 0))
                    warnings.Add("dead reaction: " + r.Id + " (no hero of one element)");

            string dir = Path.Combine(root, "Reports", "ContentValidation");
            Directory.CreateDirectory(dir);
            var md = new StringBuilder("# Content validation report\n\n");
            md.AppendLine($"- Errors (blocking): **{errors.Count}**");
            md.AppendLine($"- Warnings (review): **{warnings.Count}**");
            md.AppendLine();
            md.AppendLine("## Counts");
            md.AppendLine($"heroes {db.HeroList.Count} · evolutions {db.Evolutions.Count} · traits {db.TraitList.Count} · bonds {db.Bonds.Count} · enemies {db.Enemies.Count} (bosses {db.Enemies.Values.Count(e => e.Boss)}) · " +
                          $"reactions {db.Reactions.Count} (signature {db.Reactions.Values.Count(r => r.Category == ReactionCategory.Signature)}) · fields {db.Fields.Count} · relics {db.RelicList.Count} (fusions {db.Fusions.Count}) · " +
                          $"cards {db.CardList.Count} · biomes {db.BiomeList.Count} · waves {db.Waves.Count} · ascension {db.Difficulty.MaxLevel}");
            md.AppendLine();
            md.AppendLine("## Element coverage");
            md.AppendLine("| Element | Heroes | Relics tagged |");
            md.AppendLine("|---|---|---|");
            foreach (var e in ElementUtil.All) md.AppendLine($"| {ElementUtil.Key(e)} | {heroesPerElement[e]} | {relicsPerElement[e]} |");
            md.AppendLine();
            md.AppendLine("## Errors");
            if (errors.Count == 0) md.AppendLine("- none");
            foreach (string e in errors) md.AppendLine("- " + e);
            md.AppendLine();
            md.AppendLine("## Warnings");
            if (warnings.Count == 0) md.AppendLine("- none");
            foreach (string w in warnings) md.AppendLine("- " + w);
            File.WriteAllText(Path.Combine(dir, "report.md"), md.ToString());
            File.WriteAllText(Path.Combine(dir, "report.json"), "{\n  \"errors\": [" + string.Join(", ", errors.Select(Json)) + "],\n  \"warnings\": [" +
                                                                string.Join(", ", warnings.Select(Json)) + "]\n}\n");
            Console.WriteLine("validate: " + errors.Count + " errors, " + warnings.Count + " warnings -> " + dir);
            return errors.Count > 0 ? 1 : 0;
        }

        private static string Json(string s) => "\"" + s.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\"";
    }
}
