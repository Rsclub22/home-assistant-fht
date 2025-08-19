from homeassistant.const import Platform
from homeassistant.util import slugify

from .const import ADDRESS, DEV_NAME

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


async def async_migrate_entry(hass, config_entry):
    """Migrate config entry to new unique ID format."""
    if config_entry.version < 2:
        new_unique_id = f"{config_entry.data[ADDRESS]}_{slugify(config_entry.data[DEV_NAME])}"
        hass.config_entries.async_update_entry(
            config_entry, unique_id=new_unique_id, version=2
        )
    return True
