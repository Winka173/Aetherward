using System;
using System.Collections.Generic;
using System.Globalization;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using Aetherward.Sim.Run;

namespace Aetherward.Sim.Meta
{
    /// <summary>Platform storage abstraction. Unity implementation does temp-file + rename + backup.</summary>
    public interface ISaveStorage
    {
        string Read(string key);
        void Write(string key, string text);
        void Delete(string key);
    }

    /// <summary>In-memory storage for tests and the headless simulator.</summary>
    public sealed class MemoryStorage : ISaveStorage
    {
        public readonly Dictionary<string, string> Files = new Dictionary<string, string>();
        public string Read(string key) => Files.TryGetValue(key, out string v) ? v : null;
        public void Write(string key, string text) => Files[key] = text;
        public void Delete(string key) => Files.Remove(key);
    }

    public sealed class SettingsModel
    {
        public string Language = "en";
        public float MasterVolume = 0.8f;
        public float MusicVolume = 0.6f;
        public float SfxVolume = 0.8f;
        public float UiVolume = 0.7f;
        public bool DefaultFastSpeed;
        public bool ReducedVfx;
        public bool ScreenShake = true;
        public bool DamageNumbers = true;
        public bool HighContrast;
        public int TargetFps = 60;
        public bool ShowRanges;
    }

    /// <summary>
    /// Versioned JSON saves with checksum, backup fallback and migrations. Keys: "meta", "run",
    /// "settings". A corrupt file falls back to its backup, then to a clean default (never crashes).
    /// </summary>
    public sealed class SaveService
    {
        public const int CurrentVersion = 2;
        private readonly ISaveStorage _storage;
        public string LastError { get; private set; }

        public SaveService(ISaveStorage storage) { _storage = storage; }

        // ------------------------------------------------------------------ envelope

        private void WriteEnvelope(string key, JsonNode data)
        {
            string payload = data.ToJson();
            JsonNode env = JsonNode.NewObject()
                .Set("version", CurrentVersion)
                .Set("kind", key)
                .Set("checksum", Pcg32.Hash64(payload).ToString(CultureInfo.InvariantCulture))
                .Set("data", data);
            string text = env.ToJson(true);
            // Two-level backup rotation: key -> key.bak -> key.bak2 (a bad write never costs the last good save).
            string previous = _storage.Read(key);
            if (previous != null)
            {
                string older = _storage.Read(key + ".bak");
                if (older != null) _storage.Write(key + ".bak2", older);
                _storage.Write(key + ".bak", previous);
            }
            _storage.Write(key, text);
        }

        private JsonNode ReadEnvelope(string key, out int version)
        {
            version = 0;
            foreach (string candidate in new[] { key, key + ".bak", key + ".bak2" })
            {
                string text = _storage.Read(candidate);
                if (text == null) continue;
                try
                {
                    JsonNode env = JsonNode.Parse(text);
                    JsonNode data = env["data"];
                    string checksum = env.Str("checksum");
                    if (checksum != null && checksum != Pcg32.Hash64(data.ToJson()).ToString(CultureInfo.InvariantCulture))
                        throw new FormatException("checksum mismatch");
                    version = env.Int("version", 1);
                    if (version > CurrentVersion) throw new FormatException("save from newer version " + version);
                    return data;
                }
                catch (Exception e)
                {
                    LastError = candidate + ": " + e.Message;
                    // Keep the unreadable file for recovery/support instead of silently overwriting it later.
                    if (_storage.Read(candidate + ".corrupt") == null) _storage.Write(candidate + ".corrupt", text);
                }
            }
            return null;
        }

        public void Delete(string key)
        {
            _storage.Delete(key);
            _storage.Delete(key + ".bak");
            _storage.Delete(key + ".bak2");
        }

        // ------------------------------------------------------------------ settings

