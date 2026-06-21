import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WindguruApiClient, WindguruApiError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = WindguruDataCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class WindguruDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.station_id = entry.data["station_id"]
        self.station_name = entry.data.get("name", f"Station {self.station_id}")
        self._api = WindguruApiClient(async_get_clientsession(hass))

        update_interval = timedelta(
            seconds=entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL)
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{self.station_id}",
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        try:
            return await self._api.async_get_current(self.station_id)
        except WindguruApiError as err:
            raise UpdateFailed(f"Error fetching Windguru data: {err}") from err
