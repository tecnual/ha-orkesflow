"""Client API Python async for Orkesflow REST API."""
import logging
import aiohttp
from typing import Any, Dict, List

_LOGGER = logging.getLogger(__name__)

class OrkesflowApiClient:
    """Async API Client for Orkesflow."""

    def __init__(self, session: aiohttp.ClientSession, base_url: str, token: str) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def async_validate_credentials(self) -> bool:
        """Validate connection by fetching shopping boards or user info."""
        try:
            url = f"{self._base_url}/shopping/boards"
            async with self._session.get(url, headers=self._headers, timeout=10) as resp:
                return resp.status in (200, 201)
        except Exception as err:
            _LOGGER.error("Error validating Orkesflow credentials: %s", err)
            return False

    async def async_get_shopping_boards(self) -> List[Dict[str, Any]]:
        """Fetch list of shopping boards."""
        url = f"{self._base_url}/shopping/boards"
        async with self._session.get(url, headers=self._headers) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def async_get_board_items(self, board_id: str) -> List[Dict[str, Any]]:
        """Fetch items for a specific shopping board."""
        url = f"{self._base_url}/shopping/boards/{board_id}/items"
        async with self._session.get(url, headers=self._headers) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def async_add_shopping_item(self, board_id: str, name: str, quantity: int = 1) -> Dict[str, Any]:
        """Add a new item to a shopping board."""
        url = f"{self._base_url}/shopping/items"
        payload = {
            "name": name,
            "quantity": quantity,
            "columnId": board_id,  # or default column
        }
        async with self._session.post(url, json=payload, headers=self._headers) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def async_toggle_shopping_item(self, item_id: str, is_purchased: bool) -> Dict[str, Any]:
        """Toggle an item as completed/purchased."""
        url = f"{self._base_url}/shopping/items/{item_id}/toggle"
        payload = {"isPurchased": is_purchased}
        async with self._session.patch(url, json=payload, headers=self._headers) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def async_delete_shopping_item(self, item_id: str) -> bool:
        """Delete an item from a board."""
        url = f"{self._base_url}/shopping/items/{item_id}"
        async with self._session.delete(url, headers=self._headers) as resp:
            return resp.status in (200, 204)
