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

    @property
    def name(self) -> str:
        """Return the entity display name formatted as [Nombre de la lista] (Orkesflow)."""
        board_info = self.coordinator.boards_info.get(self._board_id, {})
        list_name = (
            board_info.get("title")
            or board_info.get("name")
            or f"Lista {self._board_id}"
        )
        return f"{list_name} (Orkesflow)"

    @property
    def todo_items(self) -> Optional[List[TodoItem]]:
        """Return the list of Todo items for this board."""
        items_raw = self.coordinator.data.get(self._board_id, []) if self.coordinator.data else []
        todo_list: List[TodoItem] = []

        for item in items_raw:
            is_completed = item.get("isPurchased") or item.get("isCompleted") or False
            status = (
                TodoItemStatus.COMPLETED
                if is_completed
                else TodoItemStatus.NEEDS_ACTION
            )

            # Properly extract product name or card title or item name
            product = item.get("product") if isinstance(item.get("product"), dict) else {}
            summary = (
                item.get("name")
                or item.get("title")
                or product.get("name")
                or "Sin título"
            )

            todo_list.append(
                TodoItem(
                    summary=summary,
                    uid=str(item.get("id")),
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
        await self.coordinator.api.async_toggle_shopping_item(
            item.uid, is_completed, board_id=self._board_id
        )
        await self.coordinator.async_request_refresh()

    async def async_delete_todo_item(self, uids: List[str]) -> None:
        """Delete items from the board."""
        for uid in uids:
            await self.coordinator.api.async_delete_shopping_item(uid)
        await self.coordinator.async_request_refresh()
