import { MAX_FOLD_POINTS } from './folds.ts'
import { LUT_SIZE } from './time.ts'

/** GLSL for the chart: flat ink on paper. Lines multiply onto the page, as real ink does. */
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
uniform sampler2D uTimeLut;
uniform vec2 uFold[${MAX_FOLD_POINTS}];
uniform int uFoldCount;

// Bends axis position to display position, so a period can be opened and the rest pleated.
float foldV(float u) {
  if (uFoldCount < 2) return u;
  int lo = 0;
  int hi = uFoldCount - 1;
  if (u <= uFold[0].x) return uFold[0].y + (u - uFold[0].x);
  if (u >= uFold[hi].x) return uFold[hi].y + (u - uFold[hi].x);
  for (int k = 0; k < 8 && hi - lo > 1; k++) {
    int m = (lo + hi) / 2;
    if (uFold[m].x <= u) lo = m;
    else hi = m;
  }
  float s = uFold[hi].x - uFold[lo].x;
  return s > 0.0 ? mix(uFold[lo].y, uFold[hi].y, (u - uFold[lo].x) / s) : uFold[lo].y;
}

float timeU(float t) {
  float lin = (t - uTimeScale.x) / (uTimeScale.y - uTimeScale.x);
  float position = clamp(log(1.0 + (uTimeScale.y - t) / uTimeScale.z) / uTimeScale.w, 0.0, 1.0);
  float f = position * ${LUT_SIZE - 1}.0;
  int i = min(int(f), ${LUT_SIZE - 2});
  float compressed = mix(texelFetch(uTimeLut, ivec2(i, 0), 0).r, texelFetch(uTimeLut, ivec2(i + 1, 0), 0).r, f - float(i));
  return mix(lin, compressed, uWarp);
}
vec2 worldToPx(float t, float y) {
  return vec2((foldV(timeU(t)) - uCam.x) * uScale.x + uCenter.x, (y - uCam.y) * uScale.y + uCenter.y);
}
vec4 pxToClip(vec2 p) {
  vec2 c = p / uRes * 2.0 - 1.0;
  return vec4(c.x, -c.y, 0.0, 1.0);
}
ivec2 texel(int id) {
  return ivec2(id % ${TEX_WIDTH}, id / ${TEX_WIDTH});
}
`

/** The grey the page falls back to when something is faded. */
const GRAPHITE = 'vec3(0.56, 0.53, 0.49)'

export const NODE_VS = HEADER + WORLD + /* glsl */ `
layout(location = 0) in vec2 aCorner;
uniform float uNodeAlpha;
uniform int uHover;
uniform int uSelected;
uniform float uMarkCap;
uniform float uTail;
flat out vec3 vColor;
flat out vec3 vInfo;
flat out float vTail;
flat out float vMark;
out vec2 vPx;

void main() {
  int id = gl_InstanceID;
  ivec2 tc = texel(id);
  vec4 a = texelFetch(uNodeA, tc, 0);
  vec4 b = texelFetch(uNodeB, tc, 0);
  // state: x = passes filters, y = faded, z = emphasised
  vec4 s = texelFetch(uState, tc, 0);
  float mark = id == uSelected ? 1.0 : (id == uHover ? 0.7 : 0.0);
  float alpha = max(s.x * mix(1.0, 0.3, s.y) * uNodeAlpha, mark);
  if (alpha < 0.01) {
    gl_Position = vec4(3.0, 3.0, 3.0, 1.0);
    return;
  }
  float r = min(a.z, uMarkCap) * uDpr * (1.0 + 0.2 * s.z);
  float bound = floor(mod(a.w, 8.0) / 2.0);
  float halfSize = r * 1.6 + (bound > 0.5 ? 9.0 : 2.0) * uDpr + mark * 7.0 * uDpr;
  vec2 c = worldToPx(a.x, a.y);
  if (c.x < -halfSize || c.x > uRes.x + halfSize || c.y < -halfSize || c.y > uRes.y + halfSize) {
    gl_Position = vec4(3.0, 3.0, 3.0, 1.0);
    return;
  }
  vPx = aCorner * halfSize;
  gl_Position = pxToClip(c + vPx);
  vColor = mix(${GRAPHITE}, b.rgb, mix(1.0, 0.25, s.y));
  vInfo = vec3(a.w, r, alpha);
  vMark = mark;
  vTail = max(uTail, s.z);
}
`

export const NODE_FS = HEADER + /* glsl */ `
uniform float uDpr;
uniform vec3 uPaper;
flat in vec3 vColor;
flat in vec3 vInfo;
flat in float vMark;
flat in float vTail;
in vec2 vPx;
out vec4 fragColor;

