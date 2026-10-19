using System;
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace Aetherward.EditorTools
{
    /// <summary>
    /// Build entry points (menu + batch mode). Batch example (Windows, Unity 6000.4.8f1):
    ///   Unity.exe -batchmode -quit -projectPath . -executeMethod Aetherward.EditorTools.AetherwardBuild.WindowsRelease -logFile Builds/windows.log
    /// Methods: WindowsDevelopment, WindowsRelease, AndroidDevelopmentApk, AndroidReleaseAab, IosXcodeProject.
    /// Validation runs first; a failing validation aborts the build with exit code 2.
    /// Android release signing is NOT configured (no keystore in the repo); AAB builds use the debug key
    /// unless the owner sets PlayerSettings.Android.keystore* locally. iOS produces an Xcode project
    /// that must be built and signed on macOS.
    /// </summary>
    public static class AetherwardBuild
    {
        private static string[] Scenes()
        {
            var list = new System.Collections.Generic.List<string>();
            foreach (EditorBuildSettingsScene s in EditorBuildSettings.scenes) if (s.enabled) list.Add(s.path);
            if (list.Count == 0) throw new InvalidOperationException("No scenes in build settings. Run Aetherward > Rebuild Scenes.");
            return list.ToArray();
        }

        private static bool Build(BuildTarget target, BuildTargetGroup group, string path, BuildOptions options, bool appBundle = false)
        {
            var errors = AetherwardMenu.Validate();
            if (errors.Count > 0)
            {
                Debug.LogError("Build aborted, validation failed:\n" + string.Join("\n", errors));
                if (Application.isBatchMode) EditorApplication.Exit(2);
                return false;
            }
            if (EditorUserBuildSettings.activeBuildTarget != target) EditorUserBuildSettings.SwitchActiveBuildTarget(group, target);
            if (target == BuildTarget.Android) EditorUserBuildSettings.buildAppBundle = appBundle;
            PlayerSettings.productName = "Aetherward";
            PlayerSettings.bundleVersion = Game.App.Version;
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            var opts = new BuildPlayerOptions { scenes = Scenes(), locationPathName = path, target = target, options = options };
            BuildReport report = BuildPipeline.BuildPlayer(opts);
            BuildSummary sum = report.summary;
            string line = "Aetherward build " + target + " -> " + path + ": " + sum.result + ", " + (sum.totalSize / (1024 * 1024)) + " MB, " +
                          sum.totalErrors + " errors, " + sum.totalWarnings + " warnings, " + sum.totalTime;
            File.AppendAllText("Builds/build_log.txt", DateTime.Now.ToString("s") + " " + line + Environment.NewLine);
            Debug.Log(line);
            bool ok = sum.result == BuildResult.Succeeded;
            if (Application.isBatchMode) EditorApplication.Exit(ok ? 0 : 1);
            return ok;
        }

        [MenuItem("Aetherward/Build/Windows (Development)", priority = 100)]
        public static void WindowsDevelopment() =>
            Build(BuildTarget.StandaloneWindows64, BuildTargetGroup.Standalone, "Builds/WindowsDev/Aetherward.exe", BuildOptions.Development);

        [MenuItem("Aetherward/Build/Windows (Release)", priority = 101)]
        public static void WindowsRelease() =>
            Build(BuildTarget.StandaloneWindows64, BuildTargetGroup.Standalone, "Builds/Windows/Aetherward.exe", BuildOptions.None);

        [MenuItem("Aetherward/Build/Android APK (Development)", priority = 110)]
        public static void AndroidDevelopmentApk() =>
            Build(BuildTarget.Android, BuildTargetGroup.Android, "Builds/Android/Aetherward-dev.apk", BuildOptions.Development);

        [MenuItem("Aetherward/Build/Android AAB (Release, needs keystore)", priority = 111)]
        public static void AndroidReleaseAab() =>
            Build(BuildTarget.Android, BuildTargetGroup.Android, "Builds/Android/Aetherward.aab", BuildOptions.None, true);

        [MenuItem("Aetherward/Build/iOS Xcode Project (build on macOS)", priority = 120)]
        public static void IosXcodeProject() =>
            Build(BuildTarget.iOS, BuildTargetGroup.iOS, "Builds/iOS/Xcode", BuildOptions.None);
    }
}
