"""Client for the select.live local API on Selectronic SP PRO inverters.

Example response:
{
  "device": {"name": "Selectronic SP-PRO"},
  "item_count": 22,
  "items": {
    "battery_in_wh_today": 3.78369140625,
    "battery_soc": 99.8984375,
    "battery_w": 26.91650390625,
    "grid_w": 1373.52294921875,
    ...
    "timestamp": 1791841270
  },
  "now": 1791841274
}
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import aiohttp


class SelectLiveError(Exception):
    """Base error for the select.live API."""


class CannotConnect(SelectLiveError):
    """Raised when the device cannot be reached or returns an error."""


@dataclass
class SelectLiveData:
    """A single reading from the device."""

    device_name: str | None
    items: dict[str, Any]


class SelectLiveApi:
    """Reads values from a select.live device."""

    def __init__(self, session: aiohttp.ClientSession, host: str, device_id: str) -> None:
        self._session = session
        self._url = f"http://{host.lower()}/cgi-bin/solarmonweb/devices/{device_id}/point"

    async def async_get_data(self) -> SelectLiveData:
        """Fetch the latest values from the device."""
        try:
            async with asyncio.timeout(10):
                resp = await self._session.get(
                    self._url, headers={"Accept": "application/json"}
                )
                resp.raise_for_status()
                body = await resp.json(content_type=None)
        except (TimeoutError, aiohttp.ClientError, ValueError) as err:
            raise CannotConnect(f"Error fetching {self._url}: {err}") from err

        if not isinstance(body, dict) or "items" not in body:
            raise CannotConnect(f"Unexpected response from {self._url}")

        return SelectLiveData(
            device_name=(body.get("device") or {}).get("name"),
            items=body["items"],
        )