void main() {
  float kind = mod(vInfo.x, 2.0);
  float bound = floor(mod(vInfo.x, 8.0) / 2.0);
  float strength = floor(vInfo.x / 8.0);
  float r = vInfo.y;
  float aa = 0.7 * uDpr;
  float line = 1.4 * uDpr;
  vec2 p = abs(vPx);
  float square = max(p.x, p.y);
  float circle = length(vPx);

  // Every mark carries a paper centre or none, so lines stop cleanly at its edge.
  float edge;
  float open = 1.0;
  float gap = 1.0;
  if (strength > 1.5) {
    // An awareness proxy: a hollow diamond, never an ordinary mark of use.
    edge = (p.x + p.y) / 1.3;
  } else if (strength > 0.5) {
    // A scoped inference: a square drawn only at its corners.
    edge = square;
    gap = smoothstep(r * 0.25, r * 0.4, min(p.x, p.y));
  } else if (kind < 0.5) {
    // Technology: a solid square of ink.
    edge = square;
    open = 0.0;
  } else {
    // Science: an open circle.
    edge = circle;
  }

  float outer = 1.0 - smoothstep(r - aa, r + aa, edge);
  float inner = 1.0 - smoothstep(r - line - aa, r - line + aa, edge);
  vec3 rgb = mix(vColor, uPaper, max(inner * open, (1.0 - gap)));
  float a = outer;

  if (bound > 0.5 && vTail > 0.01) {
    // A short tail says the date is a limit on one side only. It is not a span of time.
    float along = vPx.x * (bound < 1.5 ? -1.0 : 1.0);
    float tail = (1.0 - smoothstep(0.35 * uDpr, 0.95 * uDpr, abs(vPx.y))) * step(r, along) * step(along, r + 7.0 * uDpr);
    rgb = mix(rgb, vColor, tail * (1.0 - a));
    a = max(a, tail * 0.8 * vTail);
  }

  if (vMark > 0.0) {
    float ring = 1.0 - smoothstep(0.5 * uDpr, 1.2 * uDpr, abs(max(square, circle * 0.86) - (r + 4.5 * uDpr)));
    rgb = mix(rgb, vec3(0.12, 0.105, 0.086), ring * (1.0 - a));
    a = max(a, ring * vMark);
  }
  fragColor = vec4(rgb * a, a) * vInfo.z;
}
`

export const EDGE_VS = HEADER + WORLD + /* glsl */ `
layout(location = 0) in vec2 aVert;
layout(location = 1) in uvec2 aEdge;
layout(location = 2) in float aTentative;
uniform float uEdgeAlpha;
uniform float uStrokeScale;
// 0 draws a line along the parent's row that turns late into the child's.
// uWeave straightens it to a stitch falling from the parent's rule.
// uElbow turns it to a corner that drops from the parent and runs along to the child.
uniform float uWeave;
uniform float uElbow;
out float vSide;
out float vT;
flat out vec3 vColorA;
flat out vec3 vColorB;
flat out vec3 vInfo;
flat out float vLength;
out float vHalf;

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
  float alpha = min(ss.x, ts.x) * mix(1.0, 0.16, faded) * max(uEdgeAlpha, boost);
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

  vec2 chord = p3 - p0;
  float len = length(chord) + 1.0;
  // Keeps to the parent's row for most of the way, as a line on a transit map does.
  float reach = sign(chord.x + 0.001) * max(abs(chord.x), abs(chord.y) * 0.3);
  vec2 p1 = p0 + vec2(reach * 0.72, 0.0);
  vec2 p2 = p3 - vec2(reach * 0.18, 0.0);
  if (uElbow > 0.0) {
    p1 = mix(p1, p0 + vec2(0.0, chord.y * 0.86), uElbow);
    p2 = mix(p2, vec2(p0.x + chord.x * 0.14, p3.y), uElbow);
  }
  if (uWeave > 0.0) {
    vec2 q0 = vec2(p3.x, p0.y);
    p0 = mix(p0, q0, uWeave);
    p1 = mix(p1, mix(q0, p3, 0.33), uWeave);
    p2 = mix(p2, mix(q0, p3, 0.67), uWeave);
  }

  float t = aVert.x;
  float it = 1.0 - t;
  vec2 pos = it * it * it * p0 + 3.0 * it * it * t * p1 + 3.0 * it * t * t * p2 + t * t * t * p3;
  vec2 tangent = 3.0 * it * it * (p1 - p0) + 6.0 * it * t * (p2 - p1) + 3.0 * t * t * (p3 - p2);
  vec2 normal = normalize(vec2(-tangent.y, tangent.x) + vec2(0.0, 0.0001));

  float halfWidth = uDpr * mix(0.8, 1.35, boost) * uStrokeScale;
  float expand = halfWidth + 1.1 * uDpr;
  gl_Position = pxToClip(pos + normal * aVert.y * expand);
  vSide = aVert.y * expand;
  vHalf = halfWidth;
  vT = t;
  vColorA = mix(${GRAPHITE}, sb.rgb, mix(1.0, 0.2, faded));
  vColorB = mix(${GRAPHITE}, tb.rgb, mix(1.0, 0.2, faded));
  vInfo = vec3(alpha, boost, aTentative);
  vLength = len / uDpr;
}
`

export const EDGE_FS = HEADER + /* glsl */ `
uniform float uDpr;
in float vSide;
in float vT;
in float vHalf;
flat in vec3 vColorA;
flat in vec3 vColorB;
flat in vec3 vInfo;
flat in float vLength;
out vec4 fragColor;

