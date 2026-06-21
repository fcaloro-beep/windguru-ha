from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key="wind_avg",
        name="Wind average",
        icon="mdi:weather-windy",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.KNOTS,
    ),
    SensorEntityDescription(
        key="wind_max",
        name="Wind gust",
        icon="mdi:weather-windy",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.KNOTS,
    ),
    SensorEntityDescription(
        key="wind_min",
        name="Minimum wind",
        icon="mdi:weather-windy",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.KNOTS,
    ),
    SensorEntityDescription(
        key="wind_direction",
        name="Wind direction",
        icon="mdi:compass-rose",
        native_unit_of_measurement="°",
    ),
    SensorEntityDescription(
        key="temperature",
        name="Temperature",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    SensorEntityDescription(
        key="mslp",
        name="Pressure",
        icon="mdi:gauge",
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.HPA,
    ),
    SensorEntityDescription(
        key="rh",
        name="Humidity",
        icon="mdi:water-percent",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        WindguruSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class WindguruSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, description: SensorEntityDescription):
        super().__init__(coordinator)
        self.entity_description = description
        self._station_id = entry.data["station_id"]
        self._station_name = entry.data.get("name", f"Station {self._station_id}")
        self._attr_unique_id = f"windguru_{self._station_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(self._station_id))},
            name=self._station_name,
            manufacturer="Windguru",
            model="Weather Station",
            configuration_url=f"https://www.windguru.cz/station/{self._station_id}",
        )

    @property
    def native_value(self):
        data = self.coordinator.data
        if data is None:
            return None
        return data.get(self.entity_description.key)

    @property
    def available(self):
        return (
            self.coordinator.last_update_success and self.coordinator.data is not None
        )
