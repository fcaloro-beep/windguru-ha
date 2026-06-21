# Windguru Station for Home Assistant

Custom Home Assistant integration that exposes live measurements from public
Windguru weather stations.

## Features

- Add a station by Windguru ID or browse the supported countries.
- Wind average, gust, minimum speed and direction.
- Temperature, atmospheric pressure and humidity.
- Configurable refresh interval (minimum 60 seconds).
- English and Italian configuration screens.
- Built-in wind dashboard card with compass, average/gust gauge and temperature.

## Talamone dashboard

Version 1.2.2 includes a dashboard card with no additional frontend dependency.
After restarting Home Assistant, add a manual card and paste:

```yaml
type: custom:windguru-dashboard
title: Talamone
direction_entity: sensor.talamone_wind_direction
average_entity: sensor.talamone_wind_average
gust_entity: sensor.talamone_wind_gust
temperature_entity: sensor.talamone_temperature
max_speed: 40
grid_options:
  columns: full
  rows: auto
```

The compass follows wind direction, the main gauge shows average wind and the
orange marker follows gust speed. Humidity is intentionally not displayed.

## Installation

### HACS

1. Open HACS and choose **Custom repositories**.
2. Add `https://github.com/fcaloro-beep/windguru-ha` as an **Integration**.
3. Install **Windguru Station** and restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration** and search for
   **Windguru Station**.

### Manual

Copy `custom_components/windguru` into the `custom_components` folder of your
Home Assistant configuration, then restart Home Assistant.

## Finding a station ID

Open a station on Windguru. Its numeric ID is the last part of the URL, for
example `2791` in `https://www.windguru.cz/station/2791`.

## Notes

This project uses the unofficial endpoint used by the Windguru website and is
not affiliated with Windguru. Availability and values depend on the selected
station. Country browsing uses station time zones, so entering the exact ID is
the most reliable option near borders or in countries with shared time zones.

## Development

Run the local checks with:

```bash
ruff check .
python -m unittest discover -s tests -v
```

## License

[MIT](LICENSE)
