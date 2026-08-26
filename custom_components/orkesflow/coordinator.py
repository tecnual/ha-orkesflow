"""DataUpdateCoordinator for Orkesflow."""
from datetime import timedelta
import logging
from typing import Any, Dict, List

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import OrkesflowApiClient
from .const import DEFAULT_POLL_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

class OrkesflowDataUpdateCoordinator(DataUpdateCoordinator[Dict[str, List[Dict[str, Any]]]]):
    """Class to manage fetching data from Orkesflow API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: OrkesflowApiClient,
        selected_board_ids: List[str],
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_POLL_INTERVAL),
        )
        self.api = api
        self.selected_board_ids = selected_board_ids

    async def _async_update_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch data from API for all selected boards."""
        data: Dict[str, List[Dict[str, Any]]] = {}
        try:
            for board_id in self.selected_board_ids:
                items = await self.api.async_get_board_items(board_id)
                data[board_id] = items
            return data
        except Exception as err:
            raise UpdateFailed(f"Error fetching Orkesflow data: {err}") from err
