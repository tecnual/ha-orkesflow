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
        self.boards_info: Dict[str, Dict[str, Any]] = {}

    async def _async_update_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch data from API for all selected boards."""
        try:
            all_boards = await self.api.async_get_boards()
            for b in all_boards:
                if "id" in b:
                    self.boards_info[b["id"]] = b
        except Exception as err:
            _LOGGER.warning("Could not refresh board metadata in coordinator: %s", err)

        data: Dict[str, List[Dict[str, Any]]] = {}
        try:
            for board_id in self.selected_board_ids:
                items = await self.api.async_get_board_items(board_id)
                data[board_id] = items
            return data
        except Exception as err:
            raise UpdateFailed(f"Error fetching Orkesflow data: {err}") from err
