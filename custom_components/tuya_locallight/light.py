import logging
import os
import functools
from homeassistant.components.light import (
    LightEntity, ATTR_BRIGHTNESS, ATTR_COLOR_TEMP_KELVIN
)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_listdir(hass, path):
    return await hass.async_add_executor_job(functools.partial(os.listdir, path))

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
    devices = entry.options.get("devices", [])
    from .gateway import TuyaGateway

    gw = TuyaGateway(
        gateway_conf["gateway_id"],
        gateway_conf["gateway_ip"],
        gateway_conf["local_key"],
        port=gateway_conf.get("gateway_port", 6668),
    )

    # Асинхронно загружаем YAML-профили
    profiles = {}
    profdir = os.path.join(os.path.dirname(__file__), "devices")
    for fname in await async_listdir(hass, profdir):
        if fname.endswith(".yaml"):
            yaml_path = os.path.join(profdir, fname)
            profiles[fname[:-5]] = await async_load_yaml_file(hass, yaml_path)

    entities = []
    for device in devices:
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

        self._attr_supported_color_modes = self.supported_color_modes
        self._attr_color_mode = None

    @property
    def name(self):
        return self._name

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
    def color_temp_kelvin(self):
        if self._dps_color_temp:
            try:
                status = self._dev.status()
                return status["dps"].get(str(self._dps_color_temp))
            except Exception:
                pass
        return None

    @property
    def supported_color_modes(self):
        modes = []
        if self._dps_color_temp:
            modes.append("color_temp")
        elif self._dps_brightness:
            modes.append("brightness")
        else:
            modes.append("onoff")
        return modes

    def turn_on(self, **kwargs):
        self._dev.set_value(self._dps_switch, True)
        if self._dps_brightness and ATTR_BRIGHTNESS in kwargs:
            v = int(kwargs[ATTR_BRIGHTNESS] / 255 * (1000 - 10) + 10)
            self._dev.set_value(self._dps_brightness, v)
        if self._dps_color_temp and ATTR_COLOR_TEMP_KELVIN in kwargs:
            self._dev.set_value(self._dps_color_temp, kwargs[ATTR_COLOR_TEMP_KELVIN])

    def turn_off(self, **kwargs):
        self._dev.set_value(self._dps_switch, False)
