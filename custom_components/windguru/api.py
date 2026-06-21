"""Small asynchronous client for the Windguru station API."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from .const import API_BASE, API_REFERER, COUNTRY_TIMEZONES


class WindguruApiError(Exception):
    """Base class for Windguru API errors."""


class WindguruCannotConnect(WindguruApiError):
    """Raised when Windguru cannot be reached or returns invalid data."""


class WindguruInvalidStation(WindguruApiError):
    """Raised when a station does not exist."""


class WindguruUnauthorized(WindguruApiError):
    """Raised when Windguru rejects the request."""


class WindguruApiClient:
    """Client for the unofficial API used by the Windguru website."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def async_get_current(self, station_id: int) -> dict[str, Any]:
        """Return the latest measurements for a station."""
        data = await self._async_request(
            {"q": "station_data_current", "id_station": station_id}, station_id
        )
        if not isinstance(data, dict) or "unixtime" not in data:
            raise WindguruCannotConnect("Windguru returned invalid measurement data")
        return data

    async def async_get_station(self, station_id: int) -> dict[str, Any]:
        """Return station metadata and validate its ID."""
        data = await self._async_request(
            {"q": "station", "id_station": station_id, "weather": "true"},
            station_id,
        )
        if not isinstance(data, dict) or data.get("id_station") != station_id:
            raise WindguruInvalidStation(f"Station {station_id} was not found")
        return data

    async def async_get_countries(self) -> dict[str, str]:
        """Return countries supported by station browsing."""
        data = await self._async_request({"q": "countries"})
        if not isinstance(data, dict):
            raise WindguruCannotConnect("Windguru returned an invalid country list")
        supported = {str(country_id) for country_id in COUNTRY_TIMEZONES}
        return {
            str(country_id): str(name)
            for country_id, name in data.items()
            if str(country_id) in supported
        }

    async def async_get_stations(self, country_id: int) -> list[dict[str, Any]]:
        """Return stations matching one of a country's time zones."""
        data = await self._async_request({"q": "station_list"})
        if not isinstance(data, list):
            raise WindguruCannotConnect("Windguru returned an invalid station list")

        timezones = set(COUNTRY_TIMEZONES.get(country_id, ()))
        if not timezones:
            return []
        return [
            station
            for station in data
            if isinstance(station, dict) and station.get("timezone") in timezones
        ]

    async def _async_request(
        self, params: dict[str, Any], station_id: int | None = None
    ) -> Any:
        headers = {
            "Referer": API_REFERER.format(station_id=station_id or 2791),
        }
        try:
            async with asyncio.timeout(15):
                async with self._session.get(
                    API_BASE, headers=headers, params=params
                ) as response:
                    if response.status == 400:
                        raise WindguruInvalidStation("Invalid station")
                    if response.status in (401, 403):
                        raise WindguruUnauthorized("Windguru denied API access")
                    response.raise_for_status()
                    data = await response.json(content_type=None)
        except WindguruApiError:
            raise
        except (TimeoutError, aiohttp.ClientError, ValueError) as err:
            raise WindguruCannotConnect(str(err)) from err

        if isinstance(data, dict) and data.get("error"):
            raise WindguruCannotConnect(str(data["error"]))
        return data