void main() {
  float cover = 1.0 - smoothstep(vHalf - 0.55 * uDpr, vHalf + 0.55 * uDpr, abs(vSide));
  // A link still awaiting review is drawn broken.
  if (vInfo.z > 0.5) cover *= step(0.4, fract(vT * vLength / 7.0));
  vec3 color = mix(vColorA, vColorB, smoothstep(0.15, 0.85, vT));
  // Multiply blending: white leaves the paper untouched, ink darkens what is under it.
  fragColor = vec4(mix(vec3(1.0), color, cover * vInfo.x), 1.0);
}
`

export const SPAN_VS = HEADER + WORLD + /* glsl */ `
layout(location = 0) in vec2 aVert;
layout(location = 1) in vec2 aRange;
layout(location = 2) in uint aId;
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
  float alpha = s.x * mix(1.0, 0.25, s.y);
  float x0 = worldToPx(aRange.x, a.y).x;
  float x1 = worldToPx(aRange.y, a.y).x;
  float y = worldToPx(a.x, a.y).y;
  if (alpha < 0.01 || x1 - x0 < 5.0 * uDpr || x1 < 0.0 || x0 > uRes.x) {
    gl_Position = vec4(3.0, 3.0, 3.0, 1.0);
    return;
  }
  float tick = 3.5 * uDpr;
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
  // A bar with an end stop at each side, for a date known only as a range.
  float line = 1.0 - smoothstep(0.6 * uDpr, 1.1 * uDpr, abs(vLocal.y));
  float end = min(abs(vLocal.x), abs(vLocal.x - vSize.x));
  float stop = 1.0 - smoothstep(0.4 * uDpr, 1.0 * uDpr, end);
  float ink = max(line * 0.55, stop) * vAlpha;
  fragColor = vec4(mix(vec3(1.0), vColor, ink), 1.0);
}
`

/** One rule per stretch of an entry's reach or documented life. */
export const WARP_VS = HEADER + WORLD + /* glsl */ `
layout(location = 0) in vec2 aVert;
layout(location = 1) in vec2 aRange;
layout(location = 2) in uint aId;
layout(location = 3) in float aStyle;
uniform float uWarpAlpha;
flat out vec3 vColor;
flat out float vAlpha;
flat out float vStyle;
flat out float vHalf;
out float vSide;
out float vAlong;

void main() {
  int id = int(aId);
  ivec2 tc = texel(id);
  vec4 a = texelFetch(uNodeA, tc, 0);
  vec4 b = texelFetch(uNodeB, tc, 0);
  vec4 s = texelFetch(uState, tc, 0);
  float alpha = s.x * mix(1.0, 0.22, s.y) * uWarpAlpha;
  float x0 = worldToPx(aRange.x, a.y).x;
  float x1 = worldToPx(aRange.y, a.y).x;
  float y = worldToPx(a.x, a.y).y;
  if (alpha < 0.01 || x1 < 0.0 || x0 > uRes.x) {
    gl_Position = vec4(3.0, 3.0, 3.0, 1.0);
    return;
  }
  // Style 0: built on directly. 1: only through later entries. 2: through unreviewed links.
  // Style 3: the documented life, in a heavier, darker stroke that nothing else uses.
  float half_ = (aStyle > 2.5 ? 1.5 : aStyle < 0.5 ? 0.62 : 0.36) * uDpr * (1.0 + 0.35 * s.z);
  float expand = half_ + 1.0 * uDpr;
  float px = mix(x0, x1, aVert.x * 0.5 + 0.5);
  gl_Position = pxToClip(vec2(px, y + aVert.y * expand));
  vSide = aVert.y * expand;
  vHalf = half_;
  vAlong = (px - x0) / uDpr;
  vStyle = aStyle;
  vColor = aStyle > 2.5 ? vec3(0.12, 0.105, 0.086) : mix(${GRAPHITE}, b.rgb, 0.78);
  vAlpha = alpha;
}
`

export const WARP_FS = HEADER + /* glsl */ `
uniform float uDpr;
flat in vec3 vColor;
flat in float vAlpha;
flat in float vStyle;
flat in float vHalf;
in float vSide;
in float vAlong;
out vec4 fragColor;

void main() {
  float cover = 1.0 - smoothstep(vHalf - 0.5 * uDpr, vHalf + 0.5 * uDpr, abs(vSide));
  if (vStyle > 1.5 && vStyle < 2.5) cover *= step(0.42, fract(vAlong / 6.0));
  fragColor = vec4(mix(vec3(1.0), vColor, cover * vAlpha), 1.0);
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