        public void SaveSettings(SettingsModel s)
        {
            WriteEnvelope("settings", JsonNode.NewObject()
                .Set("language", s.Language).Set("master", s.MasterVolume).Set("music", s.MusicVolume)
                .Set("sfx", s.SfxVolume).Set("ui", s.UiVolume).Set("fast", s.DefaultFastSpeed)
                .Set("reducedVfx", s.ReducedVfx).Set("shake", s.ScreenShake).Set("numbers", s.DamageNumbers)
                .Set("contrast", s.HighContrast).Set("fps", s.TargetFps).Set("ranges", s.ShowRanges));
        }

        public SettingsModel LoadSettings()
        {
            JsonNode d = ReadEnvelope("settings", out _);
            var s = new SettingsModel();
            if (d == null) return s;
            s.Language = d.Str("language", "en");
            s.MasterVolume = d.Float("master", s.MasterVolume);
            s.MusicVolume = d.Float("music", s.MusicVolume);
            s.SfxVolume = d.Float("sfx", s.SfxVolume);
            s.UiVolume = d.Float("ui", s.UiVolume);
            s.DefaultFastSpeed = d.Bool("fast");
            s.ReducedVfx = d.Bool("reducedVfx");
            s.ScreenShake = d.Bool("shake", true);
            s.DamageNumbers = d.Bool("numbers", true);
            s.HighContrast = d.Bool("contrast");
            s.TargetFps = d.Int("fps", 60);
            s.ShowRanges = d.Bool("ranges");
            return s;
        }

        // ------------------------------------------------------------------ meta

        public void SaveMeta(MetaProfile m)
        {
            JsonNode d = JsonNode.NewObject()
                .Set("heroes", StringArray(m.UnlockedHeroes))
                .Set("relics", StringArray(m.UnlockedRelics))
                .Set("biomes", StringArray(m.UnlockedBiomes))
                .Set("codex", StringArray(m.Codex))
                .Set("heroRuns", IntMap(m.HeroRuns))
                .Set("heroWins", IntMap(m.HeroWins))
                .Set("modeRecords", IntMap(m.ModeRecords))
                .Set("totalRuns", m.TotalRuns).Set("victories", m.Victories).Set("bestWave", m.BestWave)
                .Set("totalReactions", m.TotalReactions).Set("ascension", m.MaxAscensionUnlocked).Set("tutorial", m.TutorialDone);
            JsonNode hist = JsonNode.NewArray();
            foreach (RunHistoryEntry h in m.History)
            {
                JsonNode tl = JsonNode.NewArray();
                foreach (float v in h.CrystalTimeline) tl.Add(JsonNode.From(Math.Round(v, 1)));
                hist.Add(JsonNode.NewObject()
                    .Set("seed", h.Seed).Set("version", h.Version).Set("victory", h.Victory).Set("wave", h.Wave)
                    .Set("asc", h.Ascension).Set("seconds", Math.Round(h.Seconds, 1)).Set("reactions", h.Reactions)
                    .Set("strongest", h.StrongestReaction).Set("defeat", h.DefeatSource).Set("mvp", h.Mvp)
                    .Set("heroes", StringArray(h.Heroes)).Set("relics", StringArray(h.Relics)).Set("timeline", tl)
                    .Set("time", h.UnixTime));
            }
            d.Set("history", hist);
            WriteEnvelope("meta", d);
        }

