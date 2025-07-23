import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_GATEWAY_IP, CONF_GATEWAY_PORT, CONF_LOCAL_KEY

class TuyaLocalLightConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # тут можно проверить соединение с шлюзом, если хочешь
            return self.async_create_entry(title="Tuya LocalLight Gateway", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_GATEWAY_IP): str,
            vol.Required(CONF_GATEWAY_PORT, default=6668): int,
            vol.Required(CONF_LOCAL_KEY): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
