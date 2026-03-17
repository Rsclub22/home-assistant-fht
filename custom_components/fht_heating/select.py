import logging

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

MODE_KEY = "mode"
OPTIONS = ["auto", "manual", "holiday"]

async def async_setup_entry(hass, config_entry, async_add_entities):
    fht_instances = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for dev_name, fht in fht_instances.items():
        entities.append(FhtModeSelect(fht, dev_name))

    if entities:
        async_add_entities(entities, True)


class FhtModeSelect(SelectEntity):
    _attr_should_poll = True
    _attr_options = OPTIONS

    def __init__(self, fht, dev_name: str) -> None:
        self._fht = fht
        self._address = getattr(fht, "address", dev_name)
        self._dev_name = dev_name

        self._attr_name = f"{self._dev_name} Mode"
        self._attr_unique_id = f"{self._address}_{self._dev_name}_mode"
        self._attr_current_option = None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._address}_{self._dev_name}")},
            name=f"FHT {self._dev_name}",
            manufacturer="FHT",
            model="Thermostat",
        )

    async def async_update(self):
        try:
            value = await self.hass.async_add_executor_job(self._fht.get_value, MODE_KEY)
            s = str(value).strip().lower() if value is not None else ""
            if s in OPTIONS:
                self._attr_current_option = s
                self._attr_available = True
            elif s in ("holiday_short", "holiday-short"):
                self._attr_current_option = "holiday"
                self._attr_available = True
            else:
                self._attr_current_option = None
                self._attr_available = False
        except Exception:
            self._attr_current_option = None
            self._attr_available = False

    async def async_select_option(self, option: str) -> None:
        if option not in OPTIONS or self._fht is None:
            return

        def _set():
            return self._fht.set_value(MODE_KEY, option, bypass_cache=True)

        await self.hass.async_add_executor_job(_set)
        self._attr_current_option = option
        self.async_write_ha_state()
