"""TodoListEntity for Orkesflow boards in Home Assistant."""
import logging
from typing import Any, List, Optional

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
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
    """Set up the Orkesflow todo entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: OrkesflowDataUpdateCoordinator = data["coordinator"]
    selected_boards: List[str] = entry.data.get(CONF_SELECTED_BOARDS, [])

    entities = [
        OrkesflowTodoListEntity(coordinator, board_id)
        for board_id in selected_boards
    ]
    async_add_entities(entities)

class OrkesflowTodoListEntity(
    CoordinatorEntity[OrkesflowDataUpdateCoordinator], TodoListEntity
):
    """Orkesflow Todo List Entity."""

    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
    )

    def __init__(
        self,
        coordinator: OrkesflowDataUpdateCoordinator,
        board_id: str,
    ) -> None:
        """Initialize the Todo List Entity."""
        super().__init__(coordinator)
        self._board_id = board_id
        self._attr_unique_id = f"orkesflow_board_{board_id}"
        self._attr_name = f"Orkesflow Board {board_id}"

    @property
    def todo_items(self) -> Optional[List[TodoItem]]:
        """Return the list of Todo items for this board."""
        items_raw = self.coordinator.data.get(self._board_id, [])
        todo_list: List[TodoItem] = []

        for item in items_raw:
            is_completed = item.get("isPurchased") or item.get("isCompleted") or False
            status = (
                TodoItemStatus.COMPLETED
                if is_completed
                else TodoItemStatus.NEEDS_ACTION
            )
            todo_list.append(
                TodoItem(
                    summary=item.get("name") or item.get("title") or "Sin título",
                    uid=item.get("id"),
                    status=status,
                )
            )
        return todo_list

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Add an item to the Orkesflow board."""
        if not item.summary:
            return
        await self.coordinator.api.async_add_shopping_item(
            self._board_id, item.summary
        )
        await self.coordinator.async_request_refresh()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update an item's completed status."""
        if not item.uid:
            return
        is_completed = item.status == TodoItemStatus.COMPLETED
        await self.coordinator.api.async_toggle_shopping_item(item.uid, is_completed)
        await self.coordinator.async_request_refresh()

    async def async_delete_todo_item(self, uids: List[str]) -> None:
        """Delete items from the board."""
        for uid in uids:
            await self.coordinator.api.async_delete_shopping_item(uid)
        await self.coordinator.async_request_refresh()
