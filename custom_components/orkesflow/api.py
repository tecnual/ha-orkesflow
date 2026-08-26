"""Client API Python async for Orkesflow REST API."""
import logging
import aiohttp
from typing import Any, Dict, List

_LOGGER = logging.getLogger(__name__)

class OrkesflowApiClient:
    """Async API Client for Orkesflow."""

    def __init__(self, session: aiohttp.ClientSession, base_url: str, token: str) -> None:
        self._session = session
        base = base_url.rstrip("/")
        if not base.endswith("/api/v1"):
            base = f"{base}/api/v1"
        self._base_url = base
        self._token = token
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def async_validate_credentials(self) -> bool:
        """Validate connection by fetching boards."""
        try:
            boards = await self.async_get_boards()
            return len(boards) >= 0
        except Exception as err:
            _LOGGER.error("Error validating Orkesflow credentials: %s", err)
            return False

    async def async_get_boards(self) -> List[Dict[str, Any]]:
        """Fetch list of all user boards (shopping, chores, meal plan, kanban, etc.)."""
        try:
            url = f"{self._base_url}/boards"
            async with self._session.get(url, headers=self._headers, timeout=10) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    if isinstance(data, list):
                        return data
                else:
                    _LOGGER.warning("GET /boards returned status %s: %s", resp.status, await resp.text())
        except Exception as err:
            _LOGGER.warning("Could not fetch /boards, falling back to /shopping/boards: %s", err)

        return await self.async_get_shopping_boards()

    async def async_get_shopping_boards(self) -> List[Dict[str, Any]]:
        """Fetch list of shopping boards."""
        url = f"{self._base_url}/shopping/boards"
        async with self._session.get(url, headers=self._headers) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def async_get_board_details(self, board_id: str) -> Dict[str, Any]:
        """Fetch full details for a board."""
        url = f"{self._base_url}/boards/{board_id}"
        async with self._session.get(url, headers=self._headers) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def async_get_board_items(self, board_id: str) -> List[Dict[str, Any]]:
        """Fetch items/cards for any board."""
        # 1. Try shopping list items endpoint
        try:
            url = f"{self._base_url}/shopping/boards/{board_id}/items"
            async with self._session.get(url, headers=self._headers) as resp:
                if resp.status == 200:
                    items = await resp.json()
                    for item in items:
                        if "product" in item and isinstance(item["product"], dict):
                            item["name"] = item["product"].get("name")
                        item["itemType"] = "SHOPPING"
                    return items
        except Exception as err:
            _LOGGER.debug("Shopping items fetch failed for board %s, trying board details: %s", board_id, err)

        # 2. Fallback to generic board details (cards across columns)
        try:
            board = await self.async_get_board_details(board_id)
            items: List[Dict[str, Any]] = []
            for col in board.get("columns", []):
                col_name = col.get("name", "").lower()
                col_cat = col.get("category", "")
                is_col_done = col_cat == "DONE" or "comprad" in col_name or "completad" in col_name or "done" in col_name

                # Process shopping items if present in column
                for item in col.get("shoppingItems", []):
                    prod_name = item.get("product", {}).get("name") if isinstance(item.get("product"), dict) else item.get("name")
                    items.append({
                        "id": item.get("id"),
                        "name": prod_name or "Sin título",
                        "title": prod_name or "Sin título",
                        "isPurchased": item.get("isPurchased", is_col_done),
                        "isCompleted": item.get("isPurchased", is_col_done),
                        "columnId": col.get("id"),
                        "itemType": "SHOPPING",
                    })

                # Process cards if present in column
                for bc in col.get("boardCards", []):
                    card = bc.get("card") or bc
                    if card and not card.get("archivedAt"):
                        items.append({
                            "id": card.get("id"),
                            "name": card.get("title") or card.get("name") or "Sin título",
                            "title": card.get("title") or card.get("name") or "Sin título",
                            "isCompleted": is_col_done,
                            "isPurchased": is_col_done,
                            "columnId": col.get("id"),
                            "itemType": "CARD",
                        })
            return items
        except Exception as err:
            _LOGGER.error("Failed to fetch board items for board %s: %s", board_id, err)
            return []

    async def async_add_shopping_item(self, board_id: str, name: str, quantity: int = 1) -> Dict[str, Any]:
        """Add a new item or card to a board."""
        target_column_id = board_id
        is_shopping = True
        try:
            board = await self.async_get_board_details(board_id)
            if board.get("type") != "SHOPPING_LIST":
                is_shopping = False
            cols = board.get("columns", [])
            if cols:
                target_column_id = cols[0]["id"]
        except Exception:
            pass

        if is_shopping:
            url = f"{self._base_url}/shopping/items"
            payload = {
                "name": name,
                "quantity": quantity,
                "columnId": target_column_id,
            }
            try:
                async with self._session.post(url, json=payload, headers=self._headers) as resp:
                    if resp.status in (200, 201):
                        return await resp.json()
            except Exception:
                pass

        # Fallback to card creation
        url = f"{self._base_url}/boards/cards"
        payload = {
            "title": name,
            "columnId": target_column_id,
        }
        async with self._session.post(url, json=payload, headers=self._headers) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def async_toggle_shopping_item(self, item_id: str, is_purchased: bool, board_id: str | None = None) -> Dict[str, Any]:
        """Toggle item or card completed status."""
        url = f"{self._base_url}/shopping/items/{item_id}/toggle"
        payload = {"isPurchased": is_purchased}
        try:
            async with self._session.patch(url, json=payload, headers=self._headers) as resp:
                if resp.status in (200, 201):
                    return await resp.json()
        except Exception:
            pass

        if board_id:
            try:
                board = await self.async_get_board_details(board_id)
                cols = board.get("columns", [])
                target_col = None
                for c in cols:
                    c_name = c.get("name", "").lower()
                    c_cat = c.get("category", "")
                    if is_purchased and (c_cat == "DONE" or "completad" in c_name or "done" in c_name or "comprad" in c_name):
                        target_col = c["id"]
                        break
                    elif not is_purchased and (c_cat in ("TODO", "BACKLOG") or "todo" in c_name or "hacer" in c_name or "diarias" in c_name):
                        target_col = c["id"]
                        break
                if not target_col and cols:
                    target_col = cols[-1]["id"] if is_purchased else cols[0]["id"]

                if target_col:
                    card_url = f"{self._base_url}/boards/cards/{item_id}"
                    async with self._session.patch(card_url, json={"columnId": target_col}, headers=self._headers) as resp:
                        if resp.status in (200, 201):
                            return await resp.json()
            except Exception as err:
                _LOGGER.error("Failed to update card position for item %s: %s", item_id, err)

        return {}

    async def async_delete_shopping_item(self, item_id: str) -> bool:
        """Delete an item or card from a board."""
        url = f"{self._base_url}/shopping/items/{item_id}"
        try:
            async with self._session.delete(url, headers=self._headers) as resp:
                if resp.status in (200, 204):
                    return True
        except Exception:
            pass

        url = f"{self._base_url}/boards/cards/{item_id}"
        async with self._session.delete(url, headers=self._headers) as resp:
            return resp.status in (200, 204)
