/**
 * Zambretti & Sager Weather Card  v1.9.72
 * Lovelace custom card for Home Assistant
 *
 * Displays Zambretti & Sager pressure-based weather forecasts as an iOS-style
 * card with animated weather icons, precipitation gauge, forecast timeline,
 * and 24h pressure/precipitation history chart.
 */

import {
  getLabels,
  getPrecipLabel,
  getEditorStrings,
  LANG_OPTIONS,
} from "./zambretti-card-i18n.js";

// ── Condition map ─────────────────────────────────────────────────────────
/** Maps Zambretti state keys to generic weather condition strings used for icon routing and theming. */
const ZAMBRETTI_CONDITION = {
  settled_fine:"sunny", fine_weather:"sunny",
  fine_becoming_less_settled:"partlycloudy", fairly_fine_showery_later:"partlycloudy",
  showery_becoming_more_unsettled:"rainy", unsettled_rain_later:"cloudy",
  rain_at_times_worse_later:"rainy", rain_at_times_becoming_very_unsettled:"pouring",
  very_unsettled_rain:"pouring", fine_possibly_showers:"partlycloudy",
  fairly_fine_showers_likely:"partlycloudy", showery_bright_intervals:"rainy",
  changeable_some_rain:"cloudy", unsettled_rain_at_times:"rainy",
  rain_at_frequent_intervals:"pouring", stormy_much_rain:"lightning-rainy",
  becoming_fine:"partlycloudy", fairly_fine_improving:"partlycloudy",
  fairly_fine_possibly_showers_early:"partlycloudy", showery_early_improving:"rainy",
  changeable_mending:"cloudy", rather_unsettled_clearing_later:"cloudy",
  unsettled_probably_improving:"cloudy", unsettled_short_fine_intervals:"cloudy",
  very_unsettled_finer_at_times:"pouring", stormy_possibly_improving:"lightning-rainy",
  stable:"partlycloudy",
};

// ── SVG weather icons ─────────────────────────────────────────────────────
// FIX: sun — all rays + disc wrapped in ONE <g> with ONE animateTransform
// so disc and rays rotate together without jitter.
/** Inline animated SVG icons keyed by weather condition string. */
const WEATHER_ICONS = {

  sunny:`<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
    <g>
      <animateTransform attributeName="transform" type="rotate"
        from="0 32 32" to="360 32 32" dur="20s"
        repeatCount="indefinite" calcMode="linear"/>
      <circle cx="32" cy="32" r="12" fill="#FFD700"/>
      <g stroke="#FFD700" stroke-width="2.5" stroke-linecap="round">
        <line x1="32" y1="6"  x2="32" y2="13"/>
        <line x1="32" y1="51" x2="32" y2="58"/>
        <line x1="6"  y1="32" x2="13" y2="32"/>
        <line x1="51" y1="32" x2="58" y2="32"/>
        <line x1="13.8" y1="13.8" x2="18.9" y2="18.9"/>
        <line x1="45.1" y1="45.1" x2="50.2" y2="50.2"/>
        <line x1="50.2" y1="13.8" x2="45.1" y2="18.9"/>
        <line x1="18.9" y1="45.1" x2="13.8" y2="50.2"/>
      </g>
    </g>
  </svg>`,

  night_clear:`<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
    <path d="M38 10a22 22 0 1 1-22 24 16 16 0 0 0 22-24z" fill="#E8E8C8"/>
    <circle cx="44" cy="16" r="1.8" fill="#FFF" opacity="0.5">
      <animate attributeName="opacity" values="0.3;0.8;0.3" dur="2.8s" repeatCount="indefinite"/>
    </circle>
    <circle cx="14" cy="12" r="1.2" fill="#FFF" opacity="0.4">
      <animate attributeName="opacity" values="0.2;0.6;0.2" dur="3.5s" repeatCount="indefinite"/>
    </circle>
    <circle cx="52" cy="8"  r="1.0" fill="#FFF" opacity="0.35">
      <animate attributeName="opacity" values="0.2;0.7;0.2" dur="2.2s" repeatCount="indefinite"/>
    </circle>
    <circle cx="10" cy="46" r="1.4" fill="#FFF" opacity="0.3">
      <animate attributeName="opacity" values="0.15;0.55;0.15" dur="4.0s" repeatCount="indefinite"/>
    </circle>
    <circle cx="54" cy="42" r="0.9" fill="#FFF" opacity="0.3">
      <animate attributeName="opacity" values="0.15;0.5;0.15" dur="3.1s" repeatCount="indefinite"/>
    </circle>
  </svg>`,

  partlycloudy:`<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
    <g>
      <animateTransform attributeName="transform" type="rotate"
        from="0 22 26" to="360 22 26" dur="24s"
        repeatCount="indefinite" calcMode="linear"/>
      <circle cx="22" cy="26" r="9" fill="#FFD700" opacity="0.95"/>
    </g>
    <g>
      <animateTransform attributeName="transform" type="translate"
        values="0,0;4,0;0,0" dur="9s" repeatCount="indefinite" calcMode="linear"/>
      <ellipse cx="36" cy="36" rx="16" ry="10" fill="#B0BEC5"/>
      <ellipse cx="26" cy="34" rx="12" ry="9"  fill="#CFD8DC"/>
      <ellipse cx="44" cy="37" rx="10" ry="7"  fill="#B0BEC5"/>
    </g>
  </svg>`,

  cloudy:`<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
    <g>
      <animateTransform attributeName="transform" type="translate"
        values="-5,0;5,0;-5,0" dur="12s" repeatCount="indefinite" calcMode="linear"/>
      <ellipse cx="32" cy="30" rx="20" ry="12" fill="#90A4AE"/>
      <ellipse cx="22" cy="34" rx="14" ry="10" fill="#B0BEC5"/>
      <ellipse cx="44" cy="35" rx="13" ry="9"  fill="#90A4AE"/>
    </g>
  </svg>`,

  rainy:`<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
    <g>
      <animateTransform attributeName="transform" type="translate"
        values="-3,0;3,0;-3,0" dur="8s" repeatCount="indefinite" calcMode="linear"/>
      <ellipse cx="32" cy="24" rx="18" ry="11" fill="#78909C"/>
      <ellipse cx="22" cy="28" rx="13" ry="9"  fill="#90A4AE"/>
      <ellipse cx="42" cy="28" rx="12" ry="8"  fill="#78909C"/>
    </g>
    <g fill="#64B5F6">
      <line x1="22" y1="38" x2="20" y2="50" stroke="#64B5F6" stroke-width="2" stroke-linecap="round">
        <animate attributeName="y1" values="38;40;38" dur="1.2s" repeatCount="indefinite"/>
        <animate attributeName="y2" values="50;52;50" dur="1.2s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="1;0;1" dur="1.2s" repeatCount="indefinite"/>
      </line>
      <line x1="32" y1="36" x2="30" y2="48" stroke="#64B5F6" stroke-width="2" stroke-linecap="round">
        <animate attributeName="y1" values="36;38;36" dur="1.4s" begin="0.3s" repeatCount="indefinite"/>
        <animate attributeName="y2" values="48;50;48" dur="1.4s" begin="0.3s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="1;0;1" dur="1.4s" begin="0.3s" repeatCount="indefinite"/>
      </line>
      <line x1="42" y1="38" x2="40" y2="50" stroke="#64B5F6" stroke-width="2" stroke-linecap="round">
        <animate attributeName="y1" values="38;40;38" dur="1.1s" begin="0.6s" repeatCount="indefinite"/>
        <animate attributeName="y2" values="50;52;50" dur="1.1s" begin="0.6s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="1;0;1" dur="1.1s" begin="0.6s" repeatCount="indefinite"/>
      </line>
    </g>
  </svg>`,

  pouring:`<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
    <g>
      <animateTransform attributeName="transform" type="translate"
        values="-2,0;3,0;-2,0" dur="7s" repeatCount="indefinite" calcMode="linear"/>
      <ellipse cx="32" cy="22" rx="18" ry="11" fill="#546E7A"/>
      <ellipse cx="22" cy="26" rx="13" ry="9"  fill="#607D8B"/>
      <ellipse cx="42" cy="26" rx="12" ry="8"  fill="#546E7A"/>
    </g>
    <g stroke="#42A5F5" stroke-width="2.2" stroke-linecap="round">
      <line x1="20" y1="36" x2="17" y2="50">
        <animate attributeName="y1" values="36;38;36" dur="0.9s" repeatCount="indefinite"/>
        <animate attributeName="y2" values="50;52;50" dur="0.9s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="1;0;1" dur="0.9s" repeatCount="indefinite"/>
      </line>
      <line x1="29" y1="34" x2="26" y2="48">
        <animate attributeName="y1" values="34;36;34" dur="0.8s" begin="0.2s" repeatCount="indefinite"/>
        <animate attributeName="y2" values="48;50;48" dur="0.8s" begin="0.2s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="1;0;1" dur="0.8s" begin="0.2s" repeatCount="indefinite"/>
      </line>
      <line x1="38" y1="36" x2="35" y2="50">
        <animate attributeName="y1" values="36;38;36" dur="1.0s" begin="0.1s" repeatCount="indefinite"/>
        <animate attributeName="y2" values="50;52;50" dur="1.0s" begin="0.1s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="1;0;1" dur="1.0s" begin="0.1s" repeatCount="indefinite"/>
      </line>
      <line x1="47" y1="34" x2="44" y2="48">
        <animate attributeName="y1" values="34;36;34" dur="0.85s" begin="0.45s" repeatCount="indefinite"/>
        <animate attributeName="y2" values="48;50;48" dur="0.85s" begin="0.45s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="1;0;1" dur="0.85s" begin="0.45s" repeatCount="indefinite"/>
      </line>
    </g>
  </svg>`,

  "lightning-rainy":`<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
    <g>
      <animateTransform attributeName="transform" type="translate"
        values="-2,0;2,0;-2,0" dur="6s" repeatCount="indefinite" calcMode="linear"/>
      <ellipse cx="32" cy="20" rx="18" ry="11" fill="#37474F"/>
      <ellipse cx="22" cy="25" rx="13" ry="9"  fill="#455A64"/>
      <ellipse cx="42" cy="25" rx="12" ry="8"  fill="#37474F"/>
    </g>
    <polygon points="34,32 27,44 33,44 28,55 39,40 33,40" fill="#FFD740">
      <animate attributeName="opacity" values="1;0.2;1;0.2;1" dur="2.8s" repeatCount="indefinite"/>
    </polygon>
    <g stroke="#64B5F6" stroke-width="2" stroke-linecap="round">
      <line x1="20" y1="38" x2="18" y2="48">
        <animate attributeName="opacity" values="1;0;1" dur="1.1s" repeatCount="indefinite"/>
      </line>
      <line x1="46" y1="37" x2="44" y2="47">
        <animate attributeName="opacity" values="1;0;1" dur="0.9s" begin="0.5s" repeatCount="indefinite"/>
      </line>
    </g>
  </svg>`,

  snowy:`<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
    <g>
      <animateTransform attributeName="transform" type="translate"
        values="-3,0;3,0;-3,0" dur="10s" repeatCount="indefinite" calcMode="linear"/>
      <ellipse cx="32" cy="24" rx="18" ry="11" fill="#B0BEC5"/>
      <ellipse cx="22" cy="28" rx="13" ry="9"  fill="#CFD8DC"/>
      <ellipse cx="42" cy="28" rx="12" ry="8"  fill="#B0BEC5"/>
    </g>
    <g fill="white">
      <circle cx="20" cy="40" r="2.2">
        <animate attributeName="cy" values="40;56;40" dur="2.0s" repeatCount="indefinite" calcMode="linear"/>
        <animate attributeName="opacity" values="1;0;1" dur="2.0s" repeatCount="indefinite"/>
      </circle>
      <circle cx="30" cy="37" r="1.6">
        <animate attributeName="cy" values="37;53;37" dur="2.3s" begin="0.4s" repeatCount="indefinite" calcMode="linear"/>
        <animate attributeName="opacity" values="1;0;1" dur="2.3s" begin="0.4s" repeatCount="indefinite"/>
      </circle>
      <circle cx="40" cy="40" r="2.0">
        <animate attributeName="cy" values="40;56;40" dur="1.8s" begin="0.8s" repeatCount="indefinite" calcMode="linear"/>
        <animate attributeName="opacity" values="1;0;1" dur="1.8s" begin="0.8s" repeatCount="indefinite"/>
      </circle>
      <circle cx="50" cy="37" r="1.4">
        <animate attributeName="cy" values="37;53;37" dur="2.5s" begin="0.2s" repeatCount="indefinite" calcMode="linear"/>
        <animate attributeName="opacity" values="1;0;1" dur="2.5s" begin="0.2s" repeatCount="indefinite"/>
      </circle>
    </g>
  </svg>`,

  windy:`<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
    <g stroke="#90A4AE" stroke-width="2.5" stroke-linecap="round" fill="none">
      <path d="M4 18 Q18 11 32 18 Q46 25 60 18">
        <animate attributeName="d"
          values="M4 18 Q18 11 32 18 Q46 25 60 18;M4 18 Q18 25 32 18 Q46 11 60 18;M4 18 Q18 11 32 18 Q46 25 60 18"
          dur="3.0s" repeatCount="indefinite" calcMode="linear"/>
      </path>
      <path d="M4 30 Q18 23 32 30 Q46 37 60 30">
        <animate attributeName="d"
          values="M4 30 Q18 23 32 30 Q46 37 60 30;M4 30 Q18 37 32 30 Q46 23 60 30;M4 30 Q18 23 32 30 Q46 37 60 30"
          dur="3.5s" begin="0.5s" repeatCount="indefinite" calcMode="linear"/>
      </path>
      <path d="M4 42 Q18 35 32 42 Q46 49 60 42">
        <animate attributeName="d"
          values="M4 42 Q18 35 32 42 Q46 49 60 42;M4 42 Q18 49 32 42 Q46 35 60 42;M4 42 Q18 35 32 42 Q46 49 60 42"
          dur="2.8s" begin="1.0s" repeatCount="indefinite" calcMode="linear"/>
      </path>
    </g>
  </svg>`,
};

