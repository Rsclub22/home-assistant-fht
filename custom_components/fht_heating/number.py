import logging

from homeassistant.components.number import NumberEntity, NumberDeviceClass
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

KEYS = ["day-temp", "night-temp"]


async def async_setup_entry(hass, config_entry, async_add_entities):
    fht_instances = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for dev_name, fht in fht_instances.items():
        for key in KEYS:
            entities.append(FhtNumberEntity(fht, dev_name, key))

    if entities:
        async_add_entities(entities, True)


class FhtNumberEntity(NumberEntity):
    _attr_should_poll = True
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 5.5
    _attr_native_max_value = 30.0
    _attr_native_step = 0.5

    def __init__(self, fht, dev_name: str, key: str) -> None:
        self._fht = fht
        self._address = getattr(fht, "address", dev_name)
        self._dev_name = dev_name
        self._key = key

        self._attr_name = f"{self._dev_name} {self._key.replace('-', ' ').title()}"
        self._attr_unique_id = f"{self._address}_{self._dev_name}_{self._key}"
        self._attr_native_value = None

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
            value = await self.hass.async_add_executor_job(self._fht.get_value, self._key)
            if value:
                s = str(value).strip().replace("°C", "")
                self._attr_native_value = float(s)
                self._attr_available = True
            else:
                self._attr_native_value = None
                self._attr_available = True
        except Exception:
            self._attr_native_value = None
            self._attr_available = False

    async def async_set_native_value(self, value: float) -> None:
        if self._fht is None:
            return

        def _set():
            return self._fht.set_value(self._key, value, bypass_cache=True)

        await self.hass.async_add_executor_job(_set)
        self._attr_native_value = value
        self.async_write_ha_state()
