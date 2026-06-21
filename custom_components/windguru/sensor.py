from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_TYPES


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for sensor_key, sensor_config in SENSOR_TYPES.items():
        entities.append(WindguruSensor(coordinator, entry, sensor_key, sensor_config))

    async_add_entities(entities)


class WindguruSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry, sensor_key, sensor_config):
        super().__init__(coordinator)
        self._sensor_key = sensor_key
        self._sensor_config = sensor_config
        self._station_id = entry.data["station_id"]
        self._station_name = entry.data.get("name", f"Station {self._station_id}")
        self._attr_unique_id = f"windguru_{self._station_id}_{sensor_key}"
        self._attr_name = f"{self._station_name} {sensor_config['name']}"
        self._attr_icon = sensor_config["icon"]
        self._attr_should_poll = False
        self._attr_device_info = {
            "identifiers": {(DOMAIN, str(self._station_id))},
            "name": self._station_name,
            "manufacturer": "Windguru",
            "model": "Weather Station",
            "sw_version": "1.0",
        }

    @property
    def native_unit_of_measurement(self):
        return self._sensor_config["unit"]

    @property
    def device_class(self):
        return self._sensor_config["device_class"]

    @property
    def state_class(self):
        return self._sensor_config["state_class"]

    @property
    def native_value(self):
        data = self.coordinator.data
        if data is None:
            return None
        value = data.get(self._sensor_key)
        return value if value is not None else None

    @property
    def available(self):
        return self.coordinator.last_update_success and self.coordinator.data is not None