// ── Icon key routing ──────────────────────────────────────────────────────
/** Maps Zambretti state keys to icon keys, same as ZAMBRETTI_CONDITION but kept separate for clarity. */
const ZAMBRETTI_TO_ICON = {
  settled_fine:"sunny", fine_weather:"sunny",
  fine_becoming_less_settled:"partlycloudy", fairly_fine_showery_later:"partlycloudy",
  showery_becoming_more_unsettled:"rainy", unsettled_rain_later:"cloudy",
  rain_at_times_worse_later:"rainy", rain_at_times_becoming_very_unsettled:"pouring",
  very_unsettled_rain:"pouring", fine_possibly_showers:"partlycloudy",
  fairly_fine_showers_likely:"partlycloudy", showery_bright_intervals:"rainy",
  changeable_some_rain:"cloudy", unsettled_rain_at_times:"rainy",
  rain_at_frequent_intervals:"pouring", stormy_much_rain:"lightning-rainy",
  becoming_fine:"partlycloudy", fairly_fine_improving:"partlycloudy",
  fairly_fine_possibly_showers_early:"partlycloudy", showery_early_improving:"rainy",
  changeable_mending:"cloudy", rather_unsettled_clearing_later:"cloudy",
  unsettled_probably_improving:"cloudy", unsettled_short_fine_intervals:"cloudy",
  very_unsettled_finer_at_times:"pouring", stormy_possibly_improving:"lightning-rainy",
  stable:"partlycloudy",
};

/**
 * Returns the icon key for a given Zambretti state, switching to night_clear
 * when it's nighttime and the state is settled_fine / fine_weather.
 * @param {string} zambrettiState
 * @param {boolean} isNight
 * @returns {string}
 */
function getWeatherIconKey(zambrettiState, isNight) {
  if (zambrettiState === "settled_fine" || zambrettiState === "fine_weather") {
    return isNight ? "night_clear" : "sunny";
  }
  return ZAMBRETTI_TO_ICON[zambrettiState] || "partlycloudy";
}

// ── Themes ────────────────────────────────────────────────────────────────
/** Background gradient definitions keyed by weather condition. */
const CONDITION_THEME = {
  sunny:            {bg:"linear-gradient(135deg,#FF8C00 0%,#FFA500 40%,#FFD700 100%)"},
  night_clear:      {bg:"linear-gradient(135deg,#070B14 0%,#0F172A 50%,#1E293B 100%)"},
  partlycloudy:     {bg:"linear-gradient(135deg,#FF8C00 0%,#BBDEFB 50%,#FFFFFF 100%)"},
  cloudy:           {bg:"linear-gradient(135deg,#606C76 0%,#7E8A95 50%,#A2AEB8 100%)"},
  rainy:            {bg:"linear-gradient(135deg,#425363 0%,#54677A 50%,#70879C 100%)"},
  pouring:          {bg:"linear-gradient(135deg,#1C242D 0%,#2B3745 50%,#3F5063 100%)"},
  "lightning-rainy":{bg:"linear-gradient(135deg,#23153A 0%,#43286B 50%,#6943A3 100%)"},
  snowy:            {bg:"linear-gradient(135deg,#B8C6D4 0%,#DDE5ED 50%,#F4F7FA 100%)"},
  windy:            {bg:"linear-gradient(135deg,#5F9EA0 0%,#87B6B8 50%,#B4D3D4 100%)"},
};
/** Fallback theme used when no condition-specific theme matches. */
const DEFAULT_THEME = {bg:"linear-gradient(135deg,#1565C0 0%,#1976D2 100%)"};
/** Returns the theme object for a given condition key, falling back to DEFAULT_THEME. */
function getTheme(c){ return CONDITION_THEME[c] || DEFAULT_THEME; }

// ── Alpha helper: appends alpha channel to all 6-digit hex colors in a CSS string ──
/**
 * Appends an alpha (opacity) suffix to every 6-digit hex color in a CSS gradient string.
 * No-op when alphaPct is 100 or invalid.
 * @param {string} bgString  CSS background value (e.g. linear-gradient with hex stops)
 * @param {number} alphaPct  Opacity percentage 0–100
 * @returns {string}
 */
