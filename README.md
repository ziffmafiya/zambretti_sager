# Zambretti & Sager Weather Forecaster

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
![Version](https://img.shields.io/badge/version-1.9.73-blue.svg)

A Home Assistant custom integration that provides weather forecasting using the classic Zambretti and Sager algorithms based on barometric pressure trends.

<p align="center">
  <img src="https://raw.githubusercontent.com/ziffmafiya/zambretti_sager/main/logo.png" alt="Zambretti & Sager Logo" width="400">
</p>

---

## 🚀 Quick Install

Click the button below to install directly via HACS:

[![Install with HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ziffmafiya&repository=zambretti_sager&category=integration)

Or open HACS → **Integrations** → **Custom repositories** → add `https://github.com/ziffmafiya/zambretti_sager` (category: Integration).

After installation, click here to start setup:

[![Open in Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=zambretti_sager)


---

## Features

<p align="center">
  <img src="https://raw.githubusercontent.com/ziffmafiya/zambretti_sager/main/card-screenshot.png" alt="Zambretti Weather Card" width="400">
</p>

The integration includes a built-in **Lovelace card** that displays the current forecast with animated weather icons, night mode, wind info, pressure sparkline, and a 24-hour history chart. It is registered automatically — no manual resource setup needed.

- **Zambretti Forecast** — 32 different weather predictions based on pressure trends over 3 hours
- **Sager Forecast** — weather prediction based on current pressure and wind direction
- **Extended Forecasts** — predictions for 6, 12, and 24 hours ahead
- **Precipitation Probability** — percentage chance of rain based on pressure trends
- **Sea Level Pressure Correction** — automatic altitude-based pressure correction for accurate forecasts
- **Interactive Map Selection** — choose your location on a map for automatic altitude detection
- **Temperature Compensation** — uses temperature sensor for precise pressure correction
- **Wind Speed & Direction** — optional wind speed sensor with visualization in the card
- **Night Mode** — automatic moon/stars icon and dark theme when sun is down
- **Pressure Sparkline** — 24-hour pressure history chart inside the card
- **Animated Weather Icons** — drifting clouds, falling snow, waving wind lines
- **Localization** — 20 languages: English, German, Spanish, French, Italian, Dutch, Polish, Portuguese, Russian, Ukrainian, Chinese (Simplified & Traditional), Japanese, Korean, Czech, Swedish, Danish, Norwegian, Hungarian, Turkish

## Installation

### ⚡ One-Click HACS Install

[![Install with HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ziffmafiya&repository=zambretti_sager&category=integration)

Then configure:

[![Open in Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=zambretti_sager)

### Manual HACS Installation

1. Open HACS → **Integrations**
2. Click the three dots → **Custom repositories**
3. Add `https://github.com/ziffmafiya/zambretti_sager` with category **Integration**
4. Click **Install**
5. Restart Home Assistant

### Manual Installation

1. Copy `custom_components/zambretti_sager` to your HA `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **Zambretti and Sager**
4. Follow the setup wizard:
   - Select your **pressure sensor** (absolute or sea level pressure)
   - Select your **wind direction sensor**
   - (Optional) Select your **temperature sensor** for accurate sea level correction
   - Enable **sea level pressure correction** if using an absolute pressure sensor
   - Click on the **map** to select your weather station location
5. Click **Submit**

## Sensors

The integration creates six sensors grouped under a single device:

| Sensor | Description |
|---|---|
| **Zambretti Forecast** | Current detailed weather prediction (32 states) |
| **Sager Forecast** | Simplified weather prediction |
| **Zambretti Forecast 6h** | Prediction for 6 hours ahead |
| **Zambretti Forecast 12h** | Prediction for 12 hours ahead |
| **Zambretti Forecast 24h** | Prediction for 24 hours ahead |
| **Precipitation Probability** | Chance of rain, 0–100% |

## How It Works

### Zambretti Algorithm

Analyzes barometric pressure trends over the past 3 hours:

- **Falling** (≤ −1.6 hPa) — worsening weather
- **Steady** (−1.6 to +1.6 hPa) — stable conditions
- **Rising** (≥ +1.6 hPa) — improving weather

The result maps to one of 32 classical weather descriptions.

### Sager Algorithm

Uses current pressure and wind direction:

- **> 1020 hPa** — Fair, No Change
- **< 1005 hPa** — Unsettled, Rain
- **1005–1020 hPa** — Variable

### Sea Level Pressure Correction

When enabled, the integration fetches your altitude from Open-Elevation API using the map location, then applies the barometric formula:

```
P_sea = P_abs / (1 − (0.0065 × h) / (T + 0.0065 × h + 273.15))^5.257
```

## Localization

The setup UI and Lovelace card are available in **20 languages**:

🇬🇧 English · 🇩🇪 Deutsch · 🇪🇸 Español · 🇫🇷 Français · 🇮🇹 Italiano · 🇳🇱 Nederlands · 🇵🇱 Polski · 🇵🇹 Português · 🇷🇺 Русский · 🇺🇦 Українська · 🇨🇳 简体中文 · 🇹🇼 繁體中文 · 🇯🇵 日本語 · 🇰🇷 한국어 · 🇨🇿 Čeština · 🇸🇪 Svenska · 🇩🇰 Dansk · 🇳🇴 Norsk · 🇭🇺 Magyar · 🇹🇷 Türkçe

To change the language, go to your **HA profile → Language**, or set the card language in the visual editor.

## Requirements

- Home Assistant 2024.1.0 or newer
- A barometric pressure sensor (hPa)
- A wind direction sensor (degrees, optional but recommended for Sager)
- A temperature sensor (optional, for sea level correction)

## Troubleshooting

**Forecast shows "Calculating..." or "Initializing..."**
Wait a few minutes — the integration needs pressure history to calculate trends. Make sure the pressure sensor is providing valid data.

**Inaccurate forecasts**
Enable sea level correction if you're above sea level, verify the map location, and make sure the temperature sensor is working.

**Altitude not detected**
The integration uses the [Open-Elevation API](https://open-elevation.com). Check that your Home Assistant instance has internet access. Altitude is fetched once at startup.

## Credits

- **Zambretti Algorithm** — developed by Negretti and Zambra in the early 1900s
- **Sager Algorithm** — developed by meteorologist Raymond Sager
- **Integration Author** — Maksym ([@ziffmafiya](https://github.com/ziffmafiya))

## License

MIT License — see [LICENSE](LICENSE) for details.

## Support

Found a bug or have a suggestion? [Open an issue](https://github.com/ziffmafiya/zambretti_sager/issues) on GitHub.
