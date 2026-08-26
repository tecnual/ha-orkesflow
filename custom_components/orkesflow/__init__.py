"""The Orkesflow integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OrkesflowApiClient
from .const import CONF_SELECTED_BOARDS, CONF_TOKEN, CONF_URL, DOMAIN, PLATFORMS
from .coordinator import OrkesflowDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Orkesflow from a config entry."""
    url = entry.data[CONF_URL]
    token = entry.data[CONF_TOKEN]
    selected_boards = entry.data.get(CONF_SELECTED_BOARDS, [])

    session = async_get_clientsession(hass)
    api = OrkesflowApiClient(session, url, token)

    coordinator = OrkesflowDataUpdateCoordinator(hass, api, selected_boards)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
