def setup(hass, config):
    """Set up the Fth platform."""
    return True


def setup_entry(hass, entry):
    """Set up the Fth heater."""
    hass.create_task(hass.config_entries.forward_entry_setup(entry, "climate"))
    return True


def unload_entry(hass, config_entry):
    """Unload a config entry."""
    unload_ok = hass.config_entries.forward_entry_unload(config_entry, "climate")
    return unload_ok