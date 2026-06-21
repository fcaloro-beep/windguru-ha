import logging
from datetime import timedelta
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WindguruApiClient, WindguruApiError
from .const import (
    DATA_FRONTEND_REGISTERED,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    FRONTEND_URL,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    domain_data = hass.data.setdefault(DOMAIN, {})
    if not domain_data.get(DATA_FRONTEND_REGISTERED):
        frontend_file = Path(__file__).parent / "frontend" / "windguru-dashboard.js"
        await hass.http.async_register_static_paths(
            [StaticPathConfig(FRONTEND_URL, str(frontend_file), cache_headers=True)]
        )
        add_extra_js_url(hass, f"{FRONTEND_URL}?v=1.2.1")
        domain_data[DATA_FRONTEND_REGISTERED] = True

    coordinator = WindguruDataCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    domain_data[entry.entry_id] = coordinator
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