        public MetaProfile LoadMeta(ContentDatabase db)
        {
            JsonNode d = ReadEnvelope("meta", out int version);
            MetaProfile m = MetaProfile.CreateDefault(db);
            if (d == null) return m;
            foreach (string h in d.StringList("heroes")) if (db.Heroes.ContainsKey(h)) m.UnlockedHeroes.Add(h);
            foreach (string r in d.StringList("relics")) if (db.Relics.ContainsKey(r)) m.UnlockedRelics.Add(r);
            foreach (string b in d.StringList("biomes")) if (db.Biomes.ContainsKey(b)) m.UnlockedBiomes.Add(b);
            foreach (string c in d.StringList("codex")) m.Codex.Add(c);
            ReadIntMap(d["heroRuns"], m.HeroRuns);
            ReadIntMap(d["heroWins"], m.HeroWins);
            ReadIntMap(d["modeRecords"], m.ModeRecords);
            m.TotalRuns = d.Int("totalRuns");
            m.Victories = d.Int("victories");
            m.BestWave = d.Int("bestWave");
            m.TotalReactions = d.Int("totalReactions");
            m.MaxAscensionUnlocked = d.Int("ascension");
            m.TutorialDone = d.Bool("tutorial");
            foreach (JsonNode h in d["history"].Items)
            {
                var e = new RunHistoryEntry
                {
                    Seed = h.Str("seed"), Version = h.Str("version"), Victory = h.Bool("victory"), Wave = h.Int("wave"),
                    Ascension = h.Int("asc"), Seconds = h.Float("seconds"), Reactions = h.Int("reactions"),
                    StrongestReaction = h.Str("strongest"), DefeatSource = h.Str("defeat"), Mvp = h.Str("mvp"),
                    UnixTime = h["time"].AsLong()
                };
                e.Heroes.AddRange(h.StringList("heroes"));
                e.Relics.AddRange(h.StringList("relics"));
                foreach (JsonNode v in h["timeline"].Items) e.CrystalTimeline.Add(v.AsFloat());
                m.History.Add(e);
            }
            // v1 profiles had no tutorial flag; anyone with a recorded run has seen it.
            if (version < 2 && m.TotalRuns > 0) m.TutorialDone = true;
            return m;
        }

        // ------------------------------------------------------------------ run (between waves)

