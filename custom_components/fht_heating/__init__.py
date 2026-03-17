from __future__ import annotations

import logging
from homeassistant.const import Platform
from homeassistant.helpers import device_registry as dr
from .const import DOMAIN, ADDRESS, DEV_NAME
from .fht import Fht

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.BINARY_SENSOR, Platform.SELECT, Platform.TIME, Platform.NUMBER]


async def async_setup(hass, config):
    _LOGGER.debug("fht_heating.async_setup (YAML path)")

    async def handle_set_schedule(call):
        """Handle the fht_heating.set_schedule service."""
        device_id = call.data.get("device_id")

        # We need to find the fht instance from the device_id
        # In a real scenario we use the device registry to map device_id to config_entry, then to fht
        dev_reg = dr.async_get(hass)
        device = dev_reg.async_get(device_id)
        if not device:
            _LOGGER.error("Device ID %s not found for set_schedule", device_id)
            return

        fht_instances = None
        for config_entry_id in device.config_entries:
            fht_instances = hass.data.get(DOMAIN, {}).get(config_entry_id)
            if fht_instances:
                break

        if not fht_instances:
            _LOGGER.error("FHT instance not found for device %s", device_id)
            return

        target_fht = None
        for identifier in device.identifiers:
            if identifier[0] == DOMAIN:
                id_val = identifier[1] # "{address}_{dev_name}"
                for dev_name, instance in fht_instances.items():
                    if id_val.endswith(f"_{dev_name}"):
                        target_fht = instance
                        break

        if not target_fht:
            _LOGGER.error("Could not match device ID %s to any FHT instance", device_id)
            return

        # Prepare parameters
        updates = {}
        for key in call.data:
            if key != "device_id":
                val = call.data[key]
                # FHEM uses HH:MM for time
                if isinstance(val, str) and len(val) == 8 and ":" in val:
                    # Strip seconds if passed by time selector (HH:MM:SS)
                    val = val[:5]
                updates[key.replace("_", "-")] = val

        if not updates:
            return

        def _set_all():
            for k, v in updates.items():
                target_fht.set_value(k, v, bypass_cache=True)

        await hass.async_add_executor_job(_set_all)

    hass.services.async_register(DOMAIN, "set_schedule", handle_set_schedule)
    return True


async def async_setup_entry(hass, entry):
    address = entry.data.get(ADDRESS, "")

    # Ensure address is normalized to http:// or https://
    if address and not address.startswith("http://") and not address.startswith("https://"):
        address = f"http://{address}"
        # Persist the fixed address back to the entry data
        new_data = dict(entry.data)
        new_data[ADDRESS] = address
        hass.config_entries.async_update_entry(entry, data=new_data)

    # Try to read the new list structure first
    dev_names = entry.options.get("devices")
    if dev_names is None:
        dev_names = entry.data.get("devices")

    # Fallback to the old comma-separated string if it's a legacy entry
    if not isinstance(dev_names, list):
        dev_names_str = entry.options.get(DEV_NAME, entry.data.get(DEV_NAME, ""))
        dev_names = [d.strip() for d in dev_names_str.split(",") if d.strip()]

    _LOGGER.info(
        "fht_heating: setting up entry id=%s addr=%s devs=%s",
        entry.entry_id, address, dev_names
    )

    fht_instances = {}
    for dev_name in dev_names:
        fht_instances[dev_name] = Fht(address, dev_name)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = fht_instances
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(
        entry.add_update_listener(async_reload_entry)
    )

    return True

async def async_reload_entry(hass, entry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass, entry):
    _LOGGER.info("fht_heating: unloading entry id=%s", entry.entry_id)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
