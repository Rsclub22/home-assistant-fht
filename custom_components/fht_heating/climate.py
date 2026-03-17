from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVACMode,
    ClimateEntityFeature,
    HVACAction,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, DEV_NAME

_LOGGER = logging.getLogger(__name__)

MEASURED_TEMP = "measured-temp"
DESIRED_TEMP = "desired-temp"
MODE_KEY = "mode"
ACTUATOR_KEY = "actuator"



async def async_setup_entry(hass, config_entry, async_add_entities):
    fht_instances = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for dev_name, fht in fht_instances.items():
        _LOGGER.info("fht_heating.climate: add entity dev=%s", dev_name)
        entities.append(FhtClimate(fht, dev_name))

    if entities:
        async_add_entities(entities, True)


class FhtClimate(ClimateEntity):
    _attr_should_poll = True
    _attr_hvac_modes = [HVACMode.HEAT]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 7
    _attr_max_temp = 35
    _attr_available = True

    def __init__(self, fht, dev_name: str) -> None:
        # bevorzugt: geteilter Handler; Fallback: alte Signatur (address, dev_name)
        if hasattr(fht, "get_value") and hasattr(fht, "address"):
            self._fht = fht
            self._address = fht.address  # str
        else:
            self._fht = None
            self._address = fht          # str
        self._dev_name = dev_name

        # exakt wie gewünscht:
        self._attr_name = f"{self._dev_name}"
        self._attr_unique_id = f"{self._address}_{self._dev_name}"
        self._attr_hvac_action = HVACAction.IDLE
        self._attr_current_temperature = None
        self._attr_target_temperature = None

    async def async_added_to_hass(self) -> None:
        _LOGGER.info(
            "fht_heating.climate: added entity unique_id=%s dev=%s addr=%s has_handler=%s",
            self._attr_unique_id, self._dev_name, self._address, bool(self._fht),
        )

    @property
    def device_info(self) -> DeviceInfo:
        # gleicher Identifier wie Binary-Sensor -> ein Gerät
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._address}_{self._dev_name}")},
            name=f"{self._dev_name}",
            manufacturer="FHT",
            model="Thermostat",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "address": self._address,
            "pending_keys": list(getattr(self._fht, "_pending_values", {}).keys()) if self._fht else [],
            "actuator_raw": getattr(self, "_last_actuator", None),
        }

    async def async_update(self) -> None:
        if self._fht is None:
            if not getattr(self, "_warned_no_handler", False):
                _LOGGER.warning(
                    "fht_heating.climate: no handler bound; cannot update dev=%s addr=%s",
                    self._dev_name, self._address
                )
                self._warned_no_handler = True
            self._attr_available = False
            return

        def _read_all():
            gv = self._fht.get_value
            def safe(key):
                try:
                    return gv(key, force=False)  # normaler Read (Cache ok)
                except Exception as e:
                    return e
            return safe(MEASURED_TEMP), safe(DESIRED_TEMP), safe(MODE_KEY), safe(ACTUATOR_KEY)

        t_cur, t_set, mode, act = await self.hass.async_add_executor_job(_read_all)
        _LOGGER.debug("fht_heating.climate: read cur=%r set=%r mode=%r act=%r",
                      t_cur, t_set, mode, act)

        def _to_float(v):
            if isinstance(v, Exception) or v is None:
                return None
            try:
                s = str(v).replace("°C", "").strip()
                return float(s)
            except Exception:
                return None

        self._attr_current_temperature = _to_float(t_cur)
        self._attr_target_temperature = _to_float(t_set)

        self._attr_hvac_mode = HVACMode.HEAT

        act_val = None if isinstance(act, Exception) else act
        try:
            act_pct = float(str(act_val).replace("%", "").strip()) if act_val is not None else None
        except Exception:
            act_pct = None
        self._last_actuator = act_val
        self._attr_hvac_action = HVACAction.HEATING if (act_pct is not None and act_pct > 0) else HVACAction.IDLE

        self._attr_available = True

    async def async_set_temperature(self, **kwargs):
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None or self._fht is None:
            return

        def _set():
            # direkt – ohne Optimismus, ohne pending, ohne write-cache
            return self._fht.set_value(DESIRED_TEMP, temp, bypass_cache=True)

        await self.hass.async_add_executor_job(_set)
        # danach frisch lesen
        await self.async_update()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode):
        # Always HEAT mode now, no action required
        pass
