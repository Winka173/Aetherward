#!/usr/bin/env python3
"""Creates missing Unity .meta files under Assets/ with deterministic GUIDs (md5 of the asset path).

Deterministic GUIDs let hand-authored scenes reference scripts by GUID and keep references stable
across machines. Existing .meta files are never modified, except texture metas with --refresh-textures
(GUID kept) so pivot/PPU changes from the art pipeline reach Unity. Textures/audio get explicit importer
settings (sprite, point/bilinear, compression) so imports are reproducible without the Editor.
"""
import hashlib, os, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "Assets")

def guid_for(rel):
    return hashlib.md5(("aetherward:" + rel.replace("\\", "/")).encode()).hexdigest()

def folder_meta(g):
    return f"fileFormatVersion: 2\nguid: {g}\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {{}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n"

def script_meta(g):
    return f"fileFormatVersion: 2\nguid: {g}\nMonoImporter:\n  externalObjects: {{}}\n  serializedVersion: 2\n  defaultReferences: []\n  executionOrder: 0\n  icon: {{instanceID: 0}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n"

def default_meta(g):
    return f"fileFormatVersion: 2\nguid: {g}\nDefaultImporter:\n  externalObjects: {{}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n"

def text_meta(g):
    return f"fileFormatVersion: 2\nguid: {g}\nTextScriptImporter:\n  externalObjects: {{}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n"

def asmdef_meta(g):
    return f"fileFormatVersion: 2\nguid: {g}\nAssemblyDefinitionImporter:\n  externalObjects: {{}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n"

def font_meta(g):
    return (f"fileFormatVersion: 2\nguid: {g}\nTrueTypeFontImporter:\n  externalObjects: {{}}\n  serializedVersion: 4\n"
            "  fontSize: 16\n  forceTextureCase: -2\n  characterSpacing: 0\n  characterPadding: 1\n  includeFontData: 1\n"
            "  fontNames:\n  - Font\n  fallbackFontReferences: []\n  customCharacters: \n  fontRenderingMode: 0\n  ascentCalculationMode: 1\n"
            "  useLegacyBoundsCalculation: 0\n  shouldRoundAdvanceValue: 1\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n")

def audio_meta(g, streaming):
    load = 2 if streaming else 0  # 2 = Streaming, 0 = DecompressOnLoad
    fmt = 1  # Vorbis
    return (f"fileFormatVersion: 2\nguid: {g}\nAudioImporter:\n  externalObjects: {{}}\n  serializedVersion: 7\n"
            f"  defaultSettings:\n    serializedVersion: 2\n    loadType: {load}\n    sampleRateSetting: 0\n    sampleRateOverride: 44100\n"
            f"    compressionFormat: {fmt}\n    quality: 0.7\n    conversionMode: 0\n    preloadAudioData: 1\n"
            "  platformSettingOverrides: {}\n  forceToMono: 0\n  normalize: 0\n  loadInBackground: 0\n  ambisonic: 0\n  3D: 0\n"
            "  userData: \n  assetBundleName: \n  assetBundleVariant: \n")

