"""Config flow for Orkesflow integration."""
from typing import Any, Dict, List
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .api import OrkesflowApiClient
from .const import CONF_SELECTED_BOARDS, CONF_TOKEN, CONF_URL, DOMAIN

class OrkesflowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Orkesflow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._url: str = ""
        self._token: str = ""
        self._boards: List[Dict[str, Any]] = []

    async def async_step_user(
        self, user_input: Dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Step 1: Get API credentials."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            self._url = user_input[CONF_URL]
            self._token = user_input[CONF_TOKEN]

            session = async_get_clientsession(self.hass)
            client = OrkesflowApiClient(session, self._url, self._token)

            valid = await client.async_validate_credentials()
            if valid:
                try:
                    self._boards = await client.async_get_shopping_boards()
                    return await self.async_step_boards()
                except Exception:
                    errors["base"] = "cannot_connect"
            else:
                errors["base"] = "invalid_auth"

        schema = vol.Schema(
            {
                vol.Required(CONF_URL, default="http://localhost:3000"): str,
                vol.Required(CONF_TOKEN): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    async def async_step_boards(
        self, user_input: Dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Step 2: Select boards to import as todo entities."""
        if user_input is not None:
            return self.async_create_entry(
                title="Orkesflow",
                data={
                    CONF_URL: self._url,
                    CONF_TOKEN: self._token,
                    CONF_SELECTED_BOARDS: user_input[CONF_SELECTED_BOARDS],
                },
            )

        board_options = {
            b["id"]: b.get("title") or b.get("name") or b["id"] for b in self._boards
        }

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SELECTED_BOARDS, default=list(board_options.keys())
                ): cv.multi_select(board_options)
            }
        )

        return self.async_show_form(step_id="boards", data_schema=schema)
