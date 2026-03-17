import logging
from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
PERIODS = ["from1", "to1", "from2", "to2"]


async def async_setup_entry(hass, config_entry, async_add_entities):
    fht_instances = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for dev_name, fht in fht_instances.items():
        for day in DAYS:
            for period in PERIODS:
                key = f"{day}-{period}"
                entities.append(FhtScheduleTime(fht, dev_name, key))

    if entities:
        async_add_entities(entities, True)


class FhtScheduleTime(TimeEntity):
    _attr_should_poll = True

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
                s = str(value).strip()
                if ":" in s:
                    # 24:00 is not valid datetime.time in python natively (0-23).
                    # HA time entities handle up to 23:59:59 usually. Let's clamp it if it's 24:00.
                    parts = s.split(":")
                    if len(parts) >= 2:
                        hr = int(parts[0])
                        mn = int(parts[1])
                        if hr == 24 and mn == 0:
                            hr = 23
                            mn = 59
                        self._attr_native_value = time(hour=hr, minute=mn)
                        self._attr_available = True
                        return

            self._attr_native_value = None
            # Do not set unavailable if reading fails, as not all devices have all slots active all the time, or it's unconfigured
            self._attr_available = True
        except Exception:
            self._attr_native_value = None
            self._attr_available = False

    async def async_set_value(self, value: time) -> None:
        if self._fht is None:
            return

        # FHEM FHT format is HH:MM. If user sets 23:59, we send 24:00 if they actually want midnight?
        # Standard time string is enough.
        # Format time to HH:MM string.
        time_str = value.strftime("%H:%M")

        def _set():
            return self._fht.set_value(self._key, time_str, bypass_cache=True)

        await self.hass.async_add_executor_job(_set)
        self._attr_native_value = value
        self.async_write_ha_state()