        public void SaveRun(RunState s)
        {
            if (s.Phase == RunPhase.Battle || s.Finished) return; // only boundary states are resumable
            JsonNode heroes = JsonNode.NewArray();
            foreach (HeroRunState h in s.Heroes)
            {
                heroes.Add(JsonNode.NewObject()
                    .Set("uid", h.Uid).Set("id", h.DefId).Set("level", h.Level).Set("xp", h.Xp).Set("evo", h.EvolutionId)
                    .Set("hp", h.HpFraction).Set("downed", h.Downed).Set("node", h.Node).Set("joined", h.JoinedWave)
                    .Set("dmg", h.DamageDealt).Set("heal", h.HealingDone).Set("taken", h.DamageTaken).Set("kills", h.Kills)
                    .Set("reactions", h.Reactions).Set("casts", h.SkillCasts).Set("downs", h.TimesDowned).Set("trait", h.TraitId).Set("awaken", h.Awakened));
            }
            JsonNode offers = JsonNode.NewArray();
            foreach (Offer o in s.Offers)
            {
                offers.Add(JsonNode.NewObject().Set("kind", o.Kind.ToString()).Set("id", o.Id).Set("price", o.Price)
                    .Set("hero", o.HeroUid).Set("opt", o.OptionIndex).Set("sold", o.Sold).Set("tag", o.Tag).Set("trait", o.TraitId));
            }
            JsonNode cards = JsonNode.NewObject();
            foreach (string id in s.CardOrder) cards.Set(id, s.CardStacks(id));
            JsonNode waves = JsonNode.NewArray();
            foreach (WaveRecord w in s.WaveLog)
            {
                waves.Add(JsonNode.NewObject().Set("wave", w.Wave).Set("dur", w.Duration).Set("cdmg", w.CrystalDamage)
                    .Set("chp", w.CrystalHpAfter).Set("kills", w.Kills).Set("leaks", w.Leaks).Set("reactions", w.Reactions)
                    .Set("downs", w.HeroDowns).Set("gold", w.GoldEarned).Set("peak", w.PeakEnemies).Set("pps", w.PeakReactionsPerSecond)
                    .Set("cleared", w.Cleared));
            }
            JsonNode pending = JsonNode.NewArray();
            foreach (RewardKind r in s.PendingRewards) pending.Add(JsonNode.From(r.ToString()));
            JsonNode elements = JsonNode.NewArray();
            foreach (float v in s.ElementDamage) elements.Add(JsonNode.From(v));
            JsonNode kinds = JsonNode.NewArray();
            foreach (float v in s.DamageByKind) kinds.Add(JsonNode.From(v));

            JsonNode d = JsonNode.NewObject()
                .Set("seed", s.Seed.ToString(CultureInfo.InvariantCulture)).Set("gameVersion", s.GameVersion)
                .Set("ascension", s.Ascension).Set("wave", s.Wave).Set("phase", s.Phase.ToString())
                .Set("gold", s.Gold).Set("essence", s.Essence).Set("crystal", s.CrystalHp).Set("crystalBase", s.CrystalBaseMaxHp)
                .Set("crystalKnownMax", s.CrystalKnownMax).Set("nextUid", s.NextHeroUid)
                .Set("heroes", heroes).Set("relics", StringArray(s.Relics)).Set("cards", cards).Set("pacts", StringArray(s.Pacts))
                .Set("nextMods", StringArray(s.NextWaveModifiers)).Set("pending", pending).Set("current", s.CurrentReward.ToString())
                .Set("offers", offers).Set("event", s.CurrentEventId).Set("rerollsScreen", s.RerollsThisScreen)
                .Set("rerolls", s.TotalRerolls).Set("freeRerolls", s.FreeRerollsLeft).Set("seconds", s.ActiveSeconds)
                .Set("goldEarned", s.GoldEarnedTotal).Set("goldSpent", s.GoldSpentTotal).Set("waves", waves)
                .Set("reactionCounts", IntMap(s.ReactionCounts)).Set("reactionDamage", FloatMap(s.ReactionDamage))
                .Set("sourceCounts", IntMap(s.SourceActivations)).Set("sourceDamage", FloatMap(s.SourceDamage))
                .Set("dmgKinds", kinds).Set("shieldAbsorbed", s.ShieldAbsorbed).Set("procDepth", s.MaxProcDepth).Set("crystalBy", FloatMap(s.CrystalDamageByEnemy))
                .Set("elements", elements).Set("seen", StringArray(s.SeenEnemies)).Set("drafts", s.DraftsTaken)
                .Set("bosses", BossMap(s.BossChoices)).Set("blocked", s.BlockedNode).Set("biome", s.BiomeId)
                .Set("mode", s.Mode.ToString()).Set("daily", s.DailyKey).Set("modeMods", StringArray(s.ModeModifiers))
                .Set("heroPool", StringArray(s.HeroPool)).Set("relicPool", StringArray(s.RelicPool))
                .Set("menuSeconds", Math.Round(s.MenuSeconds, 1)).Set("tactic", s.Tactic.ToString())
                .Set("lock", s.LockedOffer == null ? JsonNode.NewObject() : JsonNode.NewObject().Set("kind", s.LockedOffer.Kind.ToString()).Set("id", s.LockedOffer.Id)
                    .Set("price", s.LockedOffer.Price).Set("trait", s.LockedOffer.TraitId));
            WriteEnvelope("run", d);
        }

        private static JsonNode BossMap(Dictionary<int, string> map)
        {
            JsonNode n = JsonNode.NewObject();
            var keys = new List<int>(map.Keys);
            keys.Sort();
            foreach (int k in keys) n.Set(k.ToString(CultureInfo.InvariantCulture), map[k]);
            return n;
        }

