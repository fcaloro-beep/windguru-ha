"""Config flow for the Windguru integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    WindguruApiClient,
    WindguruCannotConnect,
    WindguruInvalidStation,
    WindguruUnauthorized,
)
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, MIN_SCAN_INTERVAL


class WindguruConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._country_id: int | None = None
        self._station_id: int | None = None

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            if user_input["method"] == "browse":
                return await self.async_step_country()
            return await self.async_step_manual()

        schema = vol.Schema(
            {
                vol.Required("method", default="browse"): vol.In(
                    {
                        "browse": "Browse by country",
                        "manual": "Enter station ID",
                    }
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_manual(self, user_input=None):
        errors = {}
        if user_input is not None:
            station_id = user_input["station_id"]
            name = user_input.get("name", "")
            try:
                station = await self._api.async_get_station(station_id)
            except WindguruInvalidStation:
                errors["base"] = "invalid_station"
            except WindguruUnauthorized:
                errors["base"] = "unauthorized"
            except WindguruCannotConnect:
                errors["base"] = "cannot_connect"

            if not errors:
                if not name:
                    name = station.get("name") or station.get(
                        "spotname", f"Station {station_id}"
                    )
                await self.async_set_unique_id(f"windguru_{station_id}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name,
                    data={
                        "station_id": station_id,
                        "name": name,
                        "scan_interval": user_input.get(
                            "scan_interval", DEFAULT_SCAN_INTERVAL
                        ),
                    },
                )

        schema = vol.Schema(
            {
                vol.Required("station_id"): vol.Coerce(int),
                vol.Optional("name"): str,
                vol.Optional("scan_interval", default=DEFAULT_SCAN_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)
                ),
            }
        )
        return self.async_show_form(step_id="manual", data_schema=schema, errors=errors)

    async def async_step_country(self, user_input=None):
        if user_input is not None:
            self._country_id = int(user_input["country_id"])
            return await self.async_step_station()

        try:
            countries = await self._api.async_get_countries()
        except (WindguruCannotConnect, WindguruUnauthorized):
            return self.async_abort(reason="cannot_connect")

        sorted_countries = sorted(countries.items(), key=lambda x: x[1])
        country_options = {k: v for k, v in sorted_countries}

        schema = vol.Schema({vol.Required("country_id"): vol.In(country_options)})
        return self.async_show_form(step_id="country", data_schema=schema)

    async def async_step_station(self, user_input=None):
        if user_input is not None:
            self._station_id = int(user_input["station_id"])
            return await self.async_step_confirm()

        try:
            filtered = await self._api.async_get_stations(self._country_id)
        except (WindguruCannotConnect, WindguruUnauthorized):
            return self.async_abort(reason="cannot_connect")

        if not filtered:
            return self.async_abort(reason="no_stations")

        filtered.sort(key=lambda s: (s.get("spotname") or "").lower())
        stations_options = {}
        for s in filtered:
            sid = s["id_station"]
            label = s.get("spotname") or s.get("name") or f"Station {sid}"
            stations_options[str(sid)] = f"{label} (ID {sid})"

        schema = vol.Schema({vol.Required("station_id"): vol.In(stations_options)})
        return self.async_show_form(
            step_id="station",
            data_schema=schema,
            description_placeholders={"count": str(len(filtered))},
        )

    async def async_step_confirm(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title=user_input["name"],
                data={
                    "station_id": self._station_id,
                    "name": user_input["name"],
                    "scan_interval": user_input.get(
                        "scan_interval", DEFAULT_SCAN_INTERVAL
                    ),
                },
            )

        await self.async_set_unique_id(f"windguru_{self._station_id}")
        self._abort_if_unique_id_configured()

        try:
            station = await self._api.async_get_station(self._station_id)
        except (WindguruCannotConnect, WindguruInvalidStation, WindguruUnauthorized):
            return self.async_show_form(
                step_id="confirm",
                data_schema=self._confirm_schema(f"Station {self._station_id}"),
                description_placeholders={"station": f"(ID {self._station_id})"},
            )

        default_name = station.get("name") or station.get(
            "spotname", f"Station {self._station_id}"
        )

        return self.async_show_form(
            step_id="confirm",
            data_schema=self._confirm_schema(default_name),
            description_placeholders={
                "station": f"{default_name} (ID {self._station_id})"
            },
        )

    def _confirm_schema(self, default_name: str) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required("name", default=default_name): str,
                vol.Optional("scan_interval", default=DEFAULT_SCAN_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)
                ),
            }
        )

    @property
    def _api(self) -> WindguruApiClient:
        return WindguruApiClient(async_get_clientsession(self.hass))
