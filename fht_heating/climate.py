from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.components.climate import ClimateEntity, PLATFORM_SCHEMA
from homeassistant.components.climate.const import (
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    TEMP_CELSIUS,
)
from homeassistant.helpers import config_validation as cv

from .const import (
    DEV_NAME,
    ADDRESS
)
from .fht import Fht

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(DEV_NAME): cv.string,
        vol.Required(ADDRESS): cv.string
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    _setup(hass, add_entities, config[ADDRESS], config[DEV_NAME])


def setup_entry(hass, entry, add_entities):
    _setup(hass, add_entities, entry.data[ADDRESS], entry.data[DEV_NAME])


def _setup(hass, add_entities, address, dev_name):
    dev = []
    dev.append(FhtDevice(address, dev_name))
    add_entities(dev)


class FhtDevice(ClimateEntity):
    _attr_hvac_modes = []
    _attr_max_temp = 30
    _attr_min_temp = 6
    _attr_target_temperature_step = 0.5
    _attr_dev_name = ""
    _attr_address = ""

    _attr_supported_features = SUPPORT_TARGET_TEMPERATURE
    _attr_temperature_unit = TEMP_CELSIUS

    def __init__(self, address, dev_name):
        self._attr_dev_name = dev_name
        self._attr_address = address
        self._fht_data_handler = Fht(self._attr_address, self._attr_dev_name)
        self.update()

    @property
    def name(self):
        return self._attr_dev_name

    @property
    def hvac_mode(self):
        pass

    @property
    def icon(self):
        if self.hvac_mode == HVAC_MODE_HEAT:
            return "mdi:radiator"
        return "mdi:radiator-off"

    def set_hvac_mode(self, hvac_mode) -> None:
        pass

    @property
    def current_temperature(self):
        return float(self._fht_data_handler.get_cached_value("measured-temp"))

    @property
    def target_temperature(self):
        self._attr_last_temp = self._fht_data_handler.get_cached_value("desired-temp")
        return float(self._fht_data_handler.get_cached_value("desired-temp"))

    def set_temperature(self, **kwargs):
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        self._attr_last_temp = temperature
        self._fht_data_handler.set_value("desired-temp", temperature)
        self.set_hvac_mode(HVAC_MODE_HEAT)

    def update(self):
        self._fht_data_handler.get_value("desired-temp")
        self._fht_data_handler.get_value("measured-temp")
        self._fht_data_handler.get_value("actuator")
