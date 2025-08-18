from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.components.climate import (
    ClimateEntity,
    PLATFORM_SCHEMA,
)
from homeassistant.components.climate.const import (
    HVACMode,
    ClimateEntityFeature,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.helpers import config_validation as cv

from .const import DEV_NAME, ADDRESS
from .fht import Fht

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(DEV_NAME): cv.string,
        vol.Required(ADDRESS): cv.string,
    }
)


async def async_setup_platform(
    hass, config, async_add_entities, discovery_info=None
):
    async_add_entities([FhtDevice(config[ADDRESS], config[DEV_NAME])])


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([FhtDevice(entry.data[ADDRESS], entry.data[DEV_NAME])])


class FhtDevice(ClimateEntity):
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_max_temp = 30
    _attr_min_temp = 6
    _attr_target_temperature_step = 0.5
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, address: str, dev_name: str):
        self._attr_name = dev_name
        self._attr_address = address
        self._attr_unique_id = dev_name
        self._attr_hvac_mode = HVACMode.HEAT
        self._fht_data_handler = Fht(self._attr_address, self._attr_name)

    @property
    def unique_id(self):  # type: ignore[override]
        return self._attr_unique_id

    @property
    def hvac_mode(self):
        return HVACMode.HEAT

    @property
    def icon(self):
        return (
            "mdi:radiator"
            if self.hvac_mode == HVACMode.HEAT
            else "mdi:radiator-off"
        )

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        self._attr_hvac_mode = hvac_mode

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

    async def async_set_temperature(self, **kwargs):
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        await self.hass.async_add_executor_job(
            self._fht_data_handler.set_value,
            "desired-temp",
            temperature,
        )
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_update(self):
        await self.hass.async_add_executor_job(
            self._fht_data_handler.get_value,
            "desired-temp",
        )
        await self.hass.async_add_executor_job(
            self._fht_data_handler.get_value,
            "measured-temp",
        )
        await self.hass.async_add_executor_job(
            self._fht_data_handler.get_value,
            "actuator",
        )

    async def async_added_to_hass(self):
        await self.async_update()
