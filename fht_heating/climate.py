from __future__ import annotations

import logging
import voluptuous as vol
from homeassistant.components.climate import ClimateEntity, PLATFORM_SCHEMA
from homeassistant.components.climate.const import (
    HVACMode,
    ClimateEntityFeature,
    HVACAction,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DEV_NAME, ADDRESS, DOMAIN
from .fht import Fht

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(DEV_NAME): cv.string,
        vol.Required(ADDRESS): cv.string,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    async_add_entities([FhtDevice(config[ADDRESS], config[DEV_NAME])])


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([FhtDevice(entry.data[ADDRESS], entry.data[DEV_NAME])])


class FhtDevice(ClimateEntity):
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_max_temp = 30.0
    _attr_min_temp = 6.0
    _attr_target_temperature_step = 0.5
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_should_poll = True  # <-- wichtig, sonst wird async_update() nie aufgerufen

    def __init__(self, address: str, dev_name: str):
        self._attr_name = dev_name
        self._attr_address = address
        self._attr_unique_id = f"{address}_{dev_name.lower().replace(' ', '_')}"  # stabil genug
        self._attr_hvac_mode = HVACMode.HEAT
        self._fht_data_handler = Fht(self._attr_address, self._attr_name)

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=self._attr_name,
            manufacturer="FHT",
            model="Thermostat",
        )

    # --- State ---
    @property
    def hvac_mode(self) -> HVACMode:
        # vorher: immer HEAT -> falsch
        return self._attr_hvac_mode

    @property
    def hvac_action(self) -> HVACAction | None:
        # Nutze actuator und/oder Temperaturen für sinnvolle Anzeige
        if self._attr_hvac_mode == HVACMode.OFF:
            return HVACAction.OFF

        act = self._fht_data_handler.get_cached_value("actuator")
        try:
            act = float(act) if act is not None else None
        except (TypeError, ValueError):
            act = None

        if act is not None:
            return HVACAction.HEATING if act > 0 else HVACAction.IDLE

        cur = self.current_temperature
        tgt = self.target_temperature
        if cur is None or tgt is None:
            return HVACAction.IDLE
        return HVACAction.HEATING if cur < tgt else HVACAction.IDLE

    @property
    def icon(self) -> str:
        return "mdi:radiator" if self._attr_hvac_mode == HVACMode.HEAT else "mdi:radiator-off"

    # --- Temps ---
    @property
    def current_temperature(self):
        value = self._fht_data_handler.get_cached_value("measured-temp")
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            _LOGGER.debug("Invalid measured-temp value: %s", value)
            return None

    @property
    def target_temperature(self):
        value = self._fht_data_handler.get_cached_value("desired-temp")
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            _LOGGER.debug("Invalid desired-temp value: %s", value)
            return None

    # --- Commands ---
    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode not in (HVACMode.HEAT, HVACMode.OFF):
            _LOGGER.debug("Unsupported hvac_mode requested: %s", hvac_mode)
            return
        self._attr_hvac_mode = hvac_mode
        # Falls dein FHT echtes OFF kennt, hier den Gerätemodus setzen:
        # await self.hass.async_add_executor_job(self._fht_data_handler.set_value, "mode",
        #     "heat" if hvac_mode == HVACMode.HEAT else "off")
        self.async_write_ha_state()  # <-- UI updaten

    async def async_set_temperature(self, **kwargs):
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        # clamp + quantisieren
        temp = float(temperature)
        temp = max(self.min_temp, min(self.max_temp, temp))
        step = self._attr_target_temperature_step or 0.5
        temp = round(temp / step) * step

        await self.hass.async_add_executor_job(
            self._fht_data_handler.set_value,
            "desired-temp",
            temp,
        )

        # Heat-only: Zieltemp setzen impliziert HEAT
        if self._attr_hvac_mode != HVACMode.HEAT:
            self._attr_hvac_mode = HVACMode.HEAT

        self.async_write_ha_state()  # <-- sofortiges UI-Feedback

    # --- Polling ---
    async def async_update(self):
        # Diese Aufrufe sollen die Cache-Werte aktualisieren
        await self.hass.async_add_executor_job(self._fht_data_handler.get_value, "desired-temp")
        await self.hass.async_add_executor_job(self._fht_data_handler.get_value, "measured-temp")
        await self.hass.async_add_executor_job(self._fht_data_handler.get_value, "actuator")

    async def async_added_to_hass(self):
        await self.async_update()

    @property
    def extra_state_attributes(self):
        # Optional: rohen actuator-Wert sichtbar machen (Debug/Diagnose)
        return {
            "address": self._attr_address,
            "actuator_raw": self._fht_data_handler.get_cached_value("actuator"),
        }
