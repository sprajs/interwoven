import { LUT_SIZE } from './time.ts'

/**
 * GLSL for the chart: pen strokes and inked marks on a sheet of paper.
 * Nothing here glows. Strokes multiply onto the page, so crossings darken as real ink does.
 */
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
uniform sampler2D uTimeLut;

float timeU(float t) {
  float lin = (t - uTimeScale.x) / (uTimeScale.y - uTimeScale.x);
  float position = clamp(log(1.0 + (uTimeScale.y - t) / uTimeScale.z) / uTimeScale.w, 0.0, 1.0);
  float f = position * ${LUT_SIZE - 1}.0;
  int i = min(int(f), ${LUT_SIZE - 2});
  float compressed = mix(texelFetch(uTimeLut, ivec2(i, 0), 0).r, texelFetch(uTimeLut, ivec2(i + 1, 0), 0).r, f - float(i));
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
// state: x = passes filters, y = faded, z = emphasised, w = shown regardless of zoom
float visible(vec4 state, float level) {
  return state.x * max(uReveal[int(level)], state.w);
}
float hash(float n) {
  return fract(sin(n * 12.9898) * 43758.5453);
}
// Smooth 1D noise for the slight unsteadiness of a hand.
float wander(float x) {
  float i = floor(x);
  float f = fract(x);
  f = f * f * (3.0 - 2.0 * f);
  return mix(hash(i), hash(i + 1.0), f) * 2.0 - 1.0;
}
`

/** The graphite the page falls back to when something is faded. */
const GRAPHITE = 'vec3(0.56, 0.53, 0.49)'

export const NODE_VS = HEADER + WORLD + /* glsl */ `
layout(location = 0) in vec2 aCorner;
uniform float uNodeAlpha;
uniform int uHover;
uniform int uSelected;
uniform float uDrawU;
flat out vec3 vColor;
flat out vec4 vInfo;
flat out vec3 vExtra;
out vec2 vPx;

void main() {
  int id = gl_InstanceID;
  ivec2 tc = texel(id);
  vec4 a = texelFetch(uNodeA, tc, 0);
  vec4 b = texelFetch(uNodeB, tc, 0);
  vec4 s = texelFetch(uState, tc, 0);
  float v = visible(s, b.a);
  float mark = id == uSelected ? 1.0 : (id == uHover ? 0.7 : 0.0);
  float u = timeU(a.x);
  float drawn = smoothstep(u - 0.004, u + 0.004, uDrawU);
  // Below the current depth a node is only a faint point on its thread.
  float alpha = max(s.x * mix(0.42, 1.0, v) * mix(1.0, 0.3, s.y) * uNodeAlpha, mark) * drawn;
  if (alpha < 0.01) {
    gl_Position = vec4(3.0, 3.0, 3.0, 1.0);
    return;
  }
  float r = a.z * uDpr * mix(0.5, 1.0, v) * (1.0 + 0.2 * s.z);
  float halfSize = r * 1.25 + 2.0 * uDpr + mark * (r + 7.0 * uDpr);
  vec2 c = worldToPx(a.x, a.y);
  if (c.x < -halfSize || c.x > uRes.x + halfSize || c.y < -halfSize || c.y > uRes.y + halfSize) {
    gl_Position = vec4(3.0, 3.0, 3.0, 1.0);
    return;
  }
  vPx = aCorner * halfSize;
  gl_Position = pxToClip(c + vPx);
  vColor = mix(${GRAPHITE}, b.rgb, mix(1.0, 0.25, s.y));
  vInfo = vec4(a.w, r, alpha, hash(float(id) + 3.1) * 6.283);
  vExtra = vec3(mark, v, b.a);
}
`

export const NODE_FS = HEADER + /* glsl */ `
uniform float uDpr;
uniform vec3 uPaper;
flat in vec3 vColor;
flat in vec4 vInfo;
flat in vec3 vExtra;
in vec2 vPx;
out vec4 fragColor;

void main() {
  float kind = vInfo.x;
  float r = vInfo.y;
  float alpha = vInfo.z;
  float seed = vInfo.w;
  float mark = vExtra.x;

  float dist = length(vPx);
  float angle = atan(vPx.y, vPx.x);
  // No hand draws a perfect circle.
  float edge = r * (1.0 + 0.05 * sin(angle * 2.0 + seed) + 0.03 * sin(angle * 3.0 + seed * 2.0));
  float aa = 0.75 * uDpr;

  vec3 rgb = uPaper;
  float a = 0.0;

  float disc = 1.0 - smoothstep(edge - aa, edge + aa, dist);
  if (kind < 0.5) {
    // Technology: a solid drop of ink.
    rgb = vColor;
    a = disc;
  } else {
    // Science: an open ring, thick and thin as a broad nib turns around it.
    float nib = abs(sin(angle + 0.7));
    float thick = max(0.9 * uDpr, r * (0.2 + 0.26 * nib));
    float inner = 1.0 - smoothstep(edge - thick - aa, edge - thick + aa, dist);
    rgb = mix(vColor, uPaper, inner);
    a = disc;
  }

  if (mark > 0.0) {
    // A fine circle drawn around whatever has your attention.
    float ringR = r + 5.5 * uDpr;
    float wobble = ringR * (1.0 + 0.03 * sin(angle * 2.0 + seed));
    float nib = 0.55 + 0.45 * abs(sin(angle + 0.7));
    float ring = 1.0 - smoothstep(0.35 * uDpr, 1.15 * uDpr, abs(dist - wobble) / nib);
    rgb = mix(rgb, vec3(0.15, 0.13, 0.11), ring * (1.0 - a));
    a = max(a, ring * mark);
  }
  fragColor = vec4(rgb * a, a) * alpha;
}
`

export const EDGE_VS = HEADER + WORLD + /* glsl */ `
layout(location = 0) in vec2 aVert;
layout(location = 1) in uvec2 aEdge;
layout(location = 2) in float aTentative;
uniform float uEdgeAlpha;
out float vSide;
out float vT;
out float vU;
flat out vec3 vColorA;
flat out vec3 vColorB;
flat out vec4 vInfo;
flat out vec2 vExtra;
out float vHalf;

const float NIB_ANGLE = -0.62;

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

  float boost = min(ss.z, ts.z);
  float faded = max(ss.y, ts.y);
  float match = min(ss.x, ts.x);
  float alpha = match * mix(1.0, 0.16, faded) * max(uEdgeAlpha, boost);
  if (alpha < 0.008) {
    gl_Position = vec4(3.0, 3.0, 3.0, 1.0);
    return;
  }

  vec2 p0 = worldToPx(sa.x, sa.y);
  vec2 p3 = worldToPx(ta.x, ta.y);
  float margin = 40.0 * uDpr;
  if ((p0.x < -margin && p3.x < -margin) || (p0.x > uRes.x + margin && p3.x > uRes.x + margin) ||
      (p0.y < -margin && p3.y < -margin) || (p0.y > uRes.y + margin && p3.y > uRes.y + margin)) {
    gl_Position = vec4(3.0, 3.0, 3.0, 1.0);
    return;
  }

  float seed = hash(float(gl_InstanceID) * 1.37 + 0.5);
  vec2 chord = p3 - p0;
  float len = length(chord) + 1.0;
  // A hand reaches forward along time, then settles into the next mark.
  // Steep links curve as one gentle arc, so short jumps do not read as hooks.
  float handle = abs(chord.x) * 0.46 + 3.0 * uDpr;
  float steep = smoothstep(0.6, 2.2, abs(chord.y) / (abs(chord.x) + 1.0));
  vec2 bow = vec2(-chord.y, chord.x) / len * len * mix(0.04, 0.13, steep) * (seed < 0.5 ? -1.0 : 1.0) * (0.6 + 0.4 * seed);
  vec2 p1 = p0 + vec2(handle, chord.y * mix(0.1, 0.33, steep)) + bow;
  vec2 p2 = p3 - vec2(handle, chord.y * mix(0.1, 0.33, steep)) + bow;

  float t = aVert.x;
  float it = 1.0 - t;
  vec2 pos = it * it * it * p0 + 3.0 * it * it * t * p1 + 3.0 * it * t * t * p2 + t * t * t * p3;
  vec2 tangent = 3.0 * it * it * (p1 - p0) + 6.0 * it * t * (p2 - p1) + 3.0 * t * t * (p3 - p2);
  float angle = atan(tangent.y, tangent.x);
  vec2 normal = vec2(-sin(angle), cos(angle));

  float along = t * len / uDpr;
  // Keeps the ends pinned to their marks while the middle wavers slightly.
  float pin = smoothstep(0.0, 0.12, t) * smoothstep(1.0, 0.88, t);
  pos += normal * pin * uDpr * (wander(along / 70.0 + seed * 91.0) * 1.5 + wander(along / 21.0 + seed * 37.0) * 0.45);

  // A broad nib makes the stroke thick or thin depending on its direction of travel.
  float nib = abs(sin(angle - NIB_ANGLE));
  // Pressure eases off as the stroke runs on, and the pen lifts at the end.
  float pressure = (1.0 - 0.32 * t) * smoothstep(1.0, 0.94, t) * (0.72 + 0.28 * smoothstep(0.0, 0.05, t));
  float base = mix(0.95, 1.8, boost);
  float halfWidth = uDpr * base * (0.28 + 0.72 * nib) * pressure * (1.0 + 0.12 * wander(along / 34.0 + seed * 13.0));
  float expand = halfWidth + 1.1 * uDpr;

  gl_Position = pxToClip(pos + normal * aVert.y * expand);
  vSide = aVert.y * expand;
  vHalf = halfWidth;
  vT = t;
  // In screen terms, the time position lets the opening animation draw strokes left to right.
  vU = mix(timeU(sa.x), timeU(ta.x), t);
  vColorA = mix(${GRAPHITE}, sb.rgb, mix(1.0, 0.2, faded));
  vColorB = mix(${GRAPHITE}, tb.rgb, mix(1.0, 0.2, faded));
  vInfo = vec4(seed, alpha, boost, aTentative);
  vExtra = vec2(len / uDpr, 0.0);
}
`

export const EDGE_FS = HEADER + /* glsl */ `
uniform float uDpr;
uniform float uDrawU;
in float vSide;
in float vT;
in float vU;
in float vHalf;
flat in vec3 vColorA;
flat in vec3 vColorB;
flat in vec4 vInfo;
flat in vec2 vExtra;
out vec4 fragColor;

