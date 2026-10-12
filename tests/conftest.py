"""Shared fixtures for select.live tests."""
from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.select_live.api import SelectLiveData

DEVICE_ID = "9DE3EBC11070836EBF1A37E3C9E31CEA"

SAMPLE_ITEMS = {
    "battery_in_wh_today": 3.78,
    "battery_out_wh_today": 3.78,
    "battery_soc": 99.9,
    "battery_w": 26.9,
    "grid_in_wh_today": 0.0,
    "grid_out_wh_today": 1.28,
    "grid_w": 1373.5,
    "load_w": 0.0,
    "load_wh_today": 3.25,
    "solarinverter_w": 0.0,
    "timestamp": 1791841270,
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Allow loading custom_components in every test."""


@pytest.fixture
def mock_api() -> Generator[AsyncMock]:
    """Return canned device data instead of calling the network."""
    with patch(
        "custom_components.select_live.api.SelectLiveApi.async_get_data",
        new=AsyncMock(return_value=SelectLiveData("Selectronic SP-PRO", SAMPLE_ITEMS)),
    ) as mock:
        yield mock