        public RunState LoadRun(ContentDatabase db)
        {
            JsonNode d = ReadEnvelope("run", out int version);
            if (d == null) return null;
            try
            {
                var s = new RunState
                {
                    Seed = ulong.Parse(d.Str("seed", "0"), CultureInfo.InvariantCulture),
                    GameVersion = d.Str("gameVersion", "0.0.0"),
                    Ascension = d.Int("ascension"),
                    Wave = d.Int("wave", 1),
                    Phase = (RunPhase)Enum.Parse(typeof(RunPhase), d.Str("phase", "Prepare")),
                    Gold = d.Int("gold"),
                    Essence = d.Int("essence"),
                    CrystalHp = d.Float("crystal"),
                    CrystalBaseMaxHp = d.Float("crystalBase", db.Economy.CrystalHp),
                    NextHeroUid = d.Int("nextUid", 1),
                    CurrentReward = (RewardKind)Enum.Parse(typeof(RewardKind), d.Str("current", "Draft")),
                    CurrentEventId = d.Str("event"),
                    RerollsThisScreen = d.Int("rerollsScreen"),
                    TotalRerolls = d.Int("rerolls"),
                    FreeRerollsLeft = d.Int("freeRerolls"),
                    ActiveSeconds = d.Float("seconds"),
                    GoldEarnedTotal = d.Float("goldEarned"),
                    GoldSpentTotal = d.Float("goldSpent"),
                    DraftsTaken = d.Int("drafts")
                };
                // v1 saves predate CrystalKnownMax: assume base max (no relic deltas applied yet).
                s.CrystalKnownMax = version >= 2 ? d.Float("crystalKnownMax", s.CrystalBaseMaxHp) : s.CrystalBaseMaxHp;
                foreach (JsonNode h in d["heroes"].Items)
                {
                    string id = h.Str("id");
                    if (!db.Heroes.ContainsKey(id)) continue; // content removed: drop gracefully
                    string evo = h.Str("evo");
                    if (evo != null && !db.Evolutions.ContainsKey(evo)) evo = null;
                    s.Heroes.Add(new HeroRunState
                    {
                        Uid = h.Int("uid"), DefId = id, Level = h.Int("level", 1), Xp = h.Int("xp"), EvolutionId = evo,
                        HpFraction = h.Float("hp", 1f), Downed = h.Bool("downed"), Node = h.Int("node", -1), JoinedWave = h.Int("joined", 1),
                        DamageDealt = h.Float("dmg"), HealingDone = h.Float("heal"), DamageTaken = h.Float("taken"), Kills = h.Int("kills"),
                        Reactions = h.Int("reactions"), SkillCasts = h.Int("casts"), TimesDowned = h.Int("downs"),
                        TraitId = db.Traits.ContainsKey(h.Str("trait") ?? "") ? h.Str("trait") : null, // retired traits drop gracefully
                        Awakened = ElementUtil.TryParse(h.Str("awaken") ?? "", out Element aw) && aw != Element.None ? h.Str("awaken") : null
                    });
                }
                foreach (string r in d.StringList("relics")) if (db.Relics.ContainsKey(r)) s.Relics.Add(r);
                foreach (string k in d["cards"].Keys)
                {
                    if (!db.Cards.ContainsKey(k)) continue;
                    s.Cards[k] = d["cards"].Int(k);
                    s.CardOrder.Add(k);
                }
                s.Pacts.AddRange(d.StringList("pacts"));
                s.NextWaveModifiers.AddRange(d.StringList("nextMods"));
                foreach (string r in d.StringList("pending")) s.PendingRewards.Add((RewardKind)Enum.Parse(typeof(RewardKind), r));
                foreach (JsonNode o in d["offers"].Items)
                {
                    s.Offers.Add(new Offer
                    {
                        Kind = (OfferKind)Enum.Parse(typeof(OfferKind), o.Str("kind")), Id = o.Str("id"), Price = o.Int("price"),
                        HeroUid = o.Int("hero"), OptionIndex = o.Int("opt"), Sold = o.Bool("sold"), Tag = o.Str("tag"),
                        TraitId = db.Traits.ContainsKey(o.Str("trait") ?? "") ? o.Str("trait") : null
                    });
                }
                foreach (JsonNode w in d["waves"].Items)
                {
                    s.WaveLog.Add(new WaveRecord
                    {
                        Wave = w.Int("wave"), Duration = w.Float("dur"), CrystalDamage = w.Float("cdmg"), CrystalHpAfter = w.Float("chp"),
                        Kills = w.Int("kills"), Leaks = w.Int("leaks"), Reactions = w.Int("reactions"), HeroDowns = w.Int("downs"),
                        GoldEarned = w.Int("gold"), PeakEnemies = w.Int("peak"), PeakReactionsPerSecond = w.Int("pps"), Cleared = w.Bool("cleared")
                    });
                }
                ReadIntMap(d["reactionCounts"], s.ReactionCounts);
                ReadFloatMap(d["reactionDamage"], s.ReactionDamage);
                ReadIntMap(d["sourceCounts"], s.SourceActivations);
                ReadFloatMap(d["sourceDamage"], s.SourceDamage);
                var els = d["elements"].Items;
                for (int i = 0; i < els.Count && i < s.ElementDamage.Length; i++) s.ElementDamage[i] = els[i].AsFloat();
                var kinds = d["dmgKinds"].Items; // absent in older saves: stays zero
                for (int i = 0; i < kinds.Count && i < s.DamageByKind.Length; i++) s.DamageByKind[i] = kinds[i].AsFloat();
                s.ShieldAbsorbed = d.Float("shieldAbsorbed");
                s.MaxProcDepth = d.Int("procDepth");
                ReadFloatMap(d["crystalBy"], s.CrystalDamageByEnemy);
                s.SeenEnemies.AddRange(d.StringList("seen"));
                s.BlockedNode = d.Int("blocked", -1);
                string biome = d.Str("biome");
                s.BiomeId = biome != null && db.Biomes.ContainsKey(biome) ? biome : null;
                s.Mode = Enum.TryParse(d.Str("mode") ?? "Classic", out GameMode mode) ? mode : GameMode.Classic;
                s.DailyKey = d.Str("daily");
                s.ModeModifiers.AddRange(d.StringList("modeMods"));
                foreach (string h in d.StringList("heroPool")) if (db.Heroes.ContainsKey(h)) s.HeroPool.Add(h);
                foreach (string r in d.StringList("relicPool")) if (db.Relics.ContainsKey(r)) s.RelicPool.Add(r);
                s.MenuSeconds = d.Float("menuSeconds");
                s.Tactic = Enum.TryParse(d.Str("tactic") ?? "Balanced", out Combat.TeamTactic tac) ? tac : Combat.TeamTactic.Balanced;
                JsonNode lk = d["lock"];
                if (lk.Kind == JsonKind.Object && lk.Has("id") && Enum.TryParse(lk.Str("kind") ?? "", out OfferKind lkind))
                    s.LockedOffer = new Offer { Kind = lkind, Id = lk.Str("id"), Price = lk.Int("price"), TraitId = lk.Str("trait"), Tag = "locked" };
                foreach (string k in d["bosses"].Keys)
                {
                    string boss = d["bosses"].Str(k);
                    if (int.TryParse(k, NumberStyles.Integer, CultureInfo.InvariantCulture, out int w) && boss != null && db.Enemies.ContainsKey(boss)) s.BossChoices[w] = boss;
                }
                if (s.Heroes.Count == 0) throw new FormatException("run without heroes");
                return s;
            }
            catch (Exception e)
            {
                LastError = "run: " + e.Message;
                return null;
            }
        }

