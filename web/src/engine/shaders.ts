/** GLSL for the timeline. Node data lives in textures so nodes and links read one source of truth. */
export const TEX_WIDTH = 1024

const HEADER = /* glsl */ `#version 300 es
precision highp float;
precision highp int;
precision highp sampler2D;
`

const WORLD = /* glsl */ `
uniform vec2 uRes;
uniform vec2 uCam;
uniform vec2 uScale;
uniform vec2 uCenter;
uniform vec4 uTimeScale;
uniform float uWarp;
uniform float uDpr;
uniform sampler2D uNodeA;
uniform sampler2D uNodeB;
uniform sampler2D uState;
uniform vec4 uReveal;

float timeU(float t) {
  float lin = (t - uTimeScale.x) / (uTimeScale.y - uTimeScale.x);
  float compressed = 1.0 - log(1.0 + (uTimeScale.y - t) / uTimeScale.z) / uTimeScale.w;
  return mix(lin, compressed, uWarp);
}
vec2 worldToPx(float t, float y) {
  return vec2((timeU(t) - uCam.x) * uScale.x + uCenter.x, (y - uCam.y) * uScale.y + uCenter.y);
}
vec4 pxToClip(vec2 p) {
  vec2 c = p / uRes * 2.0 - 1.0;
  return vec4(c.x, -c.y, 0.0, 1.0);
}
ivec2 texel(int id) {
  return ivec2(id % ${TEX_WIDTH}, id / ${TEX_WIDTH});
}
// state: x = passes filters, y = dimmed, z = emphasised, w = shown regardless of zoom
float visible(vec4 state, float level) {
  return state.x * max(uReveal[int(level)], state.w);
}
// Nodes below the current depth stay as faint dust, so the whole network is always
// present and zooming brings detail into focus rather than popping it into existence.
const float DUST = 0.3;
float presence(vec4 state, float level) {
  return state.x * mix(DUST, 1.0, max(uReveal[int(level)], state.w));
}
`

export const NODE_VS = HEADER + WORLD + /* glsl */ `
layout(location = 0) in vec2 aCorner;
uniform float uNodeAlpha;
uniform int uHover;
uniform int uSelected;
flat out vec3 vColor;
flat out vec4 vInfo;
flat out vec2 vExtra;
out vec2 vPx;

void main() {
  int id = gl_InstanceID;
  ivec2 tc = texel(id);
  vec4 a = texelFetch(uNodeA, tc, 0);
  vec4 b = texelFetch(uNodeB, tc, 0);
  vec4 s = texelFetch(uState, tc, 0);
  float v = visible(s, b.a);
  float alpha = presence(s, b.a) * mix(1.0, 0.1, s.y) * uNodeAlpha;
  float mark = id == uSelected ? 1.0 : (id == uHover ? 0.65 : 0.0);
  alpha = max(alpha, mark);
  if (alpha < 0.004) {
    gl_Position = vec4(3.0, 3.0, 3.0, 1.0);
    return;
  }
  float r = a.z * uDpr * (0.42 + 0.58 * v) * (1.0 + 0.4 * s.z + 0.18 * mark);
  // Quads stay tight: with tens of thousands of nodes, fill rate is the main GPU cost.
  bool wide = b.a < 0.5 || mark > 0.0 || s.z > 0.05;
  float halfSize = wide ? r * 2.9 + 8.0 * uDpr : r * 2.0 + 2.0 * uDpr;
  vec2 c = worldToPx(a.x, a.y);
  if (c.x < -halfSize || c.x > uRes.x + halfSize || c.y < -halfSize || c.y > uRes.y + halfSize) {
    gl_Position = vec4(3.0, 3.0, 3.0, 1.0);
    return;
  }
  vPx = aCorner * halfSize;
  gl_Position = pxToClip(c + vPx);
  vColor = b.rgb;
  vInfo = vec4(a.w, r, alpha, s.z);
  vExtra = vec2(mark, b.a);
}
`

