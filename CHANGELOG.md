# Changelog

## [1.9.69] — 2026-07-06

### Fixed
- **Wind direction sensor not visible in config flow** — removed `device_class` filter from the wind direction and wind speed entity selectors. Previously only sensors with `device_class: wind_direction` / `wind_speed` were shown, hiding sensors from weather station integrations that don't assign those device classes. Now any `sensor` domain entity can be selected.

---

## [1.9.63] — 2026-07-01

### Fixed
- **Precip spike on chart** — added IQR outlier filter for precipitation series (same as pressure). Stale high-value entries from earlier in the day no longer cause a spike to 100%.
- **Precip line invisible on light/warm themes** — changed precip line and fill from teal `#80CBC4` to `rgba(255,255,255,0.70)` (white semi-transparent). Now readable on any background color (orange sunny, blue cloudy, dark night).
- **Trend: near-duplicate timestamps** — added 30-minute minimum gap between timeline steps. Entries within 30 min of each other (startup noise after HA restart) are merged into one.

### Changed
- **Section header icons** — replaced unicode emoji (🕐 📈) with inline SVG icons. Renders consistently on all platforms (Windows, Android, iOS, Linux).

---

## [1.9.62] — 2026-07-01

### Fixed
- **Pressure spike on chart** — IQR filter removes outlier pressure readings (e.g. from sea-level correction being toggled).
- **Trend showing times going backward** — reverted to transition-based timeline (honest: shows real state changes).

---

## [1.9.61] — 2026-07-01

### Fixed
- **Trend timeline showing only 1–2 steps** — root cause: HA Recorder only writes Zambretti sensor to history on state change. Added `_attr_force_update = True` to all sensor classes so HA writes every 5-minute coordinator cycle.

### Changed
- Timeline shows all distinct state transitions (deduplicated) instead of artificial 6h-boundary snapshots.

---

## [1.9.57] — 2026-07-01

### Fixed
- **Pressure chart line flat/missing** — pressure is now fetched directly from the raw barometric sensor (e.g. BMP280) whose entity_id is exposed via `pressure_sensor` attribute on the Zambretti sensor. Dense 5-min recorder data replaces the sparse attribute-based approach.

### Added
- `pressure_sensor` attribute added to `ZambrettiSensor.extra_state_attributes` — automatically set to `coordinator.pressure_id` (the sensor chosen at setup time). No user configuration required.

---


### Fixed
- **History chart — pressure line missing** — the WS history request used `minimal_response: true` which strips all entity attributes. Since pressure lives in the `pressure_hpa` attribute of the Zambretti sensor, it was never being read. Changed to `minimal_response: false` so attributes are included.
- **History chart — precipitation line flat** — `PrecipitationProbability` only writes to recorder on state change. If the value was stable all day, only one point was stored and displayed as a flat line. Added forward-fill across the full 24h time bucket array so the line tracks the last known value continuously.
- **Removed unnecessary "Pressure sensor" picker** — pressure is already available in `sensor.zambretti_forecast` attributes; no extra entity is needed.

---

## [1.9.53] — 2026-07-01

### Added
- **Forecast trend timeline** (`show_trend`) — optional horizontal strip showing the last 8 distinct Zambretti forecast states with weather icons and timestamps. Placed between the footer and the history chart. Each step shows the icon, first word of the forecast label, and time. The current state is highlighted. Updates live when the forecast changes without a full card rebuild.

---

## [1.9.52] — 2026-07-01

### Added
- **24h history chart** (`show_history`) — optional SVG line chart embedded directly in the card. Shows pressure (hPa, blue line, left axis) and precipitation probability (%, teal line, right axis) over the last 24 hours. Data is fetched from HA Recorder via WebSocket and cached for 5 minutes. Renders cleanly in both normal and compact modes.

---

## [1.9.51] — 2026-06-30

### Fixed
- **Wind speed unit conversion** — the card no longer assumes the wind sensor always reports in m/s. `formatWind()` now reads the sensor's native `unit_of_measurement` attribute from Home Assistant and converts correctly from any source unit (m/s, km/h, mph) to the chosen display unit. Previously, selecting km/h as the display unit always multiplied the raw value by 3.6 even when the sensor (e.g. Ecowitt via HA integration) was already reporting in km/h, resulting in values ~3.6× too high.

---

## [1.9.11] — 2026-06-21

