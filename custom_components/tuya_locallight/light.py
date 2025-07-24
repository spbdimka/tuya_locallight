import logging
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ATTR_COLOR_TEMP, SUPPORT_BRIGHTNESS, SUPPORT_COLOR_TEMP, LightEntity
)
from .const import DOMAIN
import functools

_LOGGER = logging.getLogger(__name__)


async def async_load_yaml_file(hass, path):
    import yaml
    return await hass.async_add_executor_job(
        functools.partial(_sync_load_yaml_file, path)
    )

def _sync_load_yaml_file(path):
    import yaml
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)



async def async_setup_entry(hass, entry, async_add_entities):
    gateway_conf = entry.data
    options = entry.options.get("devices", [])
    from .gateway import TuyaGateway
    import os, yaml

    gw = TuyaGateway(
        gateway_conf["gateway_id"],
        gateway_conf["gateway_ip"],
        gateway_conf["local_key"],
        port=gateway_conf.get("gateway_port", 6668),
    )

    # load profiles
    profiles = {}
    profiles = {}
    profdir = os.path.join(os.path.dirname(__file__), "devices")
    for fname in os.listdir(profdir):
        if fname.endswith(".yaml"):
            yaml_path = os.path.join(profdir, fname)
            profiles[fname[:-5]] = await async_load_yaml_file(hass, yaml_path)

    entities = []
    for device in options:
        profile = profiles[device["profile"]]
        bulb = gw.get_bulb(device["did"], device["cid"])
        entities.append(TuyaLocalLight(device, bulb, profile))
    async_add_entities(entities)

class TuyaLocalLight(LightEntity):
    def __init__(self, conf, bulb, profile):
        self._conf = conf
        self._dev = bulb
        self._profile = profile
        dps = {d["name"]: d["id"] for d in profile["primary_entity"]["dps"]}
        self._dps_switch = dps["switch"]
        self._dps_brightness = dps.get("brightness")
        self._dps_color_temp = dps.get("color_temp")
        self._name = conf["name"]

    @property
    def name(self):
        return self._name

    @property
    def supported_features(self):
        f = 0
        if self._dps_brightness:
            f |= SUPPORT_BRIGHTNESS
        if self._dps_color_temp:
            f |= SUPPORT_COLOR_TEMP
        return f

    @property
    def is_on(self):
        try:
            status = self._dev.status()
            return status["dps"].get(str(self._dps_switch), False)
        except Exception:
            return False

    @property
    def brightness(self):
        if self._dps_brightness:
            try:
                status = self._dev.status()
                v = status["dps"].get(str(self._dps_brightness))
                if v is not None:
                    # Преобразуй яркость к 0-255 если нужно
                    return int((v - 10) / (1000 - 10) * 255)
            except Exception:
                pass
        return None

    @property
    def color_temp(self):
        if self._dps_color_temp:
            try:
                status = self._dev.status()
                return status["dps"].get(str(self._dps_color_temp))
            except Exception:
                pass
        return None

    def turn_on(self, **kwargs):
        self._dev.set_value(self._dps_switch, True)
        if self._dps_brightness and ATTR_BRIGHTNESS in kwargs:
            v = int(kwargs[ATTR_BRIGHTNESS] / 255 * (1000 - 10) + 10)
            self._dev.set_value(self._dps_brightness, v)
        if self._dps_color_temp and ATTR_COLOR_TEMP in kwargs:
            self._dev.set_value(self._dps_color_temp, kwargs[ATTR_COLOR_TEMP])

    def turn_off(self, **kwargs):
        self._dev.set_value(self._dps_switch, False)