export const NODE_FS = HEADER + /* glsl */ `
uniform float uDpr;
flat in vec3 vColor;
flat in vec4 vInfo;
flat in vec2 vExtra;
in vec2 vPx;
out vec4 fragColor;

float sdHexagon(vec2 p, float r) {
  const vec3 k = vec3(-0.866025404, 0.5, 0.577350269);
  p = abs(p);
  p -= 2.0 * min(dot(k.xy, p), 0.0) * k.xy;
  p -= vec2(clamp(p.x, -k.z * r, k.z * r), r);
  return length(p) * sign(p.y);
}
float sdRoundBox(vec2 p, float r, float round_) {
  vec2 q = abs(p) - vec2(r - round_);
  return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - round_;
}
float shapeDistance(float shape, vec2 p, float r) {
  if (shape < 0.5) return length(p) - r;                    // discovery: disc
  if (shape < 1.5) return abs(length(p) - r * 0.8) - r * 0.26; // theory: ring
  if (shape < 2.5) return sdRoundBox(p, r * 0.88, r * 0.22);  // instrument: square
  if (shape < 3.5) return (abs(p.x) + abs(p.y)) * 0.7071 - r * 0.86; // invention: diamond
  return sdHexagon(p.yx, r * 0.92);                          // system: hexagon
}

void main() {
  float shape = vInfo.x;
  float r = vInfo.y;
  float alpha = vInfo.z;
  float boost = vInfo.w;
  float mark = vExtra.x;
  bool stepNode = vExtra.y < 0.5;

  float d = shapeDistance(shape, vPx, r);
  float aa = 0.9 * uDpr;
  float fill = 1.0 - smoothstep(-aa, aa, d);

  vec3 lifted = mix(vColor, vec3(1.0), 0.16);
  vec3 body = lifted * (1.05 + 0.5 * boost);
  // A brighter rim gives small shapes a crisp edge against the glow.
  float rim = (1.0 - smoothstep(0.0, 1.4 * uDpr, abs(d + 0.9 * uDpr))) * fill;
  body += mix(vColor, vec3(1.0), 0.6) * rim * 0.4;

  float outside = max(d, 0.0);
  float glow = exp(-outside / (r * 0.75 + 1.5 * uDpr)) * (0.13 + 0.5 * boost + (stepNode ? 0.2 : 0.0));
  vec3 rgb = body * fill + vColor * glow * (1.0 - fill);
  float a = fill;

  float dist = length(vPx);
  if (stepNode) {
    float halo = 1.0 - smoothstep(0.0, 1.2 * uDpr, abs(dist - r * 1.72));
    rgb += mix(vColor, vec3(1.0), 0.3) * halo * 0.65;
  }
  if (mark > 0.0) {
    float ring = 1.0 - smoothstep(0.5 * uDpr, 1.9 * uDpr, abs(dist - (r * 1.4 + 3.5 * uDpr)));
    rgb += vec3(1.0) * ring * mark;
    a = max(a, ring * mark);
  }
  fragColor = vec4(rgb, a) * alpha;
}
`

export const EDGE_VS = HEADER + WORLD + /* glsl */ `
layout(location = 0) in vec2 aVert;
layout(location = 1) in uvec2 aEdge;
layout(location = 2) in float aSoft;
uniform float uEdgeAlpha;
out float vSide;
out float vT;
flat out vec3 vColorA;
flat out vec3 vColorB;
flat out vec4 vInfo;
flat out float vLen;

void main() {
  int si = int(aEdge.x);
  int ti = int(aEdge.y);
  ivec2 sc = texel(si);
  ivec2 tc = texel(ti);
  vec4 sa = texelFetch(uNodeA, sc, 0);
  vec4 ta = texelFetch(uNodeA, tc, 0);
  vec4 sb = texelFetch(uNodeB, sc, 0);
  vec4 tb = texelFetch(uNodeB, tc, 0);
  vec4 ss = texelFetch(uState, sc, 0);
  vec4 ts = texelFetch(uState, tc, 0);

  float vis = min(presence(ss, sb.a), presence(ts, tb.a));
  float boost = min(ss.z, ts.z);
  float dim = max(ss.y, ts.y);
  float alpha = vis * mix(1.0, 0.05, dim) * (uEdgeAlpha + boost * 0.7);
  if (alpha < 0.006) {
    gl_Position = vec4(3.0, 3.0, 3.0, 1.0);
    return;
  }

  vec2 p0 = worldToPx(sa.x, sa.y);
  vec2 p3 = worldToPx(ta.x, ta.y);
  float margin = 60.0 * uDpr;
  if ((p0.x < -margin && p3.x < -margin) || (p0.x > uRes.x + margin && p3.x > uRes.x + margin) ||
      (p0.y < -margin && p3.y < -margin) || (p0.y > uRes.y + margin && p3.y > uRes.y + margin)) {
    gl_Position = vec4(3.0, 3.0, 3.0, 1.0);
    return;
  }

  // Horizontal tangents at both ends make links read as flow along time.
  float handle = max((p3.x - p0.x) * 0.5, 14.0 * uDpr);
  vec2 p1 = p0 + vec2(handle, 0.0);
  vec2 p2 = p3 - vec2(handle, 0.0);
  float t = aVert.x;
  float it = 1.0 - t;
  vec2 pos = it * it * it * p0 + 3.0 * it * it * t * p1 + 3.0 * it * t * t * p2 + t * t * t * p3;
  vec2 tangent = 3.0 * it * it * (p1 - p0) + 6.0 * it * t * (p2 - p1) + 3.0 * t * t * (p3 - p2);
  vec2 normal = normalize(vec2(-tangent.y, tangent.x) + vec2(1e-5, 0.0));

  float halfWidth = (0.55 + 0.75 * boost) * uDpr;
  float expand = halfWidth + 1.2 * uDpr;
  gl_Position = pxToClip(pos + normal * aVert.y * expand);
  vSide = aVert.y * expand;
  vT = t;
  vColorA = sb.rgb;
  vColorB = tb.rgb;
  vLen = distance(p0, p3) + 1.0;
  // Long links recede unless emphasised, so distant connections do not become a hairball.
  float recede = mix(1.0, 0.3, smoothstep(220.0 * uDpr, 1100.0 * uDpr, vLen));
  vInfo = vec4(halfWidth, alpha * mix(recede, 1.0, boost), boost, aSoft);
}
`

