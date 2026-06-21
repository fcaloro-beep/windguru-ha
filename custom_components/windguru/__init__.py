import asyncio
from datetime import timedelta
import logging

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_BASE, API_REFERER, DEFAULT_SCAN_INTERVAL, DOMAIN

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
    return True


class WindguruDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.station_id = entry.data["station_id"]
        self.station_name = entry.data.get("name", f"Station {self.station_id}")
        self._session = async_get_clientsession(hass)

        update_interval = timedelta(seconds=entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL))

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{self.station_id}",
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        headers = {"Referer": API_REFERER.format(station_id=self.station_id)}
        params = {"q": "station_data_current", "id_station": self.station_id}

        try:
            async with async_timeout.timeout(10):
                resp = await self._session.get(API_BASE, headers=headers, params=params)
                resp.raise_for_status()
                data = await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

        if "error" in data:
            raise UpdateFailed(f"API error: {data['error']}")

        return data
