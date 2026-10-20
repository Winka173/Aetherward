// Directional cast shadow of a unit sprite on the ground (built-in renderer, premultiplied blending).
// The renderer shares the unit's sprite; its pivot is the feet, so the height of a vertex above the pivot (world space,
// independent of the left/right flip) is projected along the light: offset = _AwShadowDir * height * _AwShadowLength.
// The shadow is darkest at the feet and fades and softens with height. Global uniforms keep all shadows in one batch.
Shader "Aetherward/SpriteCastShadow"
{
    Properties
    {
        [PerRendererData] _MainTex ("Sprite Texture", 2D) = "white" {}
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
                float h : TEXCOORD1;
            };

            sampler2D _MainTex;
            float4 _MainTex_TexelSize;
            float2 _AwShadowDir;        // screen-space direction of the shadow (unit vector)
            float _AwShadowLength;      // screen length of the shadow per unit of sprite height
            float _AwShadowStrength;    // 0 disables
            float _AwShadowHeight;      // world height at which the shadow has faded out

            v2f vert (appdata v)
            {
                v2f o;
                float3 world = mul(unity_ObjectToWorld, v.vertex).xyz;
                float3 origin = float3(unity_ObjectToWorld._m03, unity_ObjectToWorld._m13, unity_ObjectToWorld._m23);
                float3 rel = world - origin;
                float height = max(rel.y, 0.0);
                world.xy = origin.xy + float2(rel.x, 0.0) + _AwShadowDir * height * _AwShadowLength;
                o.pos = mul(UNITY_MATRIX_VP, float4(world, 1.0));
                o.uv = v.uv;
                o.color = v.color;
                o.h = saturate(height / max(_AwShadowHeight, 0.01));
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                // soften with height: a wider alpha footprint higher up the body
                float2 t = _MainTex_TexelSize.xy * (2.0 + 10.0 * i.h);
                float a = tex2D(_MainTex, i.uv).a * 0.4
                        + (tex2D(_MainTex, i.uv + float2(t.x, 0)).a + tex2D(_MainTex, i.uv - float2(t.x, 0)).a
                         + tex2D(_MainTex, i.uv + float2(0, t.y)).a + tex2D(_MainTex, i.uv - float2(0, t.y)).a) * 0.15;
                a *= _AwShadowStrength * (1.0 - 0.75 * i.h) * i.color.a;
                return fixed4(0, 0, 0, a);
            }
            ENDCG
        }
    }
}