export const EDGE_FS = HEADER + /* glsl */ `
uniform float uDpr;
uniform float uTimeS;
in float vSide;
in float vT;
flat in vec3 vColorA;
flat in vec3 vColorB;
flat in vec4 vInfo;
flat in float vLen;
out vec4 fragColor;

void main() {
  float halfWidth = vInfo.x;
  float alpha = vInfo.y;
  float boost = vInfo.z;
  float edge = 1.0 - smoothstep(halfWidth - 0.6 * uDpr, halfWidth + 0.8 * uDpr, abs(vSide));
  float along = vT * vLen / uDpr;
  if (vInfo.w > 0.5) edge *= step(0.42, fract(along / 7.0));
  vec3 color = mix(vColorA, vColorB, vT);
  // Pulses travel from cause to effect along emphasised links.
  float pulse = pow(0.5 + 0.5 * sin((along / 54.0 - uTimeS * 0.9) * 6.2832), 8.0);
  color = mix(color, vec3(1.0), 0.12) * (1.0 + pulse * boost * 2.2);
  fragColor = vec4(color * edge * alpha, 0.0);
}
`

export const DENSITY_VS = HEADER + WORLD + /* glsl */ `
layout(location = 0) in vec2 aCorner;
uniform float uKernel;
flat out vec3 vColor;
out vec2 vP;

void main() {
  int id = gl_InstanceID;
  ivec2 tc = texel(id);
  vec4 a = texelFetch(uNodeA, tc, 0);
  vec4 b = texelFetch(uNodeB, tc, 0);
  vec4 s = texelFetch(uState, tc, 0);
  float w = s.x * mix(1.0, 0.25, s.y);
  if (w < 0.01) {
    gl_Position = vec4(3.0, 3.0, 3.0, 1.0);
    return;
  }
  vec2 c = worldToPx(a.x, a.y);
  if (c.x < -uKernel || c.x > uRes.x + uKernel || c.y < -uKernel || c.y > uRes.y + uKernel) {
    gl_Position = vec4(3.0, 3.0, 3.0, 1.0);
    return;
  }
  vP = aCorner;
  gl_Position = pxToClip(c + aCorner * uKernel);
  vColor = b.rgb * w;
}
`

export const DENSITY_FS = HEADER + /* glsl */ `
flat in vec3 vColor;
in vec2 vP;
out vec4 fragColor;
void main() {
  float d = dot(vP, vP);
  if (d > 1.0) discard;
  float k = exp(-d * 4.0) - 0.0183;
  fragColor = vec4(vColor * k, k);
}
`

export const RECT_VS = HEADER + /* glsl */ `
layout(location = 0) in vec2 aCorner;
layout(location = 1) in vec4 aRect;
layout(location = 2) in vec4 aColor;
layout(location = 3) in float aKind;
uniform vec2 uRes;
out vec2 vUv;
flat out vec4 vColor;
flat out float vKind;
void main() {
  vec2 uv = aCorner * 0.5 + 0.5;
  vec2 p = mix(aRect.xy, aRect.zw, uv);
  vec2 c = p / uRes * 2.0 - 1.0;
  gl_Position = vec4(c.x, -c.y, 0.0, 1.0);
  vUv = uv;
  vColor = aColor;
  vKind = aKind;
}
`

export const RECT_FS = HEADER + /* glsl */ `
in vec2 vUv;
flat in vec4 vColor;
flat in float vKind;
out vec4 fragColor;
void main() {
  float a = 1.0;
  // Beam: bright centre fading sideways and towards the bottom.
  if (vKind > 0.5) a = pow(1.0 - abs(vUv.x * 2.0 - 1.0), 2.0) * pow(1.0 - vUv.y, 1.2);
  fragColor = vec4(vColor.rgb * vColor.a * a, vColor.a * a);
}
`

