from homeassistant.const import Platform

PLATFORMS: list[Platform] = [Platform.CLIMATE]


async def async_setup(hass, config):
    """Set up the Fht platform."""
    return True


async def async_setup_entry(hass, entry):
    """Set up the Fht heater."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
