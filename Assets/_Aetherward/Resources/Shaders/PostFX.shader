// Battle post-processing for the built-in renderer (OnRenderImage): soft-knee bloom (prefilter, box downsample,
// tent upsample-add), then a final pass with a light colour grade (lift/gamma/gain, saturation) and a vignette.
Shader "Hidden/Aetherward/PostFX"
{
    Properties
    {
        _MainTex ("Source", 2D) = "black" {}
    }
    CGINCLUDE
    #include "UnityCG.cginc"
    sampler2D _MainTex;
    float4 _MainTex_TexelSize;
    sampler2D _BloomTex;
    float4 _Threshold;        // x threshold, y knee, z clamp
    float _BloomIntensity;
    float4 _Lift, _Gamma, _Gain;
    float _Saturation;
    float _Vignette;
    float4 _Haze;             // rgb colour, a strength: cool depth haze toward the far (top) edge
    float4 _SunGlow;          // rgb colour, a strength: soft warm light from the key light's corner (upper left)

    half3 Prefilter(half3 c)
    {
        half br = max(c.r, max(c.g, c.b));
        half soft = clamp(br - _Threshold.x + _Threshold.y, 0, 2 * _Threshold.y);
        soft = soft * soft / (4 * _Threshold.y + 1e-4);
        half contrib = max(soft, br - _Threshold.x) / max(br, 1e-4);
        return min(c * contrib, _Threshold.z);
    }

    half3 Box(float2 uv, float d)
    {
        float4 o = _MainTex_TexelSize.xyxy * float2(-d, d).xxyy;
        return (tex2D(_MainTex, uv + o.xy).rgb + tex2D(_MainTex, uv + o.zy).rgb + tex2D(_MainTex, uv + o.xw).rgb + tex2D(_MainTex, uv + o.zw).rgb) * 0.25;
    }
    ENDCG

    SubShader
    {
        Cull Off ZWrite Off ZTest Always
        Pass // 0 prefilter + first downsample
        {
            CGPROGRAM
            #pragma vertex vert_img
            #pragma fragment frag
            half4 frag (v2f_img i) : SV_Target { return half4(Prefilter(Box(i.uv, 1)), 1); }
            ENDCG
        }
        Pass // 1 downsample
        {
            CGPROGRAM
            #pragma vertex vert_img
            #pragma fragment frag
            half4 frag (v2f_img i) : SV_Target { return half4(Box(i.uv, 1), 1); }
            ENDCG
        }
        Pass // 2 upsample, added onto the larger level
        {
            Blend One One
            CGPROGRAM
            #pragma vertex vert_img
            #pragma fragment frag
            half4 frag (v2f_img i) : SV_Target { return half4(Box(i.uv, 0.5), 1); }
            ENDCG
        }
        Pass // 3 composite + grade + vignette
        {
            CGPROGRAM
            #pragma vertex vert_img
            #pragma fragment frag
            half4 frag (v2f_img i) : SV_Target
            {
                half3 c = tex2D(_MainTex, i.uv).rgb + tex2D(_BloomTex, i.uv).rgb * _BloomIntensity;
                c = pow(max(c * _Gain.rgb + _Lift.rgb * (1 - c), 0), 1.0 / max(_Gamma.rgb, 0.01));
                half l = dot(c, half3(0.2126, 0.7152, 0.0722));
                c = lerp(l.xxx, c, _Saturation);
                c = lerp(c, _Haze.rgb, _Haze.a * smoothstep(0.55, 1.0, i.uv.y));
                c += _SunGlow.rgb * _SunGlow.a * (1 - smoothstep(0.0, 0.95, distance(i.uv * float2(1.6, 1), float2(0.0, 1.08))));
                float2 d = i.uv - 0.5;
                c *= 1 - _Vignette * smoothstep(0.35, 0.95, dot(d, d) * 2.2);
                return half4(c, 1);
            }
            ENDCG
        }
    }
}
