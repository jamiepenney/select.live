# select.live for Home Assistant

Reads live power and daily energy figures from a Selectronic SP PRO inverter via its local select.live interface.

## Install (HACS)

1. HACS → ⋮ → **Custom repositories** → add `https://github.com/jamiepenney/select.live`, category **Integration**.
2. Install **select.live**, then restart Home Assistant.
3. Settings → Devices & services → **Add integration** → **select.live**.
4. Enter the host (usually `selectronic`) and your device ID.

## Sensors

| Sensor | Unit |
| --- | --- |
| Battery state of charge | % |
| Power used, Grid load, Battery load, Solar load | W |
| Exported energy, AC load, AC input energy, Battery input, Battery output (today) | kWh |

Data is polled every 30 seconds.

## Upgrading from the YAML version

Existing `sensor: - platform: select_live` config is imported automatically on restart, and existing entities keep their entity IDs and history. Once imported, remove the YAML block.
