from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from .const import DOMAIN, ADDRESS, DEV_NAME

DATA_SCHEMA = vol.Schema({
    vol.Required(ADDRESS): str,
    vol.Required(DEV_NAME, default="FHT Thermostat"): str,
})

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)

        # Eindeutigkeit: setze unique_id auf die Adresse
        await self.async_set_unique_id(user_input[ADDRESS])
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=user_input[DEV_NAME],
            data=user_input
        )