function applyAlpha(bgString, alphaPct) {
  if (alphaPct === undefined || alphaPct >= 100 || typeof alphaPct !== 'number' || isNaN(alphaPct)) return bgString;
  const a = Math.max(0, Math.min(100, alphaPct));
  const hex = Math.round((a / 100) * 255).toString(16).padStart(2, "0").toUpperCase();
  // Replace every 6-digit hex color in the string with hex + alpha
  return bgString.replace(/#([0-9a-fA-F]{6})(?![0-9a-fA-F])/gi, `#$1${hex}`);
}

// ── Short label helper ────────────────────────────────────────────────────
/**
 * Returns a short (max 2-word) version of a forecast label for compact display.
 * @param {string} key   i18n key
 * @param {object} labels  label map
 * @returns {string}
 */
function shortLabel(key, labels) {
  const full = labels[key] || key || "—";
  return full.split(/[,\s]+/).filter(Boolean).slice(0, 2).join(" ");
}

// ── Unique ID counter for SVG gradients ──────────────────────────────────
/** Monotonic counter used to generate unique SVG gradient/clipPath IDs per render. */
let _gradientIdCounter = 0;

// ── Wind direction degrees → compass string ───────────────────────────────
/**
 * Converts a wind direction in degrees to an 8-point compass string (N, NE, E, …).
 * @param {number|null} deg
 * @returns {string}
 */
function degToCompass(deg) {
  if (deg === null || deg === undefined) return "";
  const dirs = ["N","NE","E","SE","S","SW","W","NW"];
  return dirs[Math.round((deg % 360) / 45) % 8];
}

// ── Format wind speed with correct unit ──────────────────────────────────
// sensorUnit: the native unit reported by the HA sensor (e.g. "km/h", "m/s", "mph")
// displayUnit: the unit the user wants to see on the card
/**
 * Converts a raw wind speed value from the sensor's native unit to the user's
 * chosen display unit and returns a formatted string (e.g. "SW 12 km/h").
 * @param {number|string|null} speed  Raw sensor value
 * @param {string} displayUnit  Target unit: "m/s" | "km/h" | "mph" | "kn"
 * @param {string} sensorUnit   Native sensor unit
 * @returns {string|null}
 */
function formatWind(speed, displayUnit, sensorUnit) {
  if (speed === null || speed === undefined) return null;
  const n = parseFloat(speed);
  if (isNaN(n)) return null;

  // Normalise sensor unit string (HA uses "km/h", card config uses "km/h")
  const src = (sensorUnit || "m/s").toLowerCase().replace(" ", "");
  const dst = (displayUnit || "m/s").toLowerCase().replace(" ", "");

  // Convert the raw value to m/s first, then to the desired display unit
  let ms;
  if (src === "km/h" || src === "kmh") {
    ms = n / 3.6;
  } else if (src === "mph") {
    ms = n / 2.23694;
  } else if (src === "kn" || src === "kt" || src === "knots") {
    ms = n / 1.94384;
  } else {
    ms = n; // already m/s
  }

  if (dst === "mph") {
    return `${(ms * 2.23694).toFixed(1)} mph`;
  }
  if (dst === "km/h" || dst === "kmh") {
    return `${Math.round(ms * 3.6)} km/h`;
  }
  if (dst === "kn" || dst === "kt") {
    return `${(ms * 1.94384).toFixed(1)} kn`;
  }
  return `${ms.toFixed(1)} m/s`; // default m/s
}

// ── Precipitation gauge SVG ───────────────────────────────────────────────
/**
 * Renders a circular arc gauge SVG showing precipitation probability.
 * @param {number} pct  Value 0–100
 * @returns {string}  SVG markup string
 */
function precipWidget(pct) {
  const r=44, cx=60, cy=60, circ=2*Math.PI*r;
  const trackLen=circ*0.75, trackGap=circ-trackLen;
  const fillLen=trackLen*(pct/100), fillGap=circ-fillLen;
  const rot=-225;
  const fillColor = pct < 30 ? "#90CAF9" : pct < 60 ? "#42A5F5" : "#1565C0";
  const gid = "pw" + (++_gradientIdCounter);
  return `<svg viewBox="0 0 120 110" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%">
    <defs>
      <linearGradient id="${gid}" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="${fillColor}" stop-opacity="0.75"/>
        <stop offset="100%" stop-color="${fillColor}" stop-opacity="1"/>
      </linearGradient>
    </defs>
    <circle cx="${cx}" cy="${cy}" r="${r}" fill="none"
      stroke="rgba(255,255,255,0.20)" stroke-width="10"
      stroke-dasharray="${trackLen.toFixed(2)} ${trackGap.toFixed(2)}"
      stroke-linecap="round" transform="rotate(${rot} ${cx} ${cy})"/>
    <circle cx="${cx}" cy="${cy}" r="${r}" fill="none"
      stroke="url(#${gid})" stroke-width="10"
      stroke-dasharray="${fillLen.toFixed(2)} ${fillGap.toFixed(2)}"
      stroke-linecap="round" transform="rotate(${rot} ${cx} ${cy})"
      style="transition:stroke-dasharray .9s ease"/>
    <text x="${cx}" y="${cy}" text-anchor="middle" dominant-baseline="central"
      fill="white" font-size="22" font-weight="900"
      font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">${pct}%</text>
  </svg>`;
}

// ── Forecast trend timeline ───────────────────────────────────────────────
/**
 * Render a horizontal strip of Zambretti forecast states over time.
 * Each step: small weather icon + time label. Steps separated by → arrows.
 * The last (current) step is highlighted.
 *
 * @param {Array<{t:Date, state:string, isCurrent?:boolean}>} steps  max 8
 * @param {object} labels  i18n map
 * @param {boolean} compact
 * @returns {string}  HTML string
 */
function forecastTimeline(steps, labels, compact) {
  if (!steps || steps.length === 0) {
    return `<div class="tl-empty">— no trend data yet —</div>`;
  }

  const iconSz = compact ? 28 : 34;

  // Format time: HH:MM
  function fmt(date) {
    return `${String(date.getHours()).padStart(2,"0")}:${String(date.getMinutes()).padStart(2,"0")}`;
  }

  const cells = steps.map((step, i) => {
    const isLast = i === steps.length - 1;
    const iconKey = ZAMBRETTI_TO_ICON[step.state] || "partlycloudy";
    const svg = WEATHER_ICONS[iconKey] || WEATHER_ICONS.partlycloudy;
    // Short label: first word only (keeps it compact)
    const fullLabel = labels[step.state] || step.state || "—";
    const shortLbl  = fullLabel.split(/[,\s]+/)[0];
    const timeStr   = fmt(step.t);
    const curClass  = (step.isCurrent || isLast) ? " tl-current" : "";

    const arrow = (!isLast)
      ? `<div class="tl-arrow">›</div>`
      : "";

    return `
      <div class="tl-step${curClass}">
        <div class="tl-icon" style="width:${iconSz}px;height:${iconSz}px">${svg}</div>
        <div class="tl-lbl">${shortLbl}</div>
        <div class="tl-time">${timeStr}</div>
      </div>
      ${arrow}`;
  }).join("");

  return `<div class="tl-inner">${cells}</div>`;
}

// ── History chart SVG ────────────────────────────────────────────────────
/**
 * Render a dual-axis SVG line chart:
 *   - blue line  = pressure (hPa), left axis
 *   - teal line  = precipitation probability (%), right axis
 *   - grey bars  = Zambretti condition label (bottom strip)
 *
 * @param {Array<{t:Date, p:number|null, precip:number|null, label:string|null}>} points
 *   Sorted oldest→newest, max 288 points (24h × 5-min intervals).
 * @param {object} labels  i18n label map for Zambretti keys
 * @param {boolean} compact  use compact sizing
 * @returns {string}  SVG markup string
 */
function historyChart(points, labels, compact) {
  if (!points || points.length < 2) {
    return `<div class="hchart-empty">— no history data yet —</div>`;
  }

  const W = 560, H = compact ? 150 : 200;
  const PAD = { top: 22, right: 16, bottom: 38, left: 56 };
  const cW = W - PAD.left - PAD.right;
  const cH = H - PAD.top - PAD.bottom;
  const FONT = compact ? 11 : 13;
  const FONT_FAMILY = "-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif";

  // ── Filter out nulls ───────────────────────────────────────────────────
  let pPoints  = points.filter(d => d.p    != null);
  let prPoints = points.filter(d => d.precip != null);

  // ── Spike filter (IQR) for pressure only ─────────────────────────────
  if (pPoints.length >= 4) {
    const sv = [...pPoints].map(d => d.p).sort((a, b) => a - b);
    const q1 = sv[Math.floor(sv.length * 0.25)];
    const q3 = sv[Math.floor(sv.length * 0.75)];
    const iqr = q3 - q1;
    pPoints = pPoints.filter(d => d.p >= q1 - 3*iqr && d.p <= q3 + 3*iqr);
  }
  // Note: no IQR filter for precip — 0–100% are all valid values

  // ── Pressure axis ─────────────────────────────────────────────────────
  let pMin = 980, pMax = 1040;
  if (pPoints.length) {
    const vals = pPoints.map(d => d.p);
    const lo = Math.min(...vals), hi = Math.max(...vals);
    const margin = Math.max(2, (hi - lo) * 0.15);
    pMin = Math.floor(lo - margin);
    pMax = Math.ceil(hi + margin);
  }

  // ── Time axis ─────────────────────────────────────────────────────────
  const tMin = points[0].t.getTime();
  const tMax = points[points.length - 1].t.getTime();
  const tRange = tMax - tMin || 1;

  function xOf(t)  { return PAD.left + ((t.getTime() - tMin) / tRange) * cW; }
  function yOfP(v) { return PAD.top  + (1 - (v - pMin) / (pMax - pMin)) * cH; }
  function yOfPr(v){ return PAD.top  + (1 - v / 100) * cH; }

  // ── Polyline paths ────────────────────────────────────────────────────
  function makePath(pts, yFn) {
    if (!pts.length) return "";
    return pts.map((d, i) => `${i === 0 ? "M" : "L"}${xOf(d.t).toFixed(1)},${yFn(i === 0 ? pts[0][yFn === yOfP ? "p" : "precip"] : d[yFn === yOfP ? "p" : "precip"]).toFixed(1)}`).join(" ");
  }
  // build paths properly
  const pPath  = pPoints.map((d, i)  => `${i===0?"M":"L"}${xOf(d.t).toFixed(1)},${yOfP(d.p).toFixed(1)}`).join(" ");
  const prPath = prPoints.map((d, i) => `${i===0?"M":"L"}${xOf(d.t).toFixed(1)},${yOfPr(d.precip).toFixed(1)}`).join(" ");

  // ── Area fill for pressure ─────────────────────────────────────────────
  const pAreaPath = pPoints.length ? (
    pPath +
    ` L${xOf(pPoints[pPoints.length-1].t).toFixed(1)},${(PAD.top+cH).toFixed(1)}` +
    ` L${xOf(pPoints[0].t).toFixed(1)},${(PAD.top+cH).toFixed(1)} Z`
  ) : "";

  // ── Y-axis ticks (pressure) ────────────────────────────────────────────
  const pTickCount = compact ? 3 : 4;
  const pStep = Math.ceil((pMax - pMin) / (pTickCount - 1) / 5) * 5;
  const pTicks = [];
  for (let v = Math.ceil(pMin / 5) * 5; v <= pMax; v += pStep) pTicks.push(v);

  // ── Y-axis ticks (precip %) ────────────────────────────────────────────
  const prTicks = [0, 25, 50, 75, 100];

  // ── X-axis time labels (every 6h) ─────────────────────────────────────
  const xLabels = [];
  {
    const start = new Date(tMin);
    // round up to next whole hour
    start.setMinutes(0, 0, 0);
    start.setHours(start.getHours() + 1);
    const cur = new Date(start);
    while (cur.getTime() <= tMax) {
      if (cur.getHours() % 6 === 0) {
        xLabels.push({ t: new Date(cur), label: `${String(cur.getHours()).padStart(2,"0")}:00` });
      }
      cur.setHours(cur.getHours() + 1);
    }
  }

  // ── Current time marker ───────────────────────────────────────────────
  const nowX = xOf(new Date(tMax));

  // ── Last pressure value annotation ───────────────────────────────────
  let lastPAnnot = "";
  if (pPoints.length) {
    const last = pPoints[pPoints.length - 1];
    const lx = xOf(last.t), ly = yOfP(last.p);
    // Always place label to the LEFT of the dot to avoid right-edge overflow
    lastPAnnot = `
      <circle cx="${lx.toFixed(1)}" cy="${ly.toFixed(1)}" r="5" fill="#90CAF9" stroke="#fff" stroke-width="1.5"/>
      <text x="${(lx - 8).toFixed(1)}" y="${(ly + 14).toFixed(1)}" text-anchor="middle"
        fill="#90CAF9" font-size="${FONT + 2}" font-weight="800"
        font-family="${FONT_FAMILY}">${last.p.toFixed(1)}</text>`;
  }
  let lastPrAnnot = "";
  if (prPoints.length) {
    const last = prPoints[prPoints.length - 1];
    const lx = xOf(last.t), ly = yOfPr(last.precip);
    // Place precip label above the dot
    lastPrAnnot = `
      <circle cx="${lx.toFixed(1)}" cy="${ly.toFixed(1)}" r="4.5" fill="rgba(255,255,255,0.90)" stroke="rgba(255,255,255,0.35)" stroke-width="1.5"/>
      <text x="${(lx - 8).toFixed(1)}" y="${(ly - 10).toFixed(1)}" text-anchor="middle"
        fill="rgba(255,255,255,0.85)" font-size="${FONT + 1}" font-weight="700"
        font-family="${FONT_FAMILY}">${last.precip.toFixed(0)}%</text>`;
  }

  // ── Precip area fill (bottom-anchored) ────────────────────────────────
  const prAreaPath = prPoints.length ? (
    prPath +
    ` L${xOf(prPoints[prPoints.length-1].t).toFixed(1)},${(PAD.top+cH).toFixed(1)}` +
    ` L${xOf(prPoints[0].t).toFixed(1)},${(PAD.top+cH).toFixed(1)} Z`
  ) : "";

  const gid = "hg" + (++_gradientIdCounter);

  return `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg"
    style="width:100%;height:100%;display:block;overflow:visible">
    <defs>
      <linearGradient id="${gid}_p" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%"   stop-color="#90CAF9" stop-opacity="0.40"/>
        <stop offset="100%" stop-color="#90CAF9" stop-opacity="0.05"/>
      </linearGradient>
      <linearGradient id="${gid}_pr" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%"   stop-color="rgba(255,255,255,0.22)" stop-opacity="1"/>
        <stop offset="100%" stop-color="rgba(255,255,255,0.02)" stop-opacity="1"/>
      </linearGradient>
      <clipPath id="${gid}_clip">
        <rect x="${PAD.left}" y="${PAD.top}" width="${cW}" height="${cH}"/>
      </clipPath>
    </defs>

    <!-- Horizontal grid lines (pressure ticks) -->
    ${pTicks.map(v => {
      const y = yOfP(v).toFixed(1);
      return `<line x1="${PAD.left}" y1="${y}" x2="${PAD.left+cW}" y2="${y}"
        stroke="rgba(255,255,255,0.12)" stroke-width="1" stroke-dasharray="4 5"/>`;
    }).join("")}
    <!-- Vertical grid lines (time ticks) -->
    ${xLabels.map(({t}) => {
      const x = xOf(t).toFixed(1);
      return `<line x1="${x}" y1="${PAD.top}" x2="${x}" y2="${PAD.top+cH}"
        stroke="rgba(255,255,255,0.08)" stroke-width="1" stroke-dasharray="2 5"/>`;
    }).join("")}

    <g clip-path="url(#${gid}_clip)">
      <!-- Precip area fill -->
      ${prAreaPath ? `<path d="${prAreaPath}" fill="url(#${gid}_pr)"/>` : ""}
      <!-- Precip line: dashed white, visible on any background -->
      ${prPath ? `<path d="${prPath}" fill="none" stroke="rgba(255,255,255,0.72)"
        stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
        stroke-dasharray="5 4"/>` : ""}
      <!-- Pressure area fill -->
      ${pAreaPath ? `<path d="${pAreaPath}" fill="url(#${gid}_p)"/>` : ""}
      <!-- Pressure line: solid, on top -->
      ${pPath ? `<path d="${pPath}" fill="none" stroke="#90CAF9"
        stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>` : ""}
      ${lastPAnnot}
      ${lastPrAnnot}
    </g>

    <!-- Left Y-axis labels (pressure) -->
    ${pTicks.map(v => {
      const y = yOfP(v);
      if (y < PAD.top - 4 || y > PAD.top + cH + 4) return "";
      return `<text x="${PAD.left - 7}" y="${y.toFixed(1)}" text-anchor="end"
        dominant-baseline="middle" fill="rgba(255,255,255,0.70)"
        font-size="${FONT}" font-family="${FONT_FAMILY}">${v}</text>`;
    }).join("")}

    <!-- Right Y-axis labels (precip %) — positioned inside right edge -->
    ${prTicks.map(v => {
      const y = yOfPr(v);
      if (y < PAD.top - 4 || y > PAD.top + cH + 4) return "";
      return `<text x="${(PAD.left + cW - 2).toFixed(1)}" y="${y.toFixed(1)}" text-anchor="end"
        dominant-baseline="middle" fill="rgba(255,255,255,0.45)"
        font-size="${FONT - 2}" font-family="${FONT_FAMILY}">${v}%</text>`;
    }).join("")}

    <!-- X-axis time labels -->
    ${xLabels.map(({t, label}) => {
      const x = xOf(t);
      if (x < PAD.left + 6 || x > PAD.left + cW - 6) return "";
      return `<text x="${x.toFixed(1)}" y="${(PAD.top+cH+15).toFixed(1)}" text-anchor="middle"
        fill="rgba(255,255,255,0.55)" font-size="${FONT}"
        font-family="${FONT_FAMILY}">${label}</text>`;
    }).join("")}

    <!-- Axis borders -->
    <line x1="${PAD.left}" y1="${PAD.top}" x2="${PAD.left}" y2="${PAD.top+cH}"
      stroke="rgba(255,255,255,0.25)" stroke-width="1.5"/>
    <line x1="${PAD.left}" y1="${PAD.top+cH}" x2="${PAD.left+cW}" y2="${PAD.top+cH}"
      stroke="rgba(255,255,255,0.25)" stroke-width="1.5"/>

    <!-- Legend -->
    <circle cx="${PAD.left+7}" cy="${PAD.top-7}" r="4" fill="#90CAF9"/>
    <text x="${PAD.left+15}" y="${PAD.top-4}" fill="rgba(255,255,255,0.70)"
      font-size="${FONT}" font-family="${FONT_FAMILY}" dominant-baseline="middle">hPa</text>
    <circle cx="${PAD.left+52}" cy="${PAD.top-7}" r="4" fill="rgba(255,255,255,0.80)"/>
    <text x="${PAD.left+60}" y="${PAD.top-4}" fill="rgba(255,255,255,0.60)"
      font-size="${FONT}" font-family="${FONT_FAMILY}" dominant-baseline="middle">precip %</text>
  </svg>`;
}

// ── Main card class ───────────────────────────────────────────────────────
/**
 * Main Lovelace card element.
 * Renders the weather card, handles hass state updates via full rebuild (_render)
 * or lightweight patch (_patch), and fetches 24h history for the chart/timeline.
 */
class ZambrettiWeatherCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode:"open"});
    this._config = {};
    this._historyPoints = null;   // cached chart data
    this._historyFetching = false;
    this._historyTimer = null;
  }

  /** Returns the editor element used by the Lovelace card picker. */
  static getConfigElement() { return document.createElement("zambretti-weather-card-editor"); }

  /** Returns a minimal default config for the card picker preview. */
  static getStubConfig() {
    return {
      entity_zambretti: "sensor.zambretti_forecast",
      entity_sager:     "sensor.sager_forecast",
      entity_6h:        "sensor.zambretti_forecast_6h",
      entity_12h:       "sensor.zambretti_forecast_12h",
      entity_24h:       "sensor.zambretti_forecast_24h",
      entity_precip:    "sensor.precipitation_probability",
      entity_wind_speed:  "",
      show_wind:    true,
      show_trend:   false,
      show_history: false,
      language:     "auto",
      wind_unit:    "m/s",
      compact:      false,
      auto_theme:   true,
      theme_alpha:  100,
      custom_bg:    "linear-gradient(135deg,#1565C0 0%,#1976D2 100%)",
    };
  }

  /** Applies a new card config, resets render state and clears history cache if needed. */
  setConfig(config) {
    this._rendered = false;
    this._entitiesResolved = false;
    // If history/trend toggle changed, reset cache
    if (config.show_history !== this._config.show_history ||
        config.show_trend   !== this._config.show_trend) {
      this._historyPoints  = null;
      this._timelineSteps  = null;
    }
    this._config = {
      entity_zambretti: "sensor.zambretti_forecast",
      entity_sager:     "sensor.sager_forecast",
      entity_6h:        "sensor.zambretti_forecast_6h",
      entity_12h:       "sensor.zambretti_forecast_12h",
      entity_24h:       "sensor.zambretti_forecast_24h",
      entity_precip:    "sensor.precipitation_probability",
      entity_wind_speed:  "",
      show_wind:      true,
      show_trend:     false,
      show_history:   false,
      language:       "auto",
      wind_unit:      "m/s",
      compact:        false,
      show_sager:     true,
      show_precip:    true,
      show_forecasts: true,
      auto_theme:     true,
      theme_alpha:    config.theme_alpha ?? 100,
      custom_bg:      "linear-gradient(135deg,#1565C0 0%,#1976D2 100%)",
      ...config,
    };
  }

  // ── Auto-discover entity IDs by unique_id suffixes ───────────────────────
  // HA builds entity_id as: sensor.<device_slug>_<sensor_name_slug>
  // e.g. sensor.weather_station_zambretti_forecast
  // We find them by matching unique_id suffixes stored in entity registry,
  // or fall back to scanning hass.states for known name patterns.
  /**
   * Scans hass.states for sensor entities whose IDs end with known suffixes
   * and returns a map of config key → resolved entity_id.
   * @param {object} h  hass object
   * @returns {object}
   */
  _resolveEntities(h) {
    const SUFFIX_MAP = {
      entity_zambretti: ["_zambretti_forecast", "zambretti_forecast"],
      entity_sager:     ["_sager_forecast",     "sager_forecast"],
      entity_6h:        ["_zambretti_forecast_6h",  "zambretti_forecast_6h"],
      entity_12h:       ["_zambretti_forecast_12h", "zambretti_forecast_12h"],
      entity_24h:       ["_zambretti_forecast_24h", "zambretti_forecast_24h"],
      entity_precip:    ["_precipitation_probability", "precipitation_probability"],
    };
    const states = h.states;
    const resolved = {};
    for (const [key, suffixes] of Object.entries(SUFFIX_MAP)) {
      // Already configured and entity exists — keep it
      const cur = this._config[key];
      if (cur && states[cur]) { resolved[key] = cur; continue; }
      // Search all sensor entities for a matching suffix
      const found = Object.keys(states).find(id => {
        if (!id.startsWith("sensor.")) return false;
        const slug = id.slice(7); // strip "sensor."
        return suffixes.some(s => slug === s || slug.endsWith(s));
      });
      if (found) resolved[key] = found;
    }
    return resolved;
  }

  set hass(h) {
    this._hass = h;
    // Auto-resolve entity IDs on first load (handles "weather_station_" prefix etc.)
    if (!this._entitiesResolved) {
      const resolved = this._resolveEntities(h);
      if (Object.keys(resolved).length > 0) {
        this._config = {...this._config, ...resolved};
      }
      this._entitiesResolved = true;
    }
    // Kick off history fetch (debounced) when show_history or show_trend is on
    if (this._config.show_history || this._config.show_trend) {
      this._scheduleHistoryFetch();
    }
    // Full rebuild only on first render or after config change.
    // Subsequent hass updates use _patch() to avoid destroying SVG animations.
    if (!this._rendered) {
      this._render();
    } else {
      this._patch();
    }
  }

  // ── History fetch ─────────────────────────────────────────────────────
  /**
   * Triggers a history fetch if one isn't already running and the throttle
   * interval (5 min) has elapsed. Updates chart and timeline on completion.
   */
  _scheduleHistoryFetch() {
    if (this._historyFetching) return;
    // Throttle: refetch at most once per 5 minutes
    const now = Date.now();
    if (this._historyFetchedAt && (now - this._historyFetchedAt) < 5 * 60 * 1000) return;
    this._historyFetching = true;
    this._doFetchHistory().then(() => {
      this._historyFetching = false;
      this._historyFetchedAt = Date.now();
      // Re-render chart and/or timeline section only
      if (this._rendered) {
        if (this._config.show_history) this._patchChart();
        if (this._config.show_trend)   this._patchTimeline();
      }
    }).catch(() => {
      this._historyFetching = false;
    });
  }

  /**
   * Fetches 24–48h of Zambretti state, pressure and precipitation history
   * via the HA WebSocket history API. Populates _historyPoints and _timelineSteps.
   */
  async _doFetchHistory() {
    if (!this._hass) return;
    const cfg = this._config;
    const endTime   = new Date();

    const zId      = cfg.entity_zambretti;
    const precipId = cfg.entity_precip;
    // Read pressure sensor entity_id from zambretti sensor attribute
    // (set by the Python integration — the raw BMP280/barometric sensor)
    const pressureId = this._attr(zId, "pressure_sensor", null) || null;

    if (!zId && !precipId) return;

    // Chart uses 24h window; timeline uses 48h to catch more state changes
    const chartStart    = new Date(endTime.getTime() - 24 * 60 * 60 * 1000);
    const timelineStart = new Date(endTime.getTime() - 48 * 60 * 60 * 1000);

    try {
      // Two separate requests:
      // 1. Zambretti: minimal_response=false to get attributes (pressure_hpa)
      // 2. Precip:    minimal_response=true  (only state value needed)
      const [zResult, prResult, pResult] = await Promise.all([
        // Zambretti: 48h, full format for timeline states
        zId ? this._hass.callWS({
          type: "history/history_during_period",
          start_time: timelineStart.toISOString(),
          end_time:   endTime.toISOString(),
          entity_ids: [zId],
          minimal_response: false,
          no_attributes: false,
          significant_changes_only: false,
        }) : Promise.resolve({}),
        // Precip: 24h, minimal (only state value needed)
        precipId ? this._hass.callWS({
          type: "history/history_during_period",
          start_time: chartStart.toISOString(),
          end_time:   endTime.toISOString(),
          entity_ids: [precipId],
          minimal_response: true,
          no_attributes: true,
          significant_changes_only: false,
        }) : Promise.resolve({}),
        // Raw pressure sensor: 24h, minimal (dense real data from BMP280)
        pressureId ? this._hass.callWS({
          type: "history/history_during_period",
          start_time: chartStart.toISOString(),
          end_time:   endTime.toISOString(),
          entity_ids: [pressureId],
          minimal_response: true,
          no_attributes: true,
          significant_changes_only: false,
        }) : Promise.resolve({}),
      ]);

      // ── Helpers ────────────────────────────────────────────────────────
      function bucket(t) { return Math.round(t.getTime() / (5 * 60 * 1000)); }

      // HA history_during_period returns entries in two possible shapes:
      //   Full format  (minimal_response=false): { state, last_updated, attributes:{...} }
      //   Minimal format (minimal_response=true): { s, lu, a:{...} }
      // Some HA versions also mix: { state, lu, attributes }
      function entryTime(entry) {
        if (entry.lu != null)       return new Date(entry.lu * 1000);
        if (entry.last_updated)     return new Date(entry.last_updated);
        return new Date();
      }
      function entryState(entry) {
        return entry.state ?? entry.s ?? null;
      }
      function entryAttrs(entry) {
        // Full format: entry.attributes  |  Minimal: entry.a
        return entry.attributes ?? entry.a ?? {};
      }

      // ── Build timeMap from zambretti history (last 24h only for chart) ─
      const timeMap = new Map();
      const zHistory = zResult[zId] || [];
      const chartStartMs = chartStart.getTime();

      if (pressureId) {
        // ── Use raw pressure sensor (dense data, e.g. BMP280 every 5 min) ─
        const pHistory = pResult[pressureId] || [];
        for (const entry of pHistory) {
          const t   = entryTime(entry);
          if (t.getTime() < chartStartMs) continue;
          const key = bucket(t);
          const p   = parseFloat(entryState(entry));
          if (!timeMap.has(key)) timeMap.set(key, { t, p: null, precip: null });
          if (!isNaN(p)) timeMap.get(key).p = p;
        }
      } else {
        // ── Fallback: pressure from zambretti sensor attributes ────────────
        for (const entry of zHistory) {
          const t    = entryTime(entry);
          if (t.getTime() < chartStartMs) continue;
          const key  = bucket(t);
          const attrs = entryAttrs(entry);
          const p    = parseFloat(attrs.pressure_hpa);
          if (!timeMap.has(key)) timeMap.set(key, { t, p: null, precip: null });
          if (!isNaN(p)) timeMap.get(key).p = p;
        }
      }

      // ── Forward-fill pressure so line is continuous ────────────────────
      let sortedKeys = [...timeMap.keys()].sort((a, b) => a - b);
      let lastP = null;
      for (const key of sortedKeys) {
        const pt = timeMap.get(key);
        if (pt.p != null) { lastP = pt.p; }
        else if (lastP != null) { pt.p = lastP; }
      }
      // Backward-fill: fill leading nulls from the first known value
      let firstP = null;
      for (const key of sortedKeys) {
        if (timeMap.get(key).p != null) { firstP = timeMap.get(key).p; break; }
      }
      if (firstP != null) {
        for (const key of sortedKeys) {
          const pt = timeMap.get(key);
          if (pt.p != null) break;
          pt.p = firstP;
        }
      }

      // ── Precip: add its own time buckets + forward-fill across all buckets ─
      const prHistory = prResult[precipId] || [];
      const prRaw = prHistory
        .map(e => ({ t: entryTime(e), v: parseFloat(entryState(e)) }))
        .filter(x => !isNaN(x.v))
        .sort((a, b) => a.t - b.t);

      // Always inject the live current value as the last data point
      // so the line always ends at the actual current reading
      const livePrecip = parseFloat(this._hass?.states?.[precipId]?.state);
      if (!isNaN(livePrecip)) {
        const nowKey = bucket(endTime);
        if (!timeMap.has(nowKey)) timeMap.set(nowKey, { t: endTime, p: null, precip: null });
        timeMap.get(nowKey).precip = livePrecip;
        // Re-add to prRaw so forward-fill uses it
        prRaw.push({ t: endTime, v: livePrecip });
        prRaw.sort((a, b) => a.t - b.t);
      }

      if (prRaw.length) {
        // Add precip-only buckets into timeMap
        for (const { t, v } of prRaw) {
          if (t.getTime() < chartStartMs) continue;
          const key = bucket(t);
          if (!timeMap.has(key)) timeMap.set(key, { t, p: null, precip: null });
          timeMap.get(key).precip = v;
        }
        // Re-sort after possible new keys
        sortedKeys.length = 0;
        sortedKeys.push(...[...timeMap.keys()].sort((a, b) => a - b));
        // Re-run pressure fills on new sorted keys
        lastP = null;
        for (const key of sortedKeys) {
          const pt = timeMap.get(key);
          if (pt.p != null) { lastP = pt.p; }
          else if (lastP != null) { pt.p = lastP; }
        }
        if (firstP != null) {
          for (const key of sortedKeys) {
            const pt = timeMap.get(key);
            if (pt.p != null) break;
            pt.p = firstP;
          }
        }
        // Forward-fill precip across all buckets
        let pi = 0;
        let lastPrecip = prRaw[0].v;
        for (const key of sortedKeys) {
          const tMs = timeMap.get(key).t.getTime();
          while (pi + 1 < prRaw.length && prRaw[pi + 1].t.getTime() <= tMs) pi++;
          if (prRaw[pi].t.getTime() <= tMs) lastPrecip = prRaw[pi].v;
          if (timeMap.get(key).precip == null) timeMap.get(key).precip = lastPrecip;
        }
      }

      this._historyPoints = sortedKeys.map(k => timeMap.get(k));

      // ── Timeline: all distinct state transitions + current ───────────────
      const zValid = zHistory
        .map(e => ({ t: entryTime(e), state: entryState(e) }))
        .filter(e => e.state && e.state !== "unknown" && e.state !== "unavailable")
        .sort((a, b) => a.t - b.t);

      // Collect transitions — deduplicate consecutive same states
      // AND enforce minimum 30-min gap between steps to avoid near-duplicate timestamps
      const transitions = [];
      for (const e of zValid) {
        const prev = transitions[transitions.length - 1];
        if (prev && prev.state === e.state) continue;
        // Skip if less than 30 min since last step (startup noise)
        if (prev && (e.t.getTime() - prev.t.getTime()) < 30 * 60 * 1000) {
          // Update the existing step to the newer time & state
          prev.state = e.state;
          prev.t = e.t;
          continue;
        }
        transitions.push({ t: e.t, state: e.state });
      }

      // Take last 7 transitions (leave room for current)
      const pastSteps = transitions.slice(-7);

      // Add current state pinned to now
      const curState = this._hass.states[zId]?.state;
      if (curState && curState !== "unknown" && curState !== "unavailable") {
        const last = pastSteps[pastSteps.length - 1];
        if (!last || last.state !== curState) {
          pastSteps.push({ t: new Date(), state: curState, isCurrent: true });
        } else {
          last.isCurrent = true;
          last.t = new Date();
        }
      }

      this._timelineSteps = pastSteps;

    } catch (e) {
      // history fetch failed silently — chart/timeline will show empty state
      this._historyPoints = [];
      this._timelineSteps = [];
    }
  }

  // ── Patch only the chart area without full rebuild ─────────────────────
  /** Re-renders only the history chart section without destroying the rest of the DOM. */
  _patchChart() {
    const chartWrap = this.shadowRoot?.querySelector(".history-chart-wrap");
    if (!chartWrap) {
      // Chart section not in DOM yet — do full rebuild
      this._rendered = false;
      this._render();
      return;
    }
    const compact = !!this._config.compact;
    chartWrap.style.height = `${compact ? 150 : 200}px`;
    const L = this._labels();
    chartWrap.innerHTML = historyChart(this._historyPoints, L, compact);
  }

  // ── Patch only the timeline strip without full rebuild ──────────────────
  /** Re-renders only the forecast trend timeline strip without a full card rebuild. */
  _patchTimeline() {
    const wrap = this.shadowRoot?.querySelector(".trend-timeline-wrap");
    if (!wrap) {
      this._rendered = false;
      this._render();
      return;
    }
    const L = this._labels();
    wrap.innerHTML = forecastTimeline(this._timelineSteps, L, !!this._config.compact);
  }

  /** Subscribes to the background-preview custom event dispatched by the editor. */
  connectedCallback() {
    this._bgHandler = e => {
      if (this._config && this._config.auto_theme === false) {
        this._config = {...this._config, custom_bg: e.detail.bg};
        const card = this.shadowRoot.querySelector("ha-card");
        if (card) card.style.background = e.detail.bg;
      }
    };
    window.addEventListener("zambretti-bg-preview", this._bgHandler);
  }

  /** Cleans up the background-preview event listener. */
  disconnectedCallback() {
    window.removeEventListener("zambretti-bg-preview", this._bgHandler);
  }

  /** Returns the current state string of a HA entity, or null if unavailable. */
  _state(id)              { return this._hass?.states?.[id]?.state ?? null; }
  /** Returns a specific attribute of a HA entity, or the fallback value. */
  _attr(id, key, fallback){ return this._hass?.states?.[id]?.attributes?.[key] ?? fallback; }

  /** Returns the resolved i18n label map for the configured language. */
  _labels() {
    return getLabels(this._config.language || "auto", this._hass?.language || "en");
  }

  /** Returns the localized label for the precipitation indicator. */
  _precipLabel() {
    return getPrecipLabel(this._config.language || "auto", this._hass?.language || "en");
  }

  /** Performs a full shadow DOM rebuild of the card. Called on first render or after a condition/theme change. */
  _render() {
    if (!this._hass) return;
    const cfg = this._config;
    const L   = this._labels();
    const compact = !!cfg.compact;

    // Core sensor states
    const zState = this._state(cfg.entity_zambretti);
    const sState = this._state(cfg.entity_sager);
    const s6h    = this._state(cfg.entity_6h);
    const s12h   = this._state(cfg.entity_12h);
    const s24h   = this._state(cfg.entity_24h);
    const precip = Math.max(0, Math.min(100,
      parseInt(this._state(cfg.entity_precip) || "0", 10) || 0));

    // Night / icon selection
    const isNight    = this._attr(cfg.entity_zambretti, "is_night", false);
    const iconKey    = getWeatherIconKey(zState, isNight);
    const condThemeKey = (isNight && (zState === "settled_fine" || zState === "fine_weather"))
      ? "night_clear" : (ZAMBRETTI_CONDITION[zState] || "partlycloudy");

    // Wind — optional; prefer dedicated sensor, fall back to main sensor attribute
    const showWind = cfg.show_wind !== false;
    let windStr = "";
    if (showWind) {
      const windSpeedEntityId = cfg.entity_wind_speed || cfg.entity_zambretti;
      const windSpeedRaw = cfg.entity_wind_speed
        ? this._state(cfg.entity_wind_speed)
        : this._attr(cfg.entity_zambretti, "wind_speed", null);
      // Read the sensor's native unit so we don't double-convert
      const sensorWindUnit = this._attr(windSpeedEntityId, "unit_of_measurement", "m/s");
      const windDeg = this._attr(cfg.entity_zambretti, "wind_degrees", null);
      const windDir = this._attr(cfg.entity_zambretti, "wind_direction", null) || degToCompass(windDeg);
      const windFormatted = formatWind(windSpeedRaw, cfg.wind_unit || "m/s", sensorWindUnit);
      windStr = windFormatted
        ? (windDir ? `${windDir} ${windFormatted}` : windFormatted)
        : windDir || "";
    }

    // Theme
    const autoTheme = cfg.auto_theme !== false;
    let theme = autoTheme ? getTheme(condThemeKey) : {bg: cfg.custom_bg || DEFAULT_THEME.bg};
    theme = { bg: autoTheme ? applyAlpha(theme.bg, cfg.theme_alpha) : theme.bg };

    const icon   = WEATHER_ICONS[iconKey] || WEATHER_ICONS.partlycloudy;
    const zLabel = L[zState] || zState || "—";
    const sLabel = L[sState] || sState || "—";

    const precipLabel = this._precipLabel();

    const showPrecip    = cfg.show_precip    !== false;
    const showForecasts = cfg.show_forecasts !== false;
    const showSager     = cfg.show_sager     !== false;
    const showHistory   = !!cfg.show_history;
    const showTrend     = !!cfg.show_trend;

    const fCells = [
      {label:"6h",  key:s6h},
      {label:"12h", key:s12h},
      {label:"24h", key:s24h},
    ].map(f => `
      <div class="fc">
        <span class="fc-time">${f.label}</span>
        <span class="fc-icon">${WEATHER_ICONS[ZAMBRETTI_CONDITION[f.key] || "partlycloudy"] || ""}</span>
        <span class="fc-lbl">${L[f.key] || f.key || "—"}</span>
      </div>`).join("");

    const gridCols = showPrecip ? "1fr 1fr" : "1fr";

    // Full rebuild
    this.shadowRoot.innerHTML = `
      <style>${this._css(theme, compact, showPrecip)}</style>
      <ha-card style="background:${theme.bg}">
        <div class="grid" style="grid-template-columns:${gridCols}">
          <div class="cell main-cell">
            <div class="main-icon">${icon}</div>
            <div class="main-info">
              <div class="main-label">${zLabel}</div>
              <div class="main-sub">Zambretti</div>
            </div>
          </div>
          ${showPrecip ? `
          <div class="cell precip-cell">
            <div class="precip-title">${precipLabel}</div>
            <div class="precip-widget">${precipWidget(precip)}</div>
          </div>` : ""}
          ${showForecasts ? `
          <div class="cell forecast-row">${fCells}</div>` : ""}
        </div>
        <div class="footer">
          ${windStr ? `<span class="footer-wind">💨 ${windStr}</span>` : ""}
          ${showSager ? `
          <span class="footer-badge">Sager</span>
          <span class="footer-text">${sLabel}</span>` : ""}
        </div>
        ${showTrend ? `
        <div class="trend-section">
          <div class="trend-title"><svg viewBox="0 0 16 16" width="12" height="12" style="vertical-align:-1px;margin-right:4px;opacity:0.7"><circle cx="8" cy="8" r="7" fill="none" stroke="currentColor" stroke-width="1.5"/><line x1="8" y1="4" x2="8" y2="8.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><line x1="8" y1="8.5" x2="11" y2="10.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>Trend</div>
          <div class="trend-timeline-wrap">${forecastTimeline(this._timelineSteps, L, compact)}</div>
        </div>` : ""}
        ${showHistory ? `
        <div class="history-section">
          <div class="history-title"><svg viewBox="0 0 16 16" width="12" height="12" style="vertical-align:-1px;margin-right:4px;opacity:0.7"><polyline points="1,12 5,6 8,9 11,4 15,7" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>24h</div>
          <div class="history-chart-wrap" style="height:${compact ? 150 : 200}px">${historyChart(this._historyPoints, L, compact)}</div>
        </div>` : ""}
      </ha-card>`;

    // Save state for patch
    this._lastIconKey    = iconKey;
    this._lastThemeBg    = theme.bg;
    this._lastPrecip     = precip;
    this._rendered       = true;
  }

  // ── Lightweight patch: update only text/values without touching SVG ──────
  /**
   * Updates only dynamic text nodes and the precip gauge without rebuilding the SVG.
   * Falls back to a full _render() if the icon or theme background has changed.
   */
  _patch() {
    if (!this._hass || !this._rendered) return;
    const cfg = this._config;
    const L   = this._labels();
    const sr  = this.shadowRoot;

    const zState = this._state(cfg.entity_zambretti);
    const sState = this._state(cfg.entity_sager);
    const s6h    = this._state(cfg.entity_6h);
    const s12h   = this._state(cfg.entity_12h);
    const s24h   = this._state(cfg.entity_24h);
    const precip = Math.max(0, Math.min(100,
      parseInt(this._state(cfg.entity_precip) || "0", 10) || 0));

    const isNight      = this._attr(cfg.entity_zambretti, "is_night", false);
    const iconKey      = getWeatherIconKey(zState, isNight);
    const condThemeKey = (isNight && (zState === "settled_fine" || zState === "fine_weather"))
      ? "night_clear" : (ZAMBRETTI_CONDITION[zState] || "partlycloudy");

    // If icon or theme changed — full rebuild (rare: weather condition change)
    const autoTheme = cfg.auto_theme !== false;
    let theme = autoTheme ? getTheme(condThemeKey) : {bg: cfg.custom_bg || DEFAULT_THEME.bg};
    theme = { bg: applyAlpha(theme.bg, cfg.theme_alpha) };
    if (iconKey !== this._lastIconKey || theme.bg !== this._lastThemeBg) {
      this._rendered = false;
      this._render();
      return;
    }

    // Patch labels
    const zLabel = L[zState] || zState || "—";
    const sLabel = L[sState] || sState || "—";

    const mainLabel = sr.querySelector(".main-label");
    if (mainLabel && mainLabel.textContent !== zLabel) mainLabel.textContent = zLabel;

    const footerText = sr.querySelector(".footer-text");
    if (footerText && footerText.textContent !== sLabel) footerText.textContent = sLabel;

    // Patch wind
    const showWind = cfg.show_wind !== false;
    let windStr = "";
    if (showWind) {
      const windSpeedEntityId = cfg.entity_wind_speed || cfg.entity_zambretti;
      const windSpeedRaw = cfg.entity_wind_speed
        ? this._state(cfg.entity_wind_speed)
        : this._attr(cfg.entity_zambretti, "wind_speed", null);
      // Read the sensor's native unit so we don't double-convert
      const sensorWindUnit = this._attr(windSpeedEntityId, "unit_of_measurement", "m/s");
      const windDeg = this._attr(cfg.entity_zambretti, "wind_degrees", null);
      const windDir = this._attr(cfg.entity_zambretti, "wind_direction", null) || degToCompass(windDeg);
      const windFormatted = formatWind(windSpeedRaw, cfg.wind_unit || "m/s", sensorWindUnit);
      windStr = windFormatted
        ? (windDir ? `${windDir} ${windFormatted}` : windFormatted)
        : windDir || "";
    }
    const footerWind = sr.querySelector(".footer-wind");
    if (footerWind) {
      const newWind = windStr ? `💨 ${windStr}` : "";
      if (footerWind.textContent !== newWind) footerWind.textContent = newWind;
      footerWind.style.display = showWind ? "" : "none";
    }

    // Patch forecast labels (not icons — same condition type usually)
    const fcLabels = sr.querySelectorAll(".fc-lbl");
    const fKeys = [s6h, s12h, s24h];
    fcLabels.forEach((el, i) => {
      const lbl = L[fKeys[i]] || fKeys[i] || "—";
      if (el.textContent !== lbl) el.textContent = lbl;
    });

    // Patch precip gauge only if value changed
    if (precip !== this._lastPrecip) {
      const pw = sr.querySelector(".precip-widget");
      if (pw) pw.innerHTML = precipWidget(precip);
      this._lastPrecip = precip;
    }

    // Patch timeline: if current zambretti state changed, append new step and re-render strip
    if (cfg.show_trend && this._timelineSteps) {
      const lastStep = this._timelineSteps[this._timelineSteps.length - 1];
      if (zState && zState !== "unknown" && zState !== "unavailable" &&
          lastStep && lastStep.state !== zState) {
        // Clear isCurrent from previous last step
        this._timelineSteps.forEach(s => { s.isCurrent = false; });
        this._timelineSteps.push({ t: new Date(), state: zState, isCurrent: true });
        // Keep max 8
        if (this._timelineSteps.length > 8) this._timelineSteps.shift();
        this._patchTimeline();
      }
    }

  }

  /**
   * Returns the Shadow DOM CSS string. Scales font/icon sizes for compact mode.
   * @param {object} theme  Current theme object with .bg
   * @param {boolean} compact
   * @param {boolean} showPrecip
   * @returns {string}
   */
  _css(theme, compact, showPrecip = true) {
    const s        = compact ? 0.82 : 1;
    const iconSz   = Math.round(72 * s);
    const mainFsz  = (1.15 * s).toFixed(2);
    const subFsz   = (0.72 * s).toFixed(2);
    const fcIconSz = Math.round(42 * s);
    const footFsz  = (0.80 * s).toFixed(2);
    const precipSz = Math.round(118 * s);
    const precipTSz= (0.75 * s).toFixed(2);
    const pad      = compact ? "12px 10px" : "16px 14px";

    return `
      :host { display:block; }
      ha-card {
        border-radius:22px; overflow:hidden;
        box-shadow:0 8px 36px rgba(0,0,0,0.30);
        font-family:var(--primary-font-family,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif);
        color:#fff; padding:0; border:none;
      }
      .grid {
        display:grid;
        grid-template-columns:1fr 1fr;
        grid-template-rows:auto auto;
      }
      .cell { padding:${pad}; }

      .main-cell {
        grid-column:1; grid-row:1;
        display:flex; align-items:center;
        gap:${compact ? 10 : 13}px;
        border-right:1px solid rgba(255,255,255,0.12);
        border-bottom:1px solid rgba(255,255,255,0.12);
      }
      .main-icon {
        flex:0 0 ${iconSz}px; width:${iconSz}px; height:${iconSz}px;
        filter:drop-shadow(0 2px 8px rgba(0,0,0,0.35));
      }
      .main-icon svg { width:100%; height:100%; }
      .main-info { flex:1; min-width:0; }
      .main-label {
        font-size:${mainFsz}rem; font-weight:700; line-height:1.25;
        letter-spacing:-0.01em; text-shadow:0 1px 6px rgba(0,0,0,0.35);
      }
      .main-sub {
        font-size:${subFsz}rem; font-weight:600;
        letter-spacing:0.08em; text-transform:uppercase;
        opacity:0.58; margin-top:4px;
      }

      .precip-cell {
        grid-column:2; grid-row:1;
        display:flex; flex-direction:column;
        align-items:center; justify-content:center; gap:2px;
        border-bottom:1px solid rgba(255,255,255,0.12);
        padding:${compact ? "10px 6px" : "12px 8px"};
      }
      .precip-title {
        font-size:${precipTSz}rem; font-weight:800;
        letter-spacing:0.12em; text-transform:uppercase;
        text-shadow:0 1px 4px rgba(0,0,0,0.35);
      }
      .precip-widget { width:${precipSz}px; height:${precipSz}px; }

      .forecast-row {
        grid-column:1/-1; grid-row:2;
        display:grid; grid-template-columns:1fr 1fr 1fr; padding:0;
      }
      .fc {
        display:flex; flex-direction:column; align-items:center;
        padding:${compact ? "8px 4px 10px" : "10px 6px 14px"};
        border-right:1px solid rgba(255,255,255,0.09); gap:3px;
      }
      .fc:last-child { border-right:none; }
      .fc-time {
        font-size:${(0.82*s).toFixed(2)}rem; font-weight:800;
        letter-spacing:0.06em; text-transform:uppercase;
        color:rgba(255,255,255,0.95);
        background:rgba(255,255,255,0.15); border-radius:5px; padding:1px 7px;
      }
      .fc-icon {
        width:${fcIconSz}px; height:${fcIconSz}px;
        display:flex; align-items:center; justify-content:center; opacity:0.90;
      }
      .fc-icon svg { width:100%; height:100%; }
      .fc-lbl {
        font-size:${(0.96*s).toFixed(2)}rem; font-weight:700;
        text-align:center; line-height:1.25; color:#fff;
        text-shadow:0 1px 3px rgba(0,0,0,0.3);
      }

      .footer {
        display:flex; align-items:center; gap:10px; flex-wrap:wrap;
        padding:${compact ? "6px 12px 8px" : "8px 16px 10px"};
        background:rgba(0,0,0,0.20);
        border-top:1px solid rgba(255,255,255,0.09);
      }
      .footer-wind {
        font-size:${(0.72*s).toFixed(2)}rem; font-weight:600;
        opacity:0.90; letter-spacing:0.04em; white-space:nowrap;
      }
      .footer-badge {
        font-size:0.62rem; font-weight:700; letter-spacing:0.10em;
        text-transform:uppercase; background:rgba(255,255,255,0.16);
        border:1px solid rgba(255,255,255,0.28); border-radius:5px;
        padding:2px 8px; white-space:nowrap; flex-shrink:0;
      }
      .footer-text {
        font-size:${footFsz}rem; font-weight:500; opacity:0.80; line-height:1.3;
      }

      /* ── Trend timeline section ── */
      .trend-section {
        padding:${compact ? "8px 10px 10px" : "10px 14px 12px"};
        border-top:1px solid rgba(255,255,255,0.09);
        background:rgba(0,0,0,0.12);
      }
      .trend-title {
        font-size:${(0.68*s).toFixed(2)}rem; font-weight:700;
        letter-spacing:0.10em; text-transform:uppercase;
        color:rgba(255,255,255,0.55); margin-bottom:${compact?5:7}px;
      }
      .trend-timeline-wrap { width:100%; overflow-x:auto; }
      .tl-inner {
        display:flex; align-items:center; gap:0;
        min-width:max-content; padding-bottom:2px;
      }
      .tl-step {
        display:flex; flex-direction:column; align-items:center;
        gap:3px; padding:${compact?"3px 6px":"4px 8px"};
        border-radius:10px;
        background:rgba(255,255,255,0.06);
        border:1px solid rgba(255,255,255,0.08);
        transition:background 0.3s;
        min-width:${compact?52:62}px;
      }
      .tl-step.tl-current {
        background:rgba(255,255,255,0.20);
        border-color:rgba(255,255,255,0.35);
        box-shadow:0 0 10px rgba(255,255,255,0.12);
      }
      .tl-icon { flex-shrink:0; }
      .tl-icon svg { width:100%; height:100%; display:block; }
      .tl-lbl {
        font-size:${(0.68*s).toFixed(2)}rem; font-weight:600;
        color:rgba(255,255,255,0.90); text-align:center;
        line-height:1.2; max-width:${compact?52:62}px;
        overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
      }
      .tl-current .tl-lbl { color:#fff; font-weight:700; }
      .tl-time {
        font-size:${(0.60*s).toFixed(2)}rem; font-weight:500;
        color:rgba(255,255,255,0.50); letter-spacing:0.03em;
      }
      .tl-current .tl-time { color:rgba(255,255,255,0.80); }
      .tl-arrow {
        font-size:${compact?"1.1rem":"1.3rem"}; color:rgba(255,255,255,0.30);
        padding:0 ${compact?3:4}px; flex-shrink:0; user-select:none;
        align-self:center; margin-bottom:14px;
      }
      .tl-empty {
        font-size:0.75rem; color:rgba(255,255,255,0.35);
        font-style:italic; padding:8px 0;
      }

      /* ── History chart section ── */
      .history-section {
        padding:${compact ? "8px 0 0" : "10px 0 0"};
        border-top:1px solid rgba(255,255,255,0.09);
        background:rgba(0,0,0,0.15);
        overflow:visible;
      }
      .history-title {
        font-size:${(0.68*s).toFixed(2)}rem; font-weight:700;
        letter-spacing:0.10em; text-transform:uppercase;
        color:rgba(255,255,255,0.55);
        margin-bottom:${compact?2:4}px;
        padding:0 ${compact?"10px":"14px"};
      }
      .history-chart-wrap {
        width:100%;
        /* height is set inline per render to allow live updates */
      }
      .hchart-empty {
        display:flex; align-items:center; justify-content:center;
        height:${compact ? 100 : 130}px;
        font-size:0.80rem; color:rgba(255,255,255,0.35);
        font-style:italic;
      }
    `;
  }

  getCardSize() {
    let sz = 3;
    if (this._config.show_trend)   sz += 1;
    if (this._config.show_history) sz += 2;
    return sz;
  }
}

