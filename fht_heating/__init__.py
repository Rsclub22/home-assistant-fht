from __future__ import annotations

import logging
from homeassistant.const import Platform
from .const import DOMAIN, ADDRESS, DEV_NAME
from .fht import Fht

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.BINARY_SENSOR]


async def async_setup(hass, config):
    _LOGGER.debug("fht_heating.async_setup (YAML path)")
    return True


async def async_setup_entry(hass, entry):
    address = entry.data[ADDRESS]
    dev_name = entry.data[DEV_NAME]
    _LOGGER.info(
        "fht_heating: setting up entry id=%s dev=%s addr=%s",
        entry.entry_id, dev_name, address
    )
    fht = Fht(address, dev_name)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = fht
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    _LOGGER.info("fht_heating: unloading entry id=%s", entry.entry_id)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