const FULLSCREEN_VS = HEADER + /* glsl */ `
layout(location = 0) in vec2 aCorner;
out vec2 vUv;
void main() {
  vUv = aCorner * 0.5 + 0.5;
  gl_Position = vec4(aCorner, 0.0, 1.0);
}
`

export const HAZE_VS = FULLSCREEN_VS
export const HAZE_FS = HEADER + /* glsl */ `
uniform sampler2D uTex;
uniform float uGain;
uniform float uIntensity;
uniform float uContours;
in vec2 vUv;
out vec4 fragColor;
void main() {
  vec4 s = texture(uTex, vUv);
  float amount = s.a * uGain;
  // Chromatic average keeps colours saturated however many nodes overlap.
  vec3 hue = s.a > 1e-4 ? s.rgb / s.a : vec3(0.0);
  float level = 1.0 - exp(-amount);
  vec3 color = hue * level + vec3(1.0) * pow(level, 7.0) * 0.14;
  // Thin iso-density contours make the field readable as a measure, not only a glow.
  if (uContours > 0.001 && amount > 0.012) {
    float v = log2(amount) * 0.9;
    float width = fwidth(v);
    float line = 1.0 - smoothstep(width * 0.4, width * 1.4, abs(fract(v) - 0.5));
    color += (hue * 0.8 + 0.1) * line * 0.09 * uContours * smoothstep(0.02, 0.1, amount);
  }
  fragColor = vec4(color * uIntensity, 0.0);
}
`

export const BLOOM_DOWN_VS = FULLSCREEN_VS
export const BLOOM_DOWN_FS = HEADER + /* glsl */ `
uniform sampler2D uTex;
uniform vec2 uTexel;
uniform float uThreshold;
in vec2 vUv;
out vec4 fragColor;
void main() {
  vec3 c = texture(uTex, vUv).rgb * 4.0;
  c += texture(uTex, vUv + uTexel * vec2(-1.0, -1.0)).rgb;
  c += texture(uTex, vUv + uTexel * vec2(1.0, -1.0)).rgb;
  c += texture(uTex, vUv + uTexel * vec2(-1.0, 1.0)).rgb;
  c += texture(uTex, vUv + uTexel * vec2(1.0, 1.0)).rgb;
  c /= 8.0;
  if (uThreshold > 0.0) c = max(c - uThreshold, 0.0);
  fragColor = vec4(c, 1.0);
}
`

export const BLOOM_UP_VS = FULLSCREEN_VS
export const BLOOM_UP_FS = HEADER + /* glsl */ `
uniform sampler2D uTex;
uniform vec2 uTexel;
in vec2 vUv;
out vec4 fragColor;
void main() {
  vec3 c = texture(uTex, vUv + uTexel * vec2(-2.0, 0.0)).rgb;
  c += texture(uTex, vUv + uTexel * vec2(2.0, 0.0)).rgb;
  c += texture(uTex, vUv + uTexel * vec2(0.0, -2.0)).rgb;
  c += texture(uTex, vUv + uTexel * vec2(0.0, 2.0)).rgb;
  c += texture(uTex, vUv + uTexel * vec2(-1.0, -1.0)).rgb * 2.0;
  c += texture(uTex, vUv + uTexel * vec2(1.0, -1.0)).rgb * 2.0;
  c += texture(uTex, vUv + uTexel * vec2(-1.0, 1.0)).rgb * 2.0;
  c += texture(uTex, vUv + uTexel * vec2(1.0, 1.0)).rgb * 2.0;
  fragColor = vec4(c / 12.0, 1.0);
}
`

export const COMPOSITE_VS = FULLSCREEN_VS
export const COMPOSITE_FS = HEADER + /* glsl */ `
uniform sampler2D uScene;
uniform sampler2D uBloom;
uniform float uBloomAmount;
uniform vec2 uRes;
in vec2 vUv;
out vec4 fragColor;

float noise(vec2 p) {
  return fract(52.9829189 * fract(dot(p, vec2(0.06711056, 0.00583715))));
}
void main() {
  vec3 c = texture(uScene, vUv).rgb + texture(uBloom, vUv).rgb * uBloomAmount;
  // Soft shoulder: values stay faithful up to 0.7, then roll off rather than clip.
  vec3 over = max(c - 0.7, 0.0);
  c = min(c, 0.7) + 0.3 * (1.0 - exp(-over / 0.3));
  vec2 q = vUv - 0.5;
  c *= 1.0 - dot(q, q) * 0.38;
  // Dithering prevents banding in dark gradients.
  c += (noise(gl_FragCoord.xy) - 0.5) / 255.0;
  fragColor = vec4(c, 1.0);
}
`