### Added
- **17 new languages** — German, Spanish, Italian, Polish, Chinese (Simplified & Traditional), Dutch, Portuguese, Ukrainian, Japanese, Korean, Czech, Swedish, Danish, Norwegian, Hungarian, Turkish
- Full translations for config flow, options flow, and all 38 sensor states
- Card language selector expanded to 20 languages with auto-detect from Home Assistant

---

## [1.9.10] — 2026-06-21

### Added
- **Show wind toggle** — enable or disable wind display in the card footer from the visual editor
- **Wind speed entity picker** — when wind display is enabled, HA suggests `wind_speed` sensors via `ha-entity-picker` (optional; falls back to main sensor attribute)
- **GitHub Wiki** — English documentation (installation, configuration, sensors, card, algorithms, troubleshooting, roadmap)

---

## [1.9.8] — 2026-06-21

### Fixed
- **SVG animations no longer jitter** — root cause: `shadowRoot.innerHTML` was rebuilt on every `hass` update (every few seconds in HA), destroying and recreating all SVG `<animate>` elements and restarting them from frame 0. Fixed by splitting render into two paths:
  - **Full render** — only on first load or when the weather condition/theme actually changes
  - **Patch** — all subsequent `hass` updates update only text nodes, precip gauge, and sparkline via targeted DOM mutations, leaving SVG animations completely untouched

---

## [1.9.7] — 2026-06-21

### Fixed
- **Sun animation jitter** — disc and rays are now wrapped in a single `<g>` with one `animateTransform rotate calcMode="linear"`, so the whole icon rotates smoothly without stuttering

### Added
- **Wind speed sensor support** — optional dedicated wind speed sensor (`entity_wind_speed`) selectable in card settings; falls back to the `wind_speed` attribute of the main sensor when not set
- **Wind unit selector** — choose `m/s`, `km/h`, or `mph` in card settings; automatic conversion applied
- **Animated weather icons (full rework)**:
  - ☁️ Cloudy — clouds drift horizontally with `calcMode="linear"` (no jitter)
  - 🌧 Rainy / Pouring — drops rendered as animated `<line>` elements (y1/y2 + opacity), much more realistic
  - ❄️ Snowy — snowflakes fall top-to-bottom with `calcMode="linear"`, staggered timing
  - ⚡ Lightning — double-flash pattern (`1;0.2;1;0.2;1`)
  - 💨 Windy — three sinusoidal wave paths animate in sync with `calcMode="linear"`
  - 🌤 Partly cloudy — sun rotates independently, cloud drifts separately

---

## [1.9.6] — 2026-06-21

