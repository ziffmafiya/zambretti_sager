# Sensors

The integration creates **6 sensors** grouped under a single **Weather Forecaster** device.

---

## Entity list

| Sensor / Entity | Entity ID (example) | Description |
|---|---|---|
| **Weather Station** | `weather.weather_station` | Native Home Assistant weather entity with forecasts |
| **Zambretti Forecast** | `sensor.zambretti_forecast` | Current detailed forecast (1 of 32 states) |
| **Sager Forecast** | `sensor.sager_forecast` | Simplified forecast from pressure and wind |
| **Zambretti Forecast 6h** | `sensor.zambretti_forecast_6h` | Forecast 6 hours ahead |
| **Zambretti Forecast 12h** | `sensor.zambretti_forecast_12h` | Forecast 12 hours ahead |
| **Zambretti Forecast 24h** | `sensor.zambretti_forecast_24h` | Forecast 24 hours ahead |
| **Precipitation Probability** | `sensor.precipitation_probability` | Chance of precipitation, 0–100% |
| **Last Update** | `sensor.last_update` | Timestamp of the last successful coordinator refresh |

> Exact entity IDs depend on your HA configuration. Look for the **Weather Forecaster** device in **Settings → Devices & Services**.

---

## Native Weather Entity (`weather.weather_station`)

The integration exposes a standard Home Assistant `weather` platform entity.

- **Supported Features**: `FORECAST_HOURLY`, `FORECAST_DAILY` (`WeatherEntityFeature`)
- **Supported Service**: Works with the native `weather.get_forecasts` service call in Home Assistant.
- **Attributes**:
  - `condition` — mapped HA weather state (`sunny`, `partlycloudy`, `rainy`, `lightning-rainy`, etc.)
  - `temperature` / `pressure` / `humidity` — current metrics
  - `wind_speed` — automatically converted from input sensor units (`km/h`, `mph`, `knots`) to native `m/s`
  - `wind_bearing` — wind direction in degrees (0–360°) or converted compass direction
  - `forecast` — 6h, 12h, and 24h forecast objects containing predicted pressure and conditions

---

## Main sensor attributes

The **Zambretti Forecast** sensor exposes additional attributes:

| Attribute | Description |
|---|---|
| `pressure` | Current pressure (hPa) |
| `pressure_trend` | Trend: `falling`, `steady`, `rising` |
| `pressure_delta` | Pressure change over ~3 h (hPa) |
| `wind_direction` | Wind direction (N, NE, E, …) |
| `wind_speed` | Wind speed (if sensor configured) |
| `altitude` | Altitude above sea level (m) |
| `sager_forecast` | Sager forecast key |
| `precipitation_probability` | Precipitation probability (%) |

---

## 32 Zambretti states

States are returned as **translation keys** (e.g. `settled_fine`, `stormy_much_rain`). The card and UI translate them to the selected language.

### Falling pressure (1–9)

| # | Key | Label |
|---|---|---|
| 1 | `settled_fine` | Settled Fine |
| 2 | `fine_weather` | Fine Weather |
| 3 | `fine_becoming_less_settled` | Fine, Less Settled |
| 4 | `fairly_fine_showery_later` | Fine, Showers Later |
| 5 | `showery_becoming_more_unsettled` | Showery, Worsening |
| 6 | `unsettled_rain_later` | Unsettled, Rain Later |
| 7 | `rain_at_times_worse_later` | Rain, Worse Later |
| 8 | `rain_at_times_becoming_very_unsettled` | Rain, Very Unsettled |
| 9 | `very_unsettled_rain` | Very Unsettled, Rain |

### Steady pressure (10–19)

| # | Key | Label |
|---|---|---|
| 10 | `settled_fine` | Settled Fine |
| 11 | `fine_weather` | Fine Weather |
| 12 | `fine_possibly_showers` | Fine, Possibly Showers |
| 13 | `fairly_fine_showers_likely` | Fine, Showers Likely |
| 14 | `showery_bright_intervals` | Showery, Bright Intervals |
| 15 | `changeable_some_rain` | Changeable, Some Rain |
| 16 | `unsettled_rain_at_times` | Unsettled, Rain at Times |
| 17 | `rain_at_frequent_intervals` | Frequent Rain |
| 18 | `very_unsettled_rain` | Very Unsettled, Rain |
| 19 | `stormy_much_rain` | Stormy, Heavy Rain |

### Rising pressure (20–32)

| # | Key | Label |
|---|---|---|
| 20 | `settled_fine` | Settled Fine |
| 21 | `fine_weather` | Fine Weather |
| 22 | `becoming_fine` | Becoming Fine |
| 23 | `fairly_fine_improving` | Fine, Improving |
| 24 | `fairly_fine_possibly_showers_early` | Fine, Early Showers |
| 25 | `showery_early_improving` | Early Showers, Improving |
| 26 | `changeable_mending` | Changeable, Mending |
| 27 | `rather_unsettled_clearing_later` | Unsettled, Clearing Later |
| 28 | `unsettled_probably_improving` | Unsettled, Improving |
| 29 | `unsettled_short_fine_intervals` | Unsettled, Short Fine |
| 30 | `very_unsettled_finer_at_times` | Very Unsettled |
| 31 | `stormy_possibly_improving` | Stormy, May Improve |
| 32 | `stormy_much_rain` | Stormy, Heavy Rain |

---

## Sager states

| Key | Description |
|---|---|
| `sager_fair_improving` | Fair, improving |
| `sager_fair_tending_to_deteriorate` | Fair, tending to deteriorate |
| `sager_fair_no_change` | Fair, no important change |
| `sager_unsettled_rain_likely` | Unsettled, rain likely |
| `sager_unsettled_probably_improving` | Unsettled, probably improving |
| `sager_unsettled_rain_at_times` | Unsettled, rain at times |
| `sager_changeable_becoming_fairer` | Changeable, becoming fairer |
| `sager_changeable_becoming_more_unsettled` | Changeable, more unsettled |
| `sager_variable_slowly_improving` | Variable, slowly improving |
| `sager_variable_slowly_deteriorating` | Variable, slowly deteriorating |
| `sager_variable_some_change` | Variable, some change |

---

## Using in automations

Example trigger when weather deteriorates:

```yaml
trigger:
  - platform: state
    entity_id: sensor.zambretti_forecast
    to:
      - "very_unsettled_rain"
      - "stormy_much_rain"
      - "rain_at_frequent_intervals"
action:
  - service: notify.mobile_app
    data:
      message: "Zambretti forecast: weather deteriorating — {{ trigger.to_state.state }}"
```

Example for high precipitation probability:

```yaml
trigger:
  - platform: numeric_state
    entity_id: sensor.precipitation_probability
    above: 70
```
