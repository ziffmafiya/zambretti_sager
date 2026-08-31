#!/usr/bin/env python3
"""Generate HA translation JSON files from English base + locale overlays."""

from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "custom_components" / "zambretti_sager" / "translations"
OVERLAYS = Path(__file__).resolve().parent / "locale_overlays"
BASE = json.loads((OUT / "en.json").read_text(encoding="utf-8"))

FIELDS = (
    "title",
    "desc",
    "pressure",
    "wind",
    "wind_speed",
    "temp",
    "humid",
    "sea",
    "loc",
    "p_desc",
    "w_desc",
    "ws_desc",
    "t_desc",
    "h_desc",
    "s_desc",
    "l_desc",
    "opt_title",
    "opt_desc",
    "err_conn",
    "err_unk",
    "abort",
)


def build(t: dict) -> dict:
    data = copy.deepcopy(BASE)
    for step in ("user",):
        s = data["config"]["step"][step]
        s["title"] = t["title"]
        s["description"] = t["desc"]
        s["data"].update(
            {
                "pressure_sensor": t["pressure"],
                "wind_sensor": t["wind"],
                "wind_speed_sensor": t["wind_speed"],
                "temperature_sensor": t["temp"],
                "humidity_sensor": t["humid"],
                "use_sea_level_correction": t["sea"],
                "location": t["loc"],
            }
        )
        s["data_description"].update(
            {
                "pressure_sensor": t["p_desc"],
                "wind_sensor": t["w_desc"],
                "wind_speed_sensor": t["ws_desc"],
                "temperature_sensor": t["t_desc"],
                "humidity_sensor": t["h_desc"],
                "use_sea_level_correction": t["s_desc"],
                "location": t["l_desc"],
            }
        )
    s = data["options"]["step"]["init"]
    s["title"] = t["opt_title"]
    s["description"] = t["opt_desc"]
    s["data"].update(
        {
            "pressure_sensor": t["pressure"],
            "wind_sensor": t["wind"],
            "wind_speed_sensor": t["wind_speed"],
            "temperature_sensor": t["temp"],
            "humidity_sensor": t["humid"],
            "use_sea_level_correction": t["sea"],
            "location": t["loc"],
        }
    )
    s["data_description"].update(
        {
            "pressure_sensor": t["p_desc"],
            "wind_sensor": t["w_desc"],
            "wind_speed_sensor": t["ws_desc"],
            "temperature_sensor": t["t_desc"],
            "humidity_sensor": t["h_desc"],
            "use_sea_level_correction": t["s_desc"],
            "location": t["l_desc"],
        }
    )
    data["config"]["error"] = {"cannot_connect": t["err_conn"], "unknown": t["err_unk"]}
    data["config"]["abort"] = {"already_configured": t["abort"]}
    data["entity"]["sensor"]["zambretti_forecast"]["state"] = t["z"]
    data["entity"]["sensor"]["sager_forecast"]["state"] = t["s"]
    return data


def main() -> None:
    for path in sorted(OVERLAYS.glob("*.json")):
        locale = path.stem
        t = json.loads(path.read_text(encoding="utf-8"))
        missing = [f for f in FIELDS if f not in t]
        if missing:
            raise ValueError(f"{path.name} missing fields: {missing}")
        (OUT / f"{locale}.json").write_text(
            json.dumps(build(t), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"  {locale}.json")


if __name__ == "__main__":
    print("Generating translations:")
    main()
