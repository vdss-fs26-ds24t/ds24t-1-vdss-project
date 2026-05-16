"""Rotating globe component rendered in a Streamlit HTML iframe."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import streamlit.components.v1 as components

logger = logging.getLogger(__name__)

_GLOBE_PALETTE: dict[str, str] = {
    "warm": "#c0622a",
    "cool": "#3a7fa8",
    "globeHi": "#f8f3e6",
    "globeMid": "#ebe0c8",
    "globeLo": "#c9b890",
    "globeStroke": "#a89770",
    "graticule": "#8a7c5a",
    "land": "#a89770",
    "bern": "#c0622a",
}

_LAND_PATH = Path(__file__).resolve().parent.parent / "assets" / "land_110m.json"

_LAND_POLYGONS_FALLBACK: list[list[list[float]]] = [
    [
        [72, -168], [55, -168], [45, -130], [50, -110], [40, -100], [25, -100],
        [15, -90], [20, -75], [35, -70], [50, -60], [60, -60], [72, -80],
        [72, -168],
    ],
    [
        [12, -82], [5, -75], [-5, -70], [-20, -65], [-40, -65], [-55, -70],
        [-55, -50], [-35, -40], [-10, -45], [5, -60], [12, -70], [12, -82],
    ],
    [
        [72, -10], [60, -10], [50, -5], [40, 10], [36, 20], [40, 30],
        [50, 30], [60, 20], [70, 30], [72, 10], [72, -10],
    ],
    [
        [75, 30], [70, 60], [60, 90], [55, 110], [50, 130], [40, 150],
        [30, 160], [20, 130], [10, 110], [5, 80], [10, 60], [20, 50],
        [30, 40], [45, 40], [60, 30], [75, 30],
    ],
    [
        [35, -17], [30, 0], [25, 10], [20, 20], [10, 30], [0, 35],
        [-10, 40], [-20, 35], [-35, 20], [-35, 0], [-25, -10],
        [-10, -15], [10, -10], [20, -5], [35, -17],
    ],
    [
        [-10, 113], [-10, 153], [-25, 153], [-38, 146], [-44, 113],
        [-25, 113], [-10, 113],
    ],
    [
        [-60, -180], [-85, -180], [-85, 180], [-60, 180], [-60, -180],
    ],
]


def _load_land_polygons() -> list[list[list[float]]]:
    if not _LAND_PATH.exists():
        logger.warning("Land outline file not found at %s", _LAND_PATH)
        return _LAND_POLYGONS_FALLBACK

    try:
        return json.loads(_LAND_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Failed to read land outlines: %s", exc)
        return _LAND_POLYGONS_FALLBACK


_LAND_POLYGONS = _load_land_polygons()

_GLOBE_HTML_TEMPLATE = """<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    html, body { margin: 0; padding: 0; background: transparent; }
    #globe-wrap {
      width: 100%;
      height: __HEIGHT__px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    canvas { display: block; }
  </style>
