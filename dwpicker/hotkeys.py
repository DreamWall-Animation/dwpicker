
from maya import cmds
from dwpicker.optionvar import save_optionvar, DEFAULT_HOTKEYS


def get_hotkeys_config():
    value = cmds.optionVar(query=DEFAULT_HOTKEYS)
    return {
        entry.split('=')[0]: {
            'enabled': bool(int(entry.split('=')[-1].split(',')[-1])),
            'key_sequence': entry.split('=')[-1].split(',')[0]}
        for entry in value.split(';')}


def set_hotkey_config(function, key_sequence, enabled):
    config = get_hotkeys_config()
    config[function] = {'enabled': enabled, 'key_sequence': key_sequence}
    save_hotkey_config(config)


def save_hotkey_config(config):
    value = ';'.join([
        f'{function}={data["key_sequence"]},{int(data["enabled"])}'
        for function, data in config.items()])
    save_optionvar(DEFAULT_HOTKEYS, value)
