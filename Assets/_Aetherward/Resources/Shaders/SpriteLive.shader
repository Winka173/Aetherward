// Unit sprite shader (built-in renderer, premultiplied output like SpriteFlash) with:
//  - per-renderer flash (_Flash/_FlashColor, MaterialPropertyBlock only while flashing);
//  - readability rim: a thin lit edge on the sides facing _RimDir, from the sprite's own alpha. Global uniforms
//    (_AwRimColor, _AwRimStrength, _AwRimWidthPx) so every unit keeps batching; strength 0 disables it;
//  - dissolve (_Dissolve 0..1, per renderer while spawning/dying) with a glowing burn edge (_DissolveColor).
Shader "Aetherward/SpriteLive"
{
    Properties
    {
        [PerRendererData] _MainTex ("Sprite Texture", 2D) = "white" {}
        _FlashColor ("Flash Color", Color) = (1,1,1,1)
        _Flash ("Flash Amount", Range(0,1)) = 0
        _Dissolve ("Dissolve", Range(0,1)) = 0
        _DissolveColor ("Dissolve Edge", Color) = (1,0.35,0.45,1)
    }
    SubShader
    {
        Tags { "Queue"="Transparent" "IgnoreProjector"="True" "RenderType"="Transparent" "PreviewType"="Plane" "CanUseSpriteAtlas"="True" }
        Cull Off
        Lighting Off
        ZWrite Off
        Blend One OneMinusSrcAlpha

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            struct appdata
            {
                float4 vertex : POSITION;
                float4 color : COLOR;
                float2 uv : TEXCOORD0;
            };

            struct v2f
            {
                float4 pos : SV_POSITION;
                fixed4 color : COLOR;
                float2 uv : TEXCOORD0;
            };

            sampler2D _MainTex;
            float4 _MainTex_TexelSize;
            fixed4 _FlashColor;
            float _Flash;
            float _Dissolve;
            fixed4 _DissolveColor;
            fixed4 _AwRimColor;
            float _AwRimStrength;
            float _AwRimWidthPx;
            float2 _AwRimDir;

            v2f vert (appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.uv = v.uv;
                o.color = v.color;
                return o;
            }

            float hash(float2 p)
            {
                p = frac(p * float2(123.34, 456.21));
                p += dot(p, p + 45.32);
                return frac(p.x * p.y);
            }

            float noise(float2 p)
            {
                float2 i = floor(p), f = frac(p);
                float2 u = f * f * (3.0 - 2.0 * f);
                return lerp(lerp(hash(i), hash(i + float2(1, 0)), u.x), lerp(hash(i + float2(0, 1)), hash(i + float2(1, 1)), u.x), u.y);
            }

            fixed4 frag (v2f i) : SV_Target
            {
                fixed4 c = tex2D(_MainTex, i.uv) * i.color;
                if (_AwRimStrength > 0.001)
                {
                    float2 d = normalize(_AwRimDir) * _MainTex_TexelSize.xy * _AwRimWidthPx;
                    float n = min(tex2D(_MainTex, i.uv + d).a, min(tex2D(_MainTex, i.uv + d * 0.5).a, tex2D(_MainTex, i.uv + float2(d.x, -d.y) * 0.7).a));
                    float edge = saturate(c.a - n);
                    c.rgb += _AwRimColor.rgb * edge * _AwRimStrength;
                }
                c.rgb = lerp(c.rgb, _FlashColor.rgb, saturate(_Flash) * _FlashColor.a);
                if (_Dissolve > 0.001)
                {
                    float nz = noise(i.uv * 38.0) * 0.65 + noise(i.uv * 9.0) * 0.35;
                    float cut = _Dissolve * 1.08;
                    float burn = saturate(1.0 - (nz - cut) / 0.08);   // 1 right at the cut line, 0 beyond 0.08
                    c.rgb = lerp(c.rgb, _DissolveColor.rgb * 1.6, burn * step(cut, nz));
                    c.a *= step(cut, nz);
                }
                c.rgb *= c.a;
                return c;
            }
            ENDCG
        }
    }
}
