using System.Collections.Generic;
using Aetherward.Sim.Content;
using NUnit.Framework;

namespace Aetherward.Tests
{
    public class ContentValidationTests
    {
        [Test]
        public void ContentPassesValidation()
        {
            List<string> errors = ContentValidator.Validate(TestContent.Db);
            Assert.IsEmpty(errors, string.Join("\n", errors));
        }

        [Test]
        public void TooltipTextComesFromRealParameters()
        {
            var l = new Localization(TestContent.Db, "en");
            HeroDef ignis = TestContent.Db.Heroes["ignis"];
            string text = l.SkillText(ignis.Skill, ignis.Skill.DescKey);
            StringAssert.Contains("210%", text, "fireball multiplier 2.1 must appear as 210%");
            StringAssert.Contains("1.4 m", text);
            var fx = new EffectDescriber(TestContent.Db, l);
            string line = fx.Describe(TestContent.Db.Relics["war_drum"].Effects)[0];
            Assert.AreEqual("+10% Attack", line);
        }

        [Test]
        public void VietnameseTableIsCompleteAndDiffers()
        {
            var en = TestContent.Db.Strings["en"];
            var vi = TestContent.Db.Strings["vi"];
            Assert.AreEqual(en.Count, vi.Count);
            Assert.AreNotEqual(en["menu.new_run"], vi["menu.new_run"]);
        }
    }
}
