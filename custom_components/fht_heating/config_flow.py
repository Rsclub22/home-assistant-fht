from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, ADDRESS, DEV_NAME

DATA_SCHEMA = vol.Schema({
    vol.Required(ADDRESS, default="http://192.168.1.100:8083"): str,
    vol.Required(DEV_NAME, default="FHT_1234"): str,
})

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 3

    async def async_step_user(self, user_input=None):
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)

        address = user_input[ADDRESS].strip()
        if not address.startswith("http://") and not address.startswith("https://"):
            address = f"http://{address}"

        dev_name = user_input[DEV_NAME].strip()

        # Unique per FHEM controller address
        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"FHEM Controller ({address})",
            data={ADDRESS: address},
            options={"devices": [dev_name]}
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self) -> None:
        pass

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            action = user_input.get("action", "").strip().lower()
            if action == "add_device":
                return await self.async_step_add_device()
            elif action == "remove_device":
                return await self.async_step_remove_device()
            else:
                errors["base"] = "invalid_action"

        options_schema = vol.Schema({
            vol.Required("action", default="add_device"): vol.In(["add_device", "remove_device"]),
        })

        return self.async_show_form(step_id="init", data_schema=options_schema, errors=errors)

    async def async_step_add_device(self, user_input=None):
        if user_input is not None:
            dev_name = user_input[DEV_NAME].strip()

            # Read old list
            devices = self.config_entry.options.get("devices")
            if not isinstance(devices, list):
                # Fallback to legacy string
                dev_names_str = self.config_entry.options.get(DEV_NAME, self.config_entry.data.get(DEV_NAME, ""))
                devices = [d.strip() for d in dev_names_str.split(",") if d.strip()]
            else:
                devices = list(devices)

            if dev_name and dev_name not in devices:
                devices.append(dev_name)

            new_options = dict(self.config_entry.options)
            new_options["devices"] = devices
            new_options.pop(DEV_NAME, None) # clean up legacy

            return self.async_create_entry(title="", data=new_options)

        options_schema = vol.Schema({
            vol.Required(DEV_NAME, default="FHT_5678"): str,
        })

        return self.async_show_form(step_id="add_device", data_schema=options_schema)

    async def async_step_remove_device(self, user_input=None):
        # Read current devices
        devices = self.config_entry.options.get("devices")
        if not isinstance(devices, list):
            dev_names_str = self.config_entry.options.get(DEV_NAME, self.config_entry.data.get(DEV_NAME, ""))
            devices = [d.strip() for d in dev_names_str.split(",") if d.strip()]
        else:
            devices = list(devices)

        errors = {}
        if user_input is not None:
            dev_name = user_input[DEV_NAME].strip()
            if dev_name in devices:
                devices.remove(dev_name)
                new_options = dict(self.config_entry.options)
                new_options["devices"] = devices
                new_options.pop(DEV_NAME, None)
                return self.async_create_entry(title="", data=new_options)
            else:
                errors["base"] = "device_not_found"

        options_schema = vol.Schema({
            vol.Required(DEV_NAME): vol.In(devices) if devices else str,
        })

        return self.async_show_form(step_id="remove_device", data_schema=options_schema, errors=errors)
