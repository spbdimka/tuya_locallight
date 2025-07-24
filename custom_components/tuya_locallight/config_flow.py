import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import os
import yaml

from .const import (
    DOMAIN, CONF_GATEWAY_IP, CONF_GATEWAY_PORT, CONF_GATEWAY_ID, CONF_LOCAL_KEY,
    CONF_NAME, CONF_DID, CONF_CID, CONF_PROFILE,
)

def get_profiles():
    path = os.path.join(os.path.dirname(__file__), "devices")
    profiles = []
    for fname in os.listdir(path):
        if fname.endswith(".yaml"):
            with open(os.path.join(path, fname), encoding="utf-8") as f:
                yml = yaml.safe_load(f)
                profiles.append((fname[:-5], yml.get("name", fname[:-5])))
    return profiles

class TuyaLocalLightConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="Tuya LocalLight Gateway", data=user_input)
        schema = vol.Schema({
            vol.Required(CONF_GATEWAY_IP): str,
            vol.Required(CONF_GATEWAY_ID): str,
            vol.Required(CONF_LOCAL_KEY): str,
            vol.Optional(CONF_GATEWAY_PORT, default=6668): int,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return TuyaLocalLightOptionsFlowHandler(config_entry.entry_id)

class TuyaLocalLightOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, entry_id):
        self.entry_id = entry_id

    @property
    def config_entry(self):
        entries = self.hass.config_entries.async_entries(DOMAIN)
        for entry in entries:
            if entry.entry_id == self.entry_id:
                return entry
        return None

    async def async_step_init(self, user_input=None):
        devices = list(self.config_entry.options.get("devices", []))
        device_list = "\n".join(
            f"- {d['name']} (did: {d['did']}, cid: {d['cid']}, profile: {d['profile']})" for d in devices
        ) or "Нет добавленных устройств"
        if user_input is not None:
            # Жмём "Добавить новое" — переходим к add_device
            return await self.async_step_add_device()
        return self.async_show_form(
            step_id="init",
            description_placeholders={"devices": device_list},
            data_schema=vol.Schema({}),  # пустая форма, только список и кнопка "Далее"
        )

    async def async_step_add_device(self, user_input=None):
        profiles = get_profiles()
        schema = vol.Schema({
            vol.Required(CONF_NAME): str,
            vol.Required(CONF_DID): str,
            vol.Required(CONF_CID): str,
            vol.Required(CONF_PROFILE, default=profiles[0][0]): vol.In({p[0]: p[1] for p in profiles}),
        })
        if user_input is not None:
            devices = list(self.config_entry.options.get("devices", []))
            devices.append(user_input)
            return self.async_create_entry(title="Devices", data={"devices": devices})
        return self.async_show_form(step_id="add_device", data_schema=schema)
