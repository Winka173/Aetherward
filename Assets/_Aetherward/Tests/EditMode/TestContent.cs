using System;
using System.IO;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;

namespace Aetherward.Tests
{
    /// <summary>
    /// Loads the real content JSON from Assets/_Aetherward/Resources/Content. Works both inside Unity
    /// (cwd = project root) and in the .NET harness (walks up from the test binary folder).
    /// </summary>
    public static class TestContent
    {
        private static ContentDatabase _cached;

        public static string ContentDirectory
        {
            get
            {
                string dir = Directory.GetCurrentDirectory();
                for (int i = 0; i < 10 && dir != null; i++)
                {
                    string candidate = Path.Combine(dir, "Assets", "_Aetherward", "Resources", "Content");
                    if (Directory.Exists(candidate)) return candidate;
                    dir = Path.GetDirectoryName(dir);
                }
                string baseDir = AppDomain.CurrentDomain.BaseDirectory;
                for (int i = 0; i < 10 && baseDir != null; i++)
                {
                    string candidate = Path.Combine(baseDir, "Assets", "_Aetherward", "Resources", "Content");
                    if (Directory.Exists(candidate)) return candidate;
                    baseDir = Path.GetDirectoryName(baseDir);
                }
                throw new DirectoryNotFoundException("Content directory not found");
            }
        }

        public static ContentDatabase Db
        {
            get
            {
                if (_cached == null) _cached = Load();
                return _cached;
            }
        }

        public static ContentDatabase Load()
        {
            string dir = ContentDirectory;
            return ContentDatabase.Load(name =>
            {
                string path = Path.Combine(dir, name + ".json");
                return File.Exists(path) ? File.ReadAllText(path) : null;
            });
        }

        public static BattleSetup Setup(int wave, ulong seed, params (string hero, int node)[] heroes)
        {
            ContentDatabase db = Db;
            var setup = new BattleSetup
            {
                Content = db,
                Wave = db.Waves[wave - 1],
                Seed = seed,
                CrystalHp = db.Economy.CrystalHp,
                CrystalMaxHp = db.Economy.CrystalHp
            };
            int i = 0;
            foreach (var (hero, node) in heroes)
                setup.Heroes.Add(new HeroLoadout { Def = db.Heroes[hero], NodeIndex = node, RosterIndex = i++ });
            return setup;
        }

        /// <summary>A battle with no scheduled spawns, for deterministic unit tests of mechanics.</summary>
        public static Battle EmptyBattle(params (string hero, int node)[] heroes)
        {
            BattleSetup s = Setup(1, 42, heroes);
            var wave = new WaveDef { Number = 1, TimeLimit = 999f };
            s.Wave = wave;
            return new Battle(s);
        }
    }
}