def texture_meta(g, sprite, ppu, pivot, border, filter_mode, max_size):
    """Unity 6 TextureImporter for a single sprite (or plain texture for UI 9-slices)."""
    tex_type = 8 if sprite else 0
    px, py = pivot
    bl, bb, br, bt = border
    plat = ""
    for target in ("DefaultTexturePlatform", "Standalone", "Android", "iPhone"):
        plat += (f"  - serializedVersion: 4\n    buildTarget: {target}\n    maxTextureSize: {max_size}\n    resizeAlgorithm: 0\n"
                 f"    textureFormat: -1\n    textureCompression: 1\n    compressionQuality: 50\n    crunchedCompression: 0\n"
                 f"    allowsAlphaSplitting: 0\n    overridden: 0\n    ignorePlatformSupport: 0\n    androidETC2FallbackOverride: 0\n"
                 f"    forceMaximumCompressionQuality_BC6H_BC7: 0\n")
    return (f"fileFormatVersion: 2\nguid: {g}\nTextureImporter:\n  internalIDToNameTable: []\n  externalObjects: {{}}\n"
            f"  serializedVersion: 13\n  mipmaps:\n    mipMapMode: 0\n    enableMipMap: 0\n    sRGBTexture: 1\n    linearTexture: 0\n"
            f"    fadeOut: 0\n    borderMipMap: 0\n    mipMapsPreserveCoverage: 0\n    alphaTestReferenceValue: 0.5\n    mipMapFadeDistanceStart: 1\n"
            f"    mipMapFadeDistanceEnd: 3\n  bumpmap:\n    convertToNormalMap: 0\n    externalNormalMap: 0\n    heightScale: 0.25\n    normalMapFilter: 0\n"
            f"    flipGreenChannel: 0\n  isReadable: 0\n  streamingMipmaps: 0\n  streamingMipmapsPriority: 0\n  vTOnly: 0\n  ignoreMipmapLimit: 0\n"
            f"  grayScaleToAlpha: 0\n  generateCubemap: 6\n  cubemapConvolution: 0\n  seamlessCubemap: 0\n  textureFormat: 1\n  maxTextureSize: {max_size}\n"
            f"  textureSettings:\n    serializedVersion: 2\n    filterMode: {filter_mode}\n    aniso: 1\n    mipBias: 0\n    wrapU: 1\n    wrapV: 1\n    wrapW: 1\n"
            f"  nPOTScale: 0\n  lightmap: 0\n  compressionQuality: 50\n  spriteMode: {1 if sprite else 0}\n  spriteExtrude: 1\n  spriteMeshType: {0 if any(border) else 1}\n"
            f"  alignment: 9\n  spritePivot: {{x: {px}, y: {py}}}\n  spritePixelsToUnits: {ppu}\n  spriteBorder: {{x: {bl}, y: {bb}, z: {br}, w: {bt}}}\n"
            f"  spriteGenerateFallbackPhysicsShape: 0\n  alphaUsage: 1\n  alphaIsTransparency: 1\n  spriteTessellationDetail: -1\n"
            f"  textureType: {tex_type}\n  textureShape: 1\n  singleChannelComponent: 0\n  flipbookRows: 1\n  flipbookColumns: 1\n"
            f"  maxTextureSizeSet: 0\n  compressionQualitySet: 0\n  textureFormatSet: 0\n  ignorePngGamma: 0\n  applyGammaDecoding: 0\n"
            f"  swizzle: 50462976\n  cookieLightType: 0\n  platformSettings:\n{plat}"
            f"  spriteSheet:\n    serializedVersion: 2\n    sprites: []\n    outline: []\n    customData: \n    physicsShape: []\n    bones: []\n"
            f"    spriteID: 5e97eb03825dee720800000000000000\n    internalID: 0\n    vertices: []\n    indices: \n    edges: []\n    weights: []\n"
            f"    secondaryTextures: []\n    spriteCustomMetadata:\n      entries: []\n    nameFileIdTable: {{}}\n"
            f"  mipmapLimitGroupName: \n  pSDRemoveMatte: 0\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n")

def load_sprite_settings():
    """Per-PNG import settings written by the art pipeline (pivot, ppu, 9-slice border)."""
    path = os.path.join(ROOT, "Tools", "AssetGen", "import_settings.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

REFRESH_TEXTURES = "--refresh-textures" in sys.argv


def existing_guid(meta_path):
    """Keep the GUID of an existing .meta (references in scenes/prefabs must survive a refresh)."""
    if not os.path.exists(meta_path):
        return None
    with open(meta_path) as f:
        for line in f:
            if line.startswith("guid:"):
                return line.split(":", 1)[1].strip()
    return None


def main():
    created = refreshed = 0
    settings = load_sprite_settings()
    for dirpath, dirnames, filenames in os.walk(ASSETS):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        rel_dir = os.path.relpath(dirpath, ROOT).replace("\\", "/")
        entries = [(d, True) for d in dirnames] + [(f, False) for f in filenames]
        for name, is_dir in entries:
            if name.endswith(".meta") or name.startswith("."):
                continue
            rel = rel_dir + "/" + name
            meta_path = os.path.join(ROOT, rel + ".meta")
            ext0 = os.path.splitext(name)[1].lower()
            refresh = REFRESH_TEXTURES and not is_dir and ext0 == ".png" and rel in settings
            if os.path.exists(meta_path) and not refresh:
                continue
            g = existing_guid(meta_path) or guid_for(rel)
            ext = os.path.splitext(name)[1].lower()
            if is_dir: content = folder_meta(g)
            elif ext == ".cs": content = script_meta(g)
            elif ext == ".asmdef": content = asmdef_meta(g)
            elif ext in (".json", ".txt", ".md", ".csv", ".bytes"): content = text_meta(g)
            elif ext in (".ttf", ".otf"): content = font_meta(g)
            elif ext in (".wav", ".ogg"): content = audio_meta(g, "/Music/" in rel)
            elif ext == ".png":
                s = settings.get(rel, {})
                content = texture_meta(g, s.get("sprite", True), s.get("ppu", 100), tuple(s.get("pivot", [0.5, 0.5])),
                                       tuple(s.get("border", [0, 0, 0, 0])), s.get("filter", 1), s.get("maxSize", 2048))
            else: content = default_meta(g)
            if os.path.exists(meta_path):
                with open(meta_path) as f:
                    if f.read() == content:
                        continue
                refreshed += 1
            else:
                created += 1
            with open(meta_path, "w", newline="\n") as f:
                f.write(content)
    print(f"gen_meta: created {created} meta files" + (f", refreshed {refreshed} texture metas" if REFRESH_TEXTURES else ""))

if __name__ == "__main__":
    main()
