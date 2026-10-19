#!/usr/bin/env bash
# Downloads Unity reference assemblies (Unity3D.SDK NuGet package) into Tools/UnityRefs for the
# compile-only check in Tools/SimHarness/UnityCheck. These DLLs are NOT committed.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p UnityRefs /tmp/aetherward_refs
curl -sL -o /tmp/aetherward_refs/sdk.nupkg https://api.nuget.org/v3-flatcontainer/unity3d.sdk/2021.1.14.1/unity3d.sdk.2021.1.14.1.nupkg
unzip -o -q /tmp/aetherward_refs/sdk.nupkg -d /tmp/aetherward_refs/sdk
cp /tmp/aetherward_refs/sdk/lib/UnityEngine.dll /tmp/aetherward_refs/sdk/lib/UnityEditor.dll UnityRefs/
echo "Unity reference assemblies ready in Tools/UnityRefs"
