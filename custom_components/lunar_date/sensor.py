"""
Sensor to indicate today's lunar date.

"""

from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.core import callback
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
from homeassistant.helpers.event import async_track_point_in_utc_time
from .vietnamese_lunar_calendar import S2L

import datetime

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Lunar Date'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Time and Date sensor."""
    if hass.config.time_zone is None:
        _LOGGER.error("Timezone is not set in Home Assistant configuration")
        return False

    sensor_name = config.get(CONF_NAME)
    device = LunarDateSensor(hass, sensor_name)

    async_track_point_in_utc_time(
        hass, device.point_in_time_listener, device.get_next_interval())

    async_add_entities([device], True)

class LunarDateSensor(Entity):
    """Implementation of a Time and Date sensor."""

    def __init__(self, hass, name):
        """Initialize the sensor."""
        self._name = name
        self._state = None
        self.hass = hass
        self._update_internal_state(dt_util.utcnow())

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return 'mdi:calendar-star'

    @property
    def device_state_attributes(self):
        """Return the attribute(s) of the sensor"""
        return self._attribute

    def get_next_interval(self, now=None):
        """Compute next time an update should occur."""
        if now is None:
            now = dt_util.utcnow()
        now = dt_util.start_of_local_day(dt_util.as_local(now))
        return now + timedelta(seconds=86400)

    def _update_internal_state(self, time_date):
        date = dt_util.as_local(time_date).date()
        converted = S2L(date.day, date.month, date.year)
        lunar_date = "%04d-%02d-%02d" % (converted[2], converted[1], converted[0])
        self._state = lunar_date
        self._attribute = {}

    @callback
    def point_in_time_listener(self, time_date):
        """Get the latest data and update state."""
        self._update_internal_state(time_date)
        self.async_schedule_update_ha_state()
        async_track_point_in_utc_time(
            self.hass, self.point_in_time_listener, self.get_next_interval())
