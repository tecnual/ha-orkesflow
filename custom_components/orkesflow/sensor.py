"""Sensor platform for Orkesflow in Home Assistant."""
import logging
from typing import List

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SELECTED_BOARDS, DOMAIN
from .coordinator import OrkesflowDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Orkesflow sensor entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: OrkesflowDataUpdateCoordinator = data["coordinator"]
    selected_boards: List[str] = entry.data.get(CONF_SELECTED_BOARDS, [])

    entities = [
        OrkesflowPendingItemsSensor(coordinator, board_id)
        for board_id in selected_boards
    ]
    async_add_entities(entities)

class OrkesflowPendingItemsSensor(
    CoordinatorEntity[OrkesflowDataUpdateCoordinator], SensorEntity
):
    """Sensor showing number of pending items in an Orkesflow board."""

    def __init__(
        self,
        coordinator: OrkesflowDataUpdateCoordinator,
        board_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._board_id = board_id
        self._attr_unique_id = f"orkesflow_pending_sensor_{board_id}"
        self._attr_name = f"Orkesflow Pendientes Board {board_id}"
        self._attr_native_unit_of_measurement = "ítems"
        self._attr_icon = "mdi:format-list-checks"

    @property
    def native_value(self) -> int:
        """Return total pending items."""
        items_raw = self.coordinator.data.get(self._board_id, [])
        pending = [
            i for i in items_raw
            if not (i.get("isPurchased") or i.get("isCompleted") or False)
        ]
        return len(pending)