### Added
- **🇫🇷 French translation** — full `fr.json` translation contributed by [@gael1980](https://github.com/gael1980); config flow, options flow, and all sensor state labels are now available in French

---

## [1.9.5] — 2026-06-21

### Fixed
- **Conflict when configuring multiple instances** — removed manual `self.entity_id` assignments from all 6 sensor classes; HA now auto-generates entity IDs from unique IDs
- **Pressure watcher subscription leak on unload** — `_stop_pressure_watcher()` is now called in `async_unload_entry` to prevent stale callbacks and memory leaks
- **Dead code in precipitation probability** — humidity `<= 30%` branch was never reached because `<= 40%` was checked first; corrected evaluation order
- **History pressure retrieval** — now searches within a ±15-minute window and picks the nearest state to the target time instead of the oldest state in the range
- **Sea-level warning not reset** — `_sea_level_warning_logged` flag is now cleared when the pressure sensor changes in options
- **Missing `humidity_sensor` in `strings.json`** — added the field to config and options flows so it appears in HA UI for non-English languages
- **Division before guard in sea-level formula** — `factor <= 0` check now protects the exponentiation step as intended

---

## [1.9.4] — 2026-06-16

### Fixed
- **hassfest validation errors** — two issues reported by the HA CI pipeline:
  - Added `lovelace` to `dependencies` in `manifest.json` (required when using the lovelace/frontend card registration)
  - Added `CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)` in `__init__.py` (required when `async_setup` is defined but the integration has no YAML configuration)

---

## [1.9.3] — 2026-06-16

### Fixed
- **Card language setting now translates forecast text** — previously, sensors had `_attr_translation_key` set, which caused HA to translate state values via `translations/en.json` before the card reads them. So `hass.states[...].state` returned already-translated text like `"Settled Fine"` instead of the raw key `"settled_fine"`, making the card unable to look it up in `LABELS_RU`. Removed `_attr_translation_key` from all forecast sensors — they now always return raw keys, and the card handles all translation itself based on the card's language setting.

---

## [1.9.2] — 2026-06-16

### Fixed
- **Sensors stay unavailable after HA restart** — root cause was that HA loads integrations before all sensor states are restored. The coordinator now subscribes to state-change events on the pressure sensor and triggers a refresh the moment it becomes available, instead of waiting up to 5 minutes for the next scheduled poll.

---

## [1.9.1] — 2026-06-16

### Fixed
- **Sensors unavailable after fresh install** — all sensors now show a value immediately after setup, without waiting for pressure history to accumulate. When history is not yet available, delta is treated as 0 (steady trend). Extended forecasts (6h/12h/24h) use the best available history window and scale accordingly.

---

## [1.9.0] — 2026-06-16

### Changed
- **Sunny condition** — warm orange gradient (`#C65A00 → #F2820A → #FFAA33 → #FFD580`) instead of blue, matching iOS Weather app style
- **Card editor** — removed Compact mode toggle (simplified UI)

### Added
- **Auto theme toggle** — new switch in card settings; when enabled (default) the background follows the weather condition automatically; when disabled the user can set a custom background
- **Custom background picker** — color swatch opens a native color picker with live preview; text field accepts any CSS value (`#hex`, `linear-gradient(...)`, etc.)
- **Live preview** — background color updates the card in real time while the picker is open, without closing it (uses `window` custom event bridge across shadow DOM)

---

## [1.7.1] — 2026-06-15

### Fixed
- **Duplicate recorder queries** — all sensors share one `DataUpdateCoordinator` update cycle
- **Entity unique IDs** — based on config entry ID, stable when pressure sensor changes in options
- **History parsing** — handles recorder `State` objects and compressed dict responses
- **Optional sensors** — empty wind/temperature selections are cleared instead of saved as blank strings

### Changed
- Sensors use `CoordinatorEntity` and `_attr_native_value` (modern Home Assistant pattern)
- Wind and temperature selectors filter by `wind_direction` and `temperature` device classes
- Options flow uses the current `config_entry` API

---

## [1.7.0] — 2026-06-15

### Fixed
- **Sager forecast** — now uses pressure trend (3 h) and wind direction when available
- **Pressure units** — automatic conversion to hPa (Pa, inHg, mmHg, etc.)
- **Sea level correction** — skips correction when sensor already reports sea level pressure
- **Unavailable state** — sensors mark themselves unavailable when pressure data is missing
- **Extended forecasts** — extrapolated delta is used consistently for 6h/12h/24h Zambretti forecasts
- **Coordinates (0, 0)** — no longer treated as missing location
- **Duplicate integrations** — config flow aborts if the same pressure sensor is already configured
- **Elevation API** — uses Home Assistant shared aiohttp session instead of creating a new one

### Changed
- Pressure sensor selector in config flow filters by `atmospheric_pressure` device class

---

## [1.4.0] — 2026-06-15

### Added
- **Localization support** — the config flow and options UI now automatically use the language set in your Home Assistant profile. English (`en`) and Russian (`ru`) are fully supported out of the box. Any other language falls back to English.
  - Added `translations/en.json`
  - Added `translations/ru.json`
  - Updated `strings.json` with `abort` messages

### Removed
- **Zambretti Barometer Card** — the built-in Lovelace card has been removed from the integration.
  - Deleted `custom_components/zambretti_sager/zambretti-barometer-card.js`
  - Deleted `www/zambretti-barometer-card.js`
  - Deleted `www/README.md`
  - Removed `async_setup` function and card HTTP serving code from `__init__.py`
  - Removed `frontend` and `http` from `manifest.json` dependencies

### Changed
- `manifest.json` — bumped version to `1.4.0`, cleaned up dependencies
- `README.md` — updated version badge, rewrote changelog section, removed card documentation, added localization section
- `info.md` — updated description to reflect v1.4.0 changes

---

## [1.3.0]

### Added
- Built-in Zambretti Barometer Card (bundled with the integration)
- Automatic card registration via `add_extra_js_url`

---

## [1.2.0]

### Added
- Sea level pressure correction using Open-Elevation API
- Interactive map selector in config flow for location/altitude detection
- Temperature sensor support for precise pressure correction

---

## [1.1.0]

### Added
- Extended forecasts: Zambretti 6h, 12h, 24h sensors
- Precipitation Probability sensor (0–100%)
- Options flow — reconfigure sensors without reinstalling

---

## [1.0.0]

### Added
- Initial release
- Zambretti Forecast sensor (32 states)
- Sager Forecast sensor
- Config flow with pressure and wind sensor selection