        // ------------------------------------------------------------------ helpers

        private static JsonNode StringArray(IEnumerable<string> items)
        {
            var list = new List<string>(items);
            list.Sort(string.CompareOrdinal);
            JsonNode a = JsonNode.NewArray();
            foreach (string s in list) a.Add(JsonNode.From(s));
            return a;
        }

        private static JsonNode IntMap(Dictionary<string, int> map)
        {
            JsonNode o = JsonNode.NewObject();
            var keys = new List<string>(map.Keys);
            keys.Sort(string.CompareOrdinal);
            foreach (string k in keys) o.Set(k, map[k]);
            return o;
        }

        private static JsonNode FloatMap(Dictionary<string, float> map)
        {
            JsonNode o = JsonNode.NewObject();
            var keys = new List<string>(map.Keys);
            keys.Sort(string.CompareOrdinal);
            foreach (string k in keys) o.Set(k, Math.Round(map[k], 2));
            return o;
        }

        private static void ReadIntMap(JsonNode n, Dictionary<string, int> map)
        {
            foreach (string k in n.Keys) map[k] = n.Int(k);
        }

        private static void ReadFloatMap(JsonNode n, Dictionary<string, float> map)
        {
            foreach (string k in n.Keys) map[k] = n.Float(k);
        }
    }
}