// ── Visual editor ─────────────────────────────────────────────────────────
class ZambrettiWeatherCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode:"open"});
    this._config = {};
  }

  setConfig(config) { this._config = {...config}; this._render(); }
  set hass(h) {
    this._hass = h;
    this._syncPickers();
    if (this.shadowRoot?.querySelector("#wind-entity-picker")
        && !this.shadowRoot.querySelector("ha-entity-picker")) {
      this._setupWindEntityPicker();
    }
  }

  _applyBgToCard(bg) {
    window.dispatchEvent(new CustomEvent("zambretti-bg-preview", {detail:{bg}}));
  }

  _fire(config) {
    this.dispatchEvent(new CustomEvent("config-changed",
      {detail:{config}, bubbles:true, composed:true}));
  }

  _render() {
    const c = this._config;
    const lang = c.language || "auto";
    const hLang = this._hass?.language || "en";
    const t = getEditorStrings(lang, hLang);

    const autoThemeOn  = c.auto_theme !== false;
    const themeAlpha   = c.theme_alpha ?? 100;
    const showWindOn   = c.show_wind !== false;
    const customBg     = c.custom_bg || "linear-gradient(135deg,#1565C0 0%,#1976D2 100%)";
    const isSolidColor = /^#[0-9a-fA-F]{3,8}$/.test(customBg.trim());
    const colorInputVal= isSolidColor ? customBg.trim() : "#1565C0";
    const windUnit     = c.wind_unit || "m/s";

    this.shadowRoot.innerHTML = `
      <style>
        :host{display:block;padding:4px 0 8px}
        .section-title{font-size:0.70rem;font-weight:700;letter-spacing:.10em;
          text-transform:uppercase;color:var(--secondary-text-color);
          margin:16px 0 6px;padding-left:2px}
        .field-row{margin-bottom:10px}
        .field-row label{display:block;font-size:0.82rem;
          color:var(--secondary-text-color);margin-bottom:4px}
        .field-hint{font-size:0.72rem;color:var(--secondary-text-color);margin-top:2px}
        select,input[type=text]{
          width:100%;padding:9px 12px;border-radius:8px;box-sizing:border-box;
          border:1px solid var(--divider-color,rgba(255,255,255,0.15));
          background:var(--card-background-color,#1e1e1e);
          color:var(--primary-text-color,#fff);font-size:0.92rem;cursor:pointer}
        .row{display:flex;align-items:center;justify-content:space-between;
          padding:10px 2px;border-bottom:1px solid var(--divider-color,rgba(0,0,0,.10))}
        .row:last-child{border-bottom:none}
        .row-label{font-size:0.95rem;color:var(--primary-text-color)}
        .row-hint{font-size:0.75rem;color:var(--secondary-text-color);margin-top:2px}
        .custom-bg-row{padding:10px 2px 12px;
          border-bottom:1px solid var(--divider-color,rgba(0,0,0,.10))}
        .bg-inputs{display:flex;gap:8px;align-items:center;margin-top:6px}
        .bg-color-swatch{width:36px;height:36px;border-radius:8px;
          border:2px solid rgba(255,255,255,0.2);cursor:pointer;
          flex-shrink:0;overflow:hidden;position:relative}
        .bg-color-swatch input[type=color]{position:absolute;inset:0;
          width:100%;height:100%;border:none;padding:0;cursor:pointer;opacity:0}
        .bg-color-preview{position:absolute;inset:0;border-radius:6px;pointer-events:none}
        .bg-text-input{flex:1;padding:8px 10px;border-radius:8px;
          border:1px solid var(--divider-color,rgba(255,255,255,0.15));
          background:var(--card-background-color,#1e1e1e);
          color:var(--primary-text-color,#fff);font-size:0.85rem;font-family:monospace}
      </style>

      <div class="section-title">${t.appearance}</div>

      <div class="field-row">
        <label>${t.language}</label>
        <select id="sel-lang">
          ${LANG_OPTIONS.map(([value, label]) => {
            const text = value === "auto" ? t.langAuto : label;
            const selected = lang === value ? "selected" : "";
            return `<option value="${value}" ${selected}>${text}</option>`;
          }).join("")}
        </select>
      </div>

      ${this._toggle("sw-wind", t.showWind, t.showWindH, showWindOn)}

      ${showWindOn ? `
      <div class="field-row">
        <label>${t.windEntity}</label>
        <div id="wind-entity-picker"></div>
        <div class="field-hint">${t.windEntityH}</div>
      </div>

      <div class="field-row">
        <label>${t.windUnit}</label>
        <select id="sel-wind-unit">
          <option value="m/s"  ${windUnit==="m/s" ?"selected":""}>m/s</option>
          <option value="km/h" ${windUnit==="km/h"?"selected":""}>km/h</option>
          <option value="mph"  ${windUnit==="mph" ?"selected":""}>mph</option>
          <option value="kn"   ${windUnit==="kn"  ?"selected":""}>kn</option>
          <option value="kn"   ${windUnit==="kn"  ?"selected":""}>kn</option>
        </select>
      </div>` : ""}

      ${this._toggle("sw-auto-theme", t.autoTheme, t.autoThemeH, autoThemeOn)}
      ${autoThemeOn ? `
      <div class="custom-bg-row">
        <div class="row-label">${t.themeAlpha || "Background opacity (Alpha)"}</div>
        <div class="row-hint">${t.themeAlphaH || "Adjust the transparency of the auto theme background (0–100%)"}</div>
        <div style="display:flex; align-items:center; gap:10px; margin-top:8px;">
          <input type="range" id="theme-alpha-slider" min="0" max="100" value="${themeAlpha}" style="flex:1; cursor:pointer;">
          <span id="theme-alpha-lbl" style="font-size:0.85rem; font-family:monospace; width:40px; text-align:right;">${themeAlpha}%</span>
        </div>
      </div>` : ""}
      ${!autoThemeOn ? `
      <div class="custom-bg-row">
        <div class="row-label">${t.customBg}</div>
        <div class="row-hint">${t.customBgH}</div>
        <div class="bg-inputs">
          <div class="bg-color-swatch">
            <div class="bg-color-preview" id="bg-preview" style="background:${customBg}"></div>
            <input type="color" id="bg-color-picker" value="${colorInputVal}">
          </div>
          <input type="text" class="bg-text-input" id="bg-text"
            value="${customBg.replace(/"/g,'&quot;')}"
            placeholder="linear-gradient(...) or #hex" spellcheck="false">
        </div>
      </div>` : ""}
      ${this._toggle("sw-sager",     t.showSager,     t.showSagerH,    c.show_sager     !== false)}
      ${this._toggle("sw-precip",    t.showPrecip,    t.showPrecipH,   c.show_precip    !== false)}
      ${this._toggle("sw-forecasts", t.showForecasts, t.showForecastH, c.show_forecasts !== false)}
      ${this._toggle("sw-trend",     t.showTrend    || "Show forecast trend timeline", t.showTrendH    || "Horizontal strip of past Zambretti states with icons and times", !!c.show_trend)}
      ${this._toggle("sw-history",   t.showHistory  || "Show 24h history chart",      t.showHistoryH  || "Pressure & precipitation chart for the last 24 hours",            !!c.show_history)}
    `;

    // Event listeners
    this.shadowRoot.querySelector("#sel-lang").addEventListener("change", e => {
      this._fire({...this._config, language: e.target.value});
    });
    const windUnitSel = this.shadowRoot.querySelector("#sel-wind-unit");
    if (windUnitSel) {
      windUnitSel.addEventListener("change", e => {
        this._fire({...this._config, wind_unit: e.target.value});
      });
    }
    this._setupWindEntityPicker();
    this.shadowRoot.querySelectorAll("ha-switch[data-key]").forEach(el => {
      el.addEventListener("change", () => {
        this._fire({...this._config, [el.dataset.key]: el.checked});
      });
    });

    const alphaSlider = this.shadowRoot.querySelector("#theme-alpha-slider");
    const alphaLbl    = this.shadowRoot.querySelector("#theme-alpha-lbl");
    if (alphaSlider) {
      alphaSlider.addEventListener("input", e => {
        if (alphaLbl) alphaLbl.textContent = `${e.target.value}%`;
      });
      alphaSlider.addEventListener("change", e => {
        this._fire({...this._config, theme_alpha: parseInt(e.target.value, 10)});
      });
    }

    const bgText    = this.shadowRoot.querySelector("#bg-text");
    const bgPicker  = this.shadowRoot.querySelector("#bg-color-picker");
    const bgPreview = this.shadowRoot.querySelector("#bg-preview");
    if (bgText) {
      bgText.addEventListener("change", e => {
        const val = e.target.value.trim();
        if (bgPreview) bgPreview.style.background = val;
        this._fire({...this._config, custom_bg: val});
      });
    }
    if (bgPicker) {
      bgPicker.addEventListener("input", e => {
        const val = e.target.value;
        if (bgPreview) bgPreview.style.background = val;
        if (bgText)    bgText.value = val;
        this._config = {...this._config, custom_bg: val};
        this._applyBgToCard(val);
      });
      bgPicker.addEventListener("change", e => {
        const val = e.target.value;
        if (bgPreview) bgPreview.style.background = val;
        if (bgText)    bgText.value = val;
        this._fire({...this._config, custom_bg: val});
      });
    }
  }

  _setupWindEntityPicker() {
    const container = this.shadowRoot?.querySelector("#wind-entity-picker");
    if (!container || !this._hass) return;

    container.innerHTML = "";
    const picker = document.createElement("ha-entity-picker");
    picker.hass = this._hass;
    picker.value = this._config.entity_wind_speed || "";
    picker.includeDomains = ["sensor"];
    picker.includeDeviceClasses = ["wind_speed"];
    picker.allowCustomEntity = true;
    const onPickerChange = (e) => {
      const val = e.detail?.value ?? "";
      this._fire({...this._config, entity_wind_speed: val || ""});
    };
    picker.addEventListener("value-changed", onPickerChange);
    picker.addEventListener("changed", onPickerChange);
    container.appendChild(picker);
  }

  _syncPickers() {
    this.shadowRoot?.querySelectorAll("ha-entity-picker").forEach(p => {
      if (this._hass) p.hass = this._hass;
    });
  }

  _toggle(id, label, hint, checked) {
    const keyMap = {
      "sw-wind":      "show_wind",
      "sw-sager":     "show_sager",
      "sw-precip":    "show_precip",
      "sw-forecasts": "show_forecasts",
      "sw-auto-theme":"auto_theme",
      "sw-trend":     "show_trend",
      "sw-history":   "show_history",
    };
    return `<div class="row">
      <div>
        <div class="row-label">${label}</div>
        <div class="row-hint">${hint}</div>
      </div>
      <ha-switch data-key="${keyMap[id]}" ${checked?"checked":""}></ha-switch>
    </div>`;
  }
}

// ── Register ──────────────────────────────────────────────────────────────
customElements.define("zambretti-weather-card", ZambrettiWeatherCard);
customElements.define("zambretti-weather-card-editor", ZambrettiWeatherCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type:             "zambretti-weather-card",
  name:             "Zambretti & Sager Weather Card",
  description:      "iOS-style weather widget — Zambretti & Sager forecasts",
  preview:          true,
  documentationURL: "https://github.com/ziffmafiya/zambretti_sager",
});
