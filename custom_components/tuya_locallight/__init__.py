from .const import DOMAIN

async def async_setup(hass, config):
    return True

async def async_setup_entry(hass, entry):
    await hass.config_entries.async_forward_entry_setup(entry, "light")
    return True

async def async_unload_entry(hass, entry):
    return True