float hash2(vec2 p) {
  return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void main() {
  if (vU > uDrawU) discard;
  float alpha = vInfo.y;
  float cover = 1.0 - smoothstep(vHalf - 0.55 * uDpr, vHalf + 0.55 * uDpr, abs(vSide));
  float along = vT * vExtra.x;
  if (vInfo.w > 0.5) {
    // Unreviewed links: the pen touching down in short, uneven strokes.
    float jitter = hash2(vec2(floor(along / 8.0), vInfo.x)) * 0.25;
    cover *= step(0.34 + jitter, fract(along / 8.0));
  }
  // Ink thins where the nib runs dry.
  float grain = hash2(floor(gl_FragCoord.xy / uDpr) + vInfo.x * 40.0);
  float ink = cover * alpha * (0.86 + 0.14 * grain);
  vec3 color = mix(vColorA, vColorB, smoothstep(0.15, 0.85, vT));
  // Multiply blending: white leaves the paper untouched, ink darkens what is under it.
  fragColor = vec4(mix(vec3(1.0), color, ink), 1.0);
}
`

export const SPAN_VS = HEADER + WORLD + /* glsl */ `
layout(location = 0) in vec2 aVert;
layout(location = 1) in vec2 aRange;
layout(location = 2) in uint aId;
uniform float uDrawU;
flat out vec3 vColor;
flat out float vAlpha;
out vec2 vLocal;
flat out vec2 vSize;

void main() {
  int id = int(aId);
  ivec2 tc = texel(id);
  vec4 a = texelFetch(uNodeA, tc, 0);
  vec4 b = texelFetch(uNodeB, tc, 0);
  vec4 s = texelFetch(uState, tc, 0);
  float alpha = visible(s, b.a) * mix(1.0, 0.25, s.y);
  float x0 = worldToPx(aRange.x, a.y).x;
  float x1 = worldToPx(aRange.y, a.y).x;
  float y = worldToPx(a.x, a.y).y;
  if (alpha < 0.01 || x1 - x0 < 5.0 * uDpr || x1 < 0.0 || x0 > uRes.x || timeU(aRange.x) > uDrawU) {
    gl_Position = vec4(3.0, 3.0, 3.0, 1.0);
    return;
  }
  float tick = 2.6 * uDpr;
  vec2 p = vec2(mix(x0 - uDpr, x1 + uDpr, aVert.x * 0.5 + 0.5), y + aVert.y * tick);
  gl_Position = pxToClip(p);
  vLocal = vec2(p.x - x0, aVert.y * tick);
  vSize = vec2(x1 - x0, tick);
  vColor = b.rgb;
  vAlpha = alpha;
}
`

export const SPAN_FS = HEADER + /* glsl */ `
uniform float uDpr;
flat in vec3 vColor;
flat in float vAlpha;
in vec2 vLocal;
flat in vec2 vSize;
out vec4 fragColor;

void main() {
  // A thin bar with a small serif at each end, as in Priestley's Chart of Biography.
  float line = 1.0 - smoothstep(0.3 * uDpr, 0.8 * uDpr, abs(vLocal.y));
  float end = min(abs(vLocal.x), abs(vLocal.x - vSize.x));
  float serif = 1.0 - smoothstep(0.35 * uDpr, 0.95 * uDpr, end);
  float ink = max(line * 0.62, serif) * vAlpha;
  fragColor = vec4(mix(vec3(1.0), vColor, ink), 1.0);
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
  vec2 c = worldToPx(a.x, a.y);
  if (w < 0.01 || c.x < -uKernel || c.x > uRes.x + uKernel || c.y < -uKernel || c.y > uRes.y + uKernel) {
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
  float k = (exp(-d * 3.2) - 0.0408);
  fragColor = vec4(vColor * k, k);
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

export const STIPPLE_VS = FULLSCREEN_VS
export const STIPPLE_FS = HEADER + /* glsl */ `
uniform sampler2D uTex;
uniform vec2 uRes;
uniform float uDpr;
uniform float uGain;
uniform float uIntensity;
uniform vec2 uOffset;
in vec2 vUv;
out vec4 fragColor;

vec2 hash22(vec2 p) {
  p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)));
  return fract(sin(p) * 43758.5453);
}

void main() {
  // Density as engraver's stipple: hand-placed dots that grow and crowd where entries do.
  float cell = 5.0 * uDpr;
  vec2 fc = vec2(gl_FragCoord.x, uRes.y - gl_FragCoord.y) + uOffset * uDpr;
  vec2 id = floor(fc / cell);
  float ink = 0.0;
  vec3 color = vec3(0.3, 0.27, 0.24);
  for (int y = -1; y <= 1; y++) {
    for (int x = -1; x <= 1; x++) {
      vec2 c = id + vec2(float(x), float(y));
      vec2 h = hash22(c);
      vec2 center = (c + 0.2 + 0.6 * h) * cell;
      vec2 screen = center - uOffset * uDpr;
      vec2 uv = vec2(screen.x, uRes.y - screen.y) / uRes;
      vec4 s = texture(uTex, uv);
      float amount = 1.0 - exp(-s.a * uGain);
      float keep = step(hash22(c + 7.7).x, amount * 1.5);
      float r = (0.34 + 1.05 * sqrt(amount)) * uDpr * keep;
      float d = length(fc - center);
      float dot_ = 1.0 - smoothstep(r - 0.6 * uDpr, r + 0.6 * uDpr, d);
      if (dot_ > ink) {
        ink = dot_;
        if (s.a > 1e-4) color = s.rgb / s.a;
      }
    }
  }
  fragColor = vec4(mix(vec3(1.0), color, ink * uIntensity * 0.8), 1.0);
}
`

export const RECT_VS = HEADER + /* glsl */ `
layout(location = 0) in vec2 aCorner;
layout(location = 1) in vec4 aRect;
layout(location = 2) in vec4 aColor;
uniform vec2 uRes;
flat out vec4 vColor;
void main() {
  vec2 uv = aCorner * 0.5 + 0.5;
  vec2 p = mix(aRect.xy, aRect.zw, uv);
  vec2 c = p / uRes * 2.0 - 1.0;
  gl_Position = vec4(c.x, -c.y, 0.0, 1.0);
  vColor = aColor;
}
`

export const RECT_FS = HEADER + /* glsl */ `
flat in vec4 vColor;
out vec4 fragColor;
void main() {
  fragColor = vec4(vColor.rgb * vColor.a, vColor.a);
}
`

export const PAPER_VS = FULLSCREEN_VS
export const PAPER_FS = HEADER + /* glsl */ `
uniform vec3 uPaper;
uniform float uDpr;
in vec2 vUv;
out vec4 fragColor;

float hash(vec2 p) {
  return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}
float noise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y);
}
void main() {
  vec2 p = gl_FragCoord.xy / uDpr;
  // Paper is barely textured: long horizontal fibres and fine tooth, near the threshold of notice.
  float fibre = noise(p * vec2(0.09, 0.22)) * 0.5 + noise(p * vec2(0.37, 0.61)) * 0.3;
  float tooth = noise(p * 1.1) * 0.2;
  float shade = (fibre + tooth - 0.5) * 0.009;
  fragColor = vec4(uPaper + shade, 1.0);
}
`

export const COPY_VS = FULLSCREEN_VS
export const COPY_FS = HEADER + /* glsl */ `
uniform sampler2D uTex;
in vec2 vUv;
out vec4 fragColor;
void main() {
  fragColor = texture(uTex, vUv);
}
`
