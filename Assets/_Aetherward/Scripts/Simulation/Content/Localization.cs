using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace Aetherward.Sim.Content
{
    /// <summary>
    /// String-key localization (English source, Vietnamese translation). Combat code never builds
    /// sentences; it emits ids, and presentation resolves them here. Missing keys fall back to
    /// English, then to the key itself, and are recorded for the validator.
    /// </summary>
    public sealed class Localization
    {
        private readonly ContentDatabase _db;
        private Dictionary<string, string> _active;
        private Dictionary<string, string> _fallback;
        public readonly HashSet<string> Missing = new HashSet<string>();
        public string Language { get; private set; }
        public static readonly string[] Supported = { "en", "vi" };

        public Localization(ContentDatabase db, string language)
        {
            _db = db;
            _fallback = db.Strings.TryGetValue("en", out var en) ? en : new Dictionary<string, string>();
            SetLanguage(language);
        }

        public void SetLanguage(string language)
        {
            if (!_db.Strings.TryGetValue(language ?? "en", out _active))
            {
                _active = _fallback;
                language = "en";
            }
            Language = language;
        }

        public bool Has(string key) => key != null && (_active.ContainsKey(key) || _fallback.ContainsKey(key));

        public string Get(string key)
        {
            if (string.IsNullOrEmpty(key)) return "";
            if (_active.TryGetValue(key, out string s)) return s;
            if (_fallback.TryGetValue(key, out s)) return s;
            Missing.Add(key);
            return key;
        }

        public string Format(string key, params object[] args)
        {
            string t = Get(key);
            try
            {
                return string.Format(CultureInfo.InvariantCulture, t, args);
            }
            catch (FormatException)
            {
                return t;
            }
        }

        public string Element(Element e) => Get("element." + ElementUtil.Key(e));

        /// <summary>Reaction display name; generic auto interactions are named from both elements.</summary>
        public string ReactionName(string id)
        {
            if (string.IsNullOrEmpty(id)) return "";
            if (_db.Reactions.TryGetValue(id, out ReactionDef r))
                return r.AutoNamed ? Format(r.NameKey, Element(r.A), Element(r.B)) : Get(r.NameKey);
            return Get("reaction." + id + ".name");
        }

        public string StatusName(Element e)
        {
            ElementDef d = _db.ElementDefs[(int)e];
            return d != null ? Get("status." + d.StatusKey) : "";
        }
        public string Role(HeroRole r) => Get("role." + EnumParse.ToSnake(r.ToString()));
        public string Stat(StatId s) => Get("stat." + EnumParse.ToSnake(s.ToString()));
        public string Rarity(Rarity r) => Get("rarity." + EnumParse.ToSnake(r.ToString()));

        /// <summary>
        /// Fills {name} tokens from a parameter bag. {name%} prints value*100 as a percentage,
        /// {name} prints the number with up to one decimal. Unknown tokens are left as-is.
        /// </summary>
        public static string Fill(string template, Func<string, float?> lookup)
        {
            if (template == null || template.IndexOf('{') < 0) return template;
            var sb = new StringBuilder(template.Length + 16);
            int i = 0;
            while (i < template.Length)
            {
                char c = template[i];
                if (c != '{')
                {
                    sb.Append(c);
                    i++;
                    continue;
                }
                int end = template.IndexOf('}', i);
                if (end < 0)
                {
                    sb.Append(template, i, template.Length - i);
                    break;
                }
                string token = template.Substring(i + 1, end - i - 1);
                bool pct = token.EndsWith("%", StringComparison.Ordinal);
                string name = pct ? token.Substring(0, token.Length - 1) : token;
                float? v = lookup(name);
                if (v.HasValue) sb.Append(Number(pct ? v.Value * 100f : v.Value)).Append(pct ? "%" : "");
                else sb.Append('{').Append(token).Append('}');
                i = end + 1;
            }
            return sb.ToString();
        }

        public static string Number(float v)
        {
            if (Math.Abs(v - Math.Round(v)) < 0.05f) return ((int)Math.Round(v)).ToString(CultureInfo.InvariantCulture);
            return v.ToString("0.#", CultureInfo.InvariantCulture);
        }

        public string SkillText(SkillDef skill, string key)
        {
            string template = Get(key);
            return Fill(template, name =>
            {
                switch (name)
                {
                    case "mult": return skill.Multiplier;
                    case "cooldown": return skill.Cooldown;
                    case "gauge": return skill.Gauge;
                    default: return skill.Params.Has(name) ? skill.Params.Get(name) : (float?)null;
                }
            });
        }

        public string PassiveText(ParamBag p, string key)
        {
            return Fill(Get(key), name => p.Has(name) ? p.Get(name) : (float?)null);
        }
    }
}
