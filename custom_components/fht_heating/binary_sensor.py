from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

WINDOW_KEY = "window"


async def async_setup_entry(hass, config_entry, async_add_entities):
    fht_instances = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for dev_name, fht in fht_instances.items():
        entities.append(FhtWindowSensor(fht, dev_name))

    if entities:
        async_add_entities(entities, True)


class FhtWindowSensor(BinarySensorEntity):
    _attr_should_poll = True

    def __init__(self, fht, dev_name: str) -> None:
        self._fht = fht
        self._address = getattr(fht, "address", dev_name)
        self._dev_name = dev_name

        self._attr_name = f"{self._dev_name} Window Sensor"
        self._attr_unique_id = f"{self._address}_{self._dev_name}_window"
        self._state = None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._address}_{self._dev_name}")},  # gleich wie Climate
            name=f"FHT {self._dev_name}",
            manufacturer="FHT",
            model="Thermostat",
        )

    @property
    def is_on(self):
        # "open" = True, "closed" = False
        return str(self._state).strip().lower() == "open"

    async def async_update(self):
        try:
            value = await self.hass.async_add_executor_job(self._fht.get_value, WINDOW_KEY)
            s = str(value).strip().lower() if value is not None else ""
            if s in ("1", "open", "offen"):
                self._state = "open"
                self._attr_available = True
            elif s in ("0", "closed", "geschlossen"):
                self._state = "closed"
                self._attr_available = True
            else:
                self._state = None
                self._attr_available = False
        except Exception:
            self._state = None
            self._attr_available = False