</head>
<body>
  <div id="globe-wrap">
    <canvas id="globe-canvas"></canvas>
  </div>
  <script>
    const routes = __ROUTES__;
    const land = __LAND__;
    const palette = __PALETTE__;

    const container = document.getElementById("globe-wrap");
    const canvas = document.getElementById("globe-canvas");
    const ctx = canvas.getContext("2d");

    const state = {
      size: 520,
      r: 220,
      cx: 260,
      cy: 260,
      rot: 15,
      tickStart: performance.now(),
    };

    const prefersReduced = window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const hexToRgb = (hex) => {
      const val = hex.replace("#", "");
      return {
        r: parseInt(val.slice(0, 2), 16),
        g: parseInt(val.slice(2, 4), 16),
        b: parseInt(val.slice(4, 6), 16),
      };
    };

    const lerp = (a, b, t) => a + (b - a) * t;

    const mixColor = (a, b, t) => {
      const ca = hexToRgb(a);
      const cb = hexToRgb(b);
      const r = Math.round(lerp(ca.r, cb.r, t));
      const g = Math.round(lerp(ca.g, cb.g, t));
      const bch = Math.round(lerp(ca.b, cb.b, t));
      return `rgb(${r}, ${g}, ${bch})`;
    };

    const co2Max = Math.max(...routes.map(r => r.co2), 1);
    const colorFor = (co2) => mixColor(palette.cool, palette.warm, Math.min(1, co2 / co2Max));

    const buildGraticule = () => {
      const lines = [];
      for (let lat = -60; lat <= 60; lat += 30) {
        const line = [];
        for (let lon = -180; lon <= 180; lon += 4) {
          line.push([lat, lon]);
        }
        lines.push(line);
      }
      for (let lon = -180; lon <= 180; lon += 30) {
        const line = [];
        for (let lat = -85; lat <= 85; lat += 4) {
          line.push([lat, lon]);
        }
        lines.push(line);
      }
      return lines;
    };

    const graticule = buildGraticule();

    // Orthographic projection from lat/lon to screen.
    const project = (lat, lon) => {
      const phi = (lat * Math.PI) / 180;
      const lambda = ((lon - state.rot) * Math.PI) / 180;
      const x = Math.cos(phi) * Math.sin(lambda);
      const y = Math.sin(phi);
      const z = Math.cos(phi) * Math.cos(lambda);
      return { x: state.cx + x * state.r, y: state.cy - y * state.r, z };
    };

    const arcPoints = (from, to, segments) => {
      const pts = [];
      const lat1 = (from[0] * Math.PI) / 180;
      const lon1 = (from[1] * Math.PI) / 180;
      const lat2 = (to[0] * Math.PI) / 180;
      const lon2 = (to[1] * Math.PI) / 180;
      const d = 2 * Math.asin(Math.sqrt(
        Math.sin((lat2 - lat1) / 2) ** 2 +
        Math.cos(lat1) * Math.cos(lat2) * Math.sin((lon2 - lon1) / 2) ** 2
      ));
      for (let i = 0; i <= segments; i++) {
        const f = i / segments;
        const A = Math.sin((1 - f) * d) / Math.sin(d);
        const B = Math.sin(f * d) / Math.sin(d);
        const x = A * Math.cos(lat1) * Math.cos(lon1) + B * Math.cos(lat2) * Math.cos(lon2);
        const y = A * Math.cos(lat1) * Math.sin(lon1) + B * Math.cos(lat2) * Math.sin(lon2);
        const z = A * Math.sin(lat1) + B * Math.sin(lat2);
        const lat = Math.atan2(z, Math.sqrt(x * x + y * y)) * 180 / Math.PI;
        const lon = Math.atan2(y, x) * 180 / Math.PI;
        pts.push([lat, lon]);
      }
      return pts;
    };

    const arcs = routes.map((r) => ({
      id: r.id,
      co2: r.co2,
      pts: arcPoints(r.from, r.to, 56),
    }));

    const resize = () => {
      const rect = container.getBoundingClientRect();
      const size = Math.max(1, Math.min(rect.width, rect.height));
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.max(1, Math.floor(size * dpr));
      canvas.height = Math.max(1, Math.floor(size * dpr));
      canvas.style.width = `${size}px`;
      canvas.style.height = `${size}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      state.size = size;
      state.r = size * 0.423;
      state.cx = size / 2;
      state.cy = size / 2;
    };

    const observer = new ResizeObserver(resize);
    observer.observe(container);
    resize();

    const drawSphere = () => {
      const grad = ctx.createRadialGradient(
        state.cx - state.r * 0.2,
        state.cy - state.r * 0.15,
        state.r * 0.2,
        state.cx,
        state.cy,
        state.r
      );
      grad.addColorStop(0, palette.globeHi);
      grad.addColorStop(0.7, palette.globeMid);
      grad.addColorStop(1, palette.globeLo);
      ctx.beginPath();
      ctx.arc(state.cx, state.cy, state.r, 0, Math.PI * 2);
      ctx.fillStyle = grad;
      ctx.fill();
      ctx.lineWidth = 0.6;
      ctx.strokeStyle = palette.globeStroke;
      ctx.stroke();
    };

    const drawGraticule = () => {
      ctx.save();
      ctx.strokeStyle = palette.graticule;
      ctx.lineWidth = 0.5;
      ctx.globalAlpha = 0.55;
      graticule.forEach((line) => {
        let started = false;
        ctx.beginPath();
        line.forEach(([lat, lon]) => {
          const p = project(lat, lon);
          if (p.z > -0.05) {
            if (!started) {
              ctx.moveTo(p.x, p.y);
              started = true;
            } else {
              ctx.lineTo(p.x, p.y);
            }
          } else {
            started = false;
          }
        });
        ctx.stroke();
      });
      ctx.restore();
    };

    const landPolygons = land || [];

    const drawLand = () => {
      if (!landPolygons.length) return;
      ctx.save();
      ctx.strokeStyle = palette.land;
      ctx.lineWidth = 0.7;
      ctx.globalAlpha = 0.55;
      landPolygons.forEach((poly) => {
        let started = false;
        ctx.beginPath();
        poly.forEach(([lat, lon]) => {
          const p = project(lat, lon);
          if (p.z > -0.05) {
            if (!started) {
              ctx.moveTo(p.x, p.y);
              started = true;
            } else {
              ctx.lineTo(p.x, p.y);
            }
          } else if (started) {
            ctx.stroke();
            ctx.beginPath();
            started = false;
          }
        });
        if (started) {
          ctx.stroke();
        }
      });
      ctx.restore();
    };

    const drawBern = () => {
      const p = project(46.95, 7.45);
      if (p.z <= -0.05) return;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 3.5, 0, Math.PI * 2);
      ctx.fillStyle = palette.bern;
      ctx.fill();
      ctx.beginPath();
      ctx.arc(p.x, p.y, 8, 0, Math.PI * 2);
      ctx.strokeStyle = palette.bern;
      ctx.globalAlpha = 0.35;
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.globalAlpha = 1;
    };

    const drawArcs = (tick) => {
      const total = Math.max(1, arcs.length);
      arcs.forEach((arc, i) => {
        const stagger = (i / total) * 0.6;
        const localT = Math.max(0, Math.min(1, (tick - stagger) / 0.4));
        if (localT <= 0) return;

        const visibleCount = Math.max(1, Math.floor(arc.pts.length * localT));
        const color = colorFor(arc.co2);
        const weight = 0.6 + (arc.co2 / co2Max) * 1.8;
        let started = false;

        ctx.save();
        ctx.shadowBlur = 4;
        ctx.shadowColor = color;
        ctx.strokeStyle = color;
        ctx.lineWidth = weight;
        ctx.lineCap = "round";
        ctx.beginPath();

        for (let k = 0; k < visibleCount; k++) {
          const [lat, lon] = arc.pts[k];
          const p = project(lat, lon);
          const f0 = k / arc.pts.length;
          const bow = Math.sin(f0 * Math.PI) * state.r * 0.12;
          const dx = p.x - state.cx;
          const dy = p.y - state.cy;
          const len = Math.hypot(dx, dy) || 1;
          const x = p.x + (dx / len) * bow;
          const y = p.y + (dy / len) * bow;

          if (p.z > -0.4) {
            if (!started) {
              ctx.moveTo(x, y);
              started = true;
            } else {
              ctx.lineTo(x, y);
            }
          } else {
            started = false;
          }
        }
        ctx.stroke();
        ctx.restore();

        const last = arc.pts[Math.min(visibleCount - 1, arc.pts.length - 1)];
        if (!last) return;
        const lastP = project(last[0], last[1]);
        if (lastP.z <= -0.05) return;
        ctx.beginPath();
        ctx.arc(lastP.x, lastP.y, localT < 1 ? 2.6 : 2, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
      });
    };

    const draw = (now) => {
      if (!prefersReduced) {
        state.rot = (state.rot + 0.12) % 360;
      }
      const tick = ((now - state.tickStart) / 6000) % 1;
      ctx.clearRect(0, 0, state.size, state.size);
      drawSphere();
      drawGraticule();
      drawLand();
      drawBern();
      if (arcs.length) {
        drawArcs(tick);
      }
      requestAnimationFrame(draw);
    };

    requestAnimationFrame(draw);
  </script>
</body>
</html>
"""


def render_globe(routes: list[dict[str, Any]], height: int = 520) -> None:
    """Render a rotating globe with flight arcs.

    Args:
        routes: List of routes with from/to coords and CO2 values.
        height: Height of the component in pixels.
    """
    routes_json = json.dumps(routes or [], ensure_ascii=True)
    land_json = json.dumps(_LAND_POLYGONS, ensure_ascii=True)
    palette_json = json.dumps(_GLOBE_PALETTE, ensure_ascii=True)
    html = (
        _GLOBE_HTML_TEMPLATE
        .replace("__ROUTES__", routes_json)
        .replace("__LAND__", land_json)
        .replace("__PALETTE__", palette_json)
        .replace("__HEIGHT__", str(height))
    )
    components.html(html, height=height, scrolling=False)
