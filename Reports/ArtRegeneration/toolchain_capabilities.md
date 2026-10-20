# Toolchain capabilities (probed by Tools/ArtPipeline/audit.py)

| Tool | Probe | Result |
|---|---|---|
| Blender | `blender --version` | Blender 4.0.2 |
| Blender EEVEE | headless render | BLOCKED: aborts, `libEGL.so.1` missing (Reports/ArtQuality/blender_benchmark/DECISION.md) |
| Blender Cycles CPU | headless render | OK (no OpenImageDenoiser; denoise off) |
| Unity Editor | `which Unity unity-editor` | NOT AVAILABLE (no batchmode import/compile/playmode/build possible) |
| Unity version (project) | ProjectSettings/ProjectVersion.txt | m_EditorVersion: 6000.4.8f1 |
| Python | `python3 --version` | Python 3.13.16 |
| Pillow / NumPy / pycairo | import | 12.3.0 2.5.3 1.29.2 |
| ImageMagick | `convert -version` | Version: ImageMagick 6.9.12-98 Q16 x86_64 18038 https://legacy.imagemagick.org |
| .NET | `dotnet --version` | 8.0.131 |
| Unity/Blender MCP | session tools | not connected |
| Paid AI image services | — | not used (no credentials; brief forbids assuming access) |
