
from maya import cmds
from dwpicker.optionvar import save_optionvar, DEFAULT_HOTKEYS, OPTIONVARS


def get_hotkeys_config():
    # For config retro compatibility, we always ensure that default value is
    # set in case of new shortcut added in the system. We also ensure that old
    # shortcut is going to be removed from the config.
    default = build_config_from_string(OPTIONVARS[DEFAULT_HOTKEYS])
    saved = build_config_from_string(cmds.optionVar(query=DEFAULT_HOTKEYS))
    for key in default.keys():
        if key in saved:
            default[key] = saved[key]
    return default


def build_config_from_string(value):
    config = {}
    for entry in value.split(';'):
        function_name = entry.split('=')[0]
        enabled = bool(int(entry.split('=')[-1].split(',')[-1]))
        key_sequence = entry.split('=')[-1].split(',')[0]
        config[function_name] = {
            'enabled': enabled if key_sequence != 'None' else False,
            'key_sequence': None if key_sequence == 'None' else key_sequence}
    return config


def set_hotkey_config(function, key_sequence, enabled):
    config = get_hotkeys_config()
    config[function] = {'enabled': enabled, 'key_sequence': key_sequence}
    save_hotkey_config(config)


def save_hotkey_config(config):
    value = ';'.join([
        '{0}={1},{2}'.format(function, data['key_sequence'], int(data['enabled']))
        for function, data in config.items()])
    save_optionvar(DEFAULT_HOTKEYS, value)
