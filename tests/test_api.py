"""Tests for the Windguru API client."""

from __future__ import annotations

import importlib
import sys
import types
import unittest
from pathlib import Path

import aiohttp

PACKAGE_PATH = Path(__file__).parents[1] / "custom_components" / "windguru"
package = types.ModuleType("custom_components.windguru")
package.__path__ = [str(PACKAGE_PATH)]
sys.modules.setdefault("custom_components.windguru", package)

api = importlib.import_module("custom_components.windguru.api")


class FakeResponse:
    def __init__(self, data, status=200):
        self.data = data
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    def raise_for_status(self):
        if self.status >= 400:
            raise aiohttp.ClientResponseError(None, (), status=self.status)

    async def json(self, **kwargs):
        return self.data


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.last_request = None

    def get(self, url, **kwargs):
        self.last_request = (url, kwargs)
        return self.response


class WindguruApiClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_current_returns_measurements(self):
        session = FakeSession(FakeResponse({"unixtime": 123, "wind_avg": 8.4}))
        client = api.WindguruApiClient(session)

        result = await client.async_get_current(2791)

        self.assertEqual(8.4, result["wind_avg"])
        self.assertEqual(2791, session.last_request[1]["params"]["id_station"])

    async def test_get_station_rejects_mismatched_id(self):
        client = api.WindguruApiClient(FakeSession(FakeResponse({"id_station": 42})))

        with self.assertRaises(api.WindguruInvalidStation):
            await client.async_get_station(2791)

    async def test_get_countries_only_returns_supported_countries(self):
        client = api.WindguruApiClient(
            FakeSession(
                FakeResponse({"380": "Italy", "276": "Germany", "4": "Afghanistan"})
            )
        )

        result = await client.async_get_countries()

        self.assertEqual({"380": "Italy", "276": "Germany"}, result)

    async def test_get_stations_filters_by_country_timezone(self):
        stations = [
            {"id_station": 1, "timezone": "Europe/Rome"},
            {"id_station": 2, "timezone": "Europe/Berlin"},
        ]
        client = api.WindguruApiClient(FakeSession(FakeResponse(stations)))

        result = await client.async_get_stations(380)

        self.assertEqual([stations[0]], result)

    async def test_unauthorized_response_has_specific_error(self):
        client = api.WindguruApiClient(FakeSession(FakeResponse({}, status=403)))

        with self.assertRaises(api.WindguruUnauthorized):
            await client.async_get_current(2791)


if __name__ == "__main__":
    unittest.main()
