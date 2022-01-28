"""
Module to parse and extract data from AnimSchool picker file.
This works for Animschool until 2021 release.

PKR file structure description:

    -- header --
    4 bytes (singed int): Picker Version.
    4 bytes (singed int): Title number (x) of bytes length.
    x bytes (hex text): Title.

    -- PNG data --
    ...

    --- buttons ---
    4 bytes (singed int): Number of buttons

    -- Button array --
    for _ in range(number_of_buttons)
        - 4 bytes (singed int): Button id as signed int.
        - 4 bytes (singed int): Center position X.
        - 4 bytes (singed int): Center position Y.
        - 4 bytes (singed int):
                Size for old AnimSchool versions (4 and older)
                This is still there but unused in 2021 version.
        - 4 bytes (singed int): Width.
        - 4 bytes (singed int): Height.
        - 4 bytes (bool): Button type.
                True = Command button.
                False = Selection button.
        - 4 bytes (bool): Languages used for command button.
                True = Python.
                False = Mel.
        - 4 bytes (hex __RRGGBB): Background color.
        - 4 bytes (hex __RRGGBB): Text color.
        - 4 bytes (singed int): Label number (x) of bytes length.
        - x bytes (hexa text): Label.
        - 4 bytes (singed int): Number (x) of targets.
                This is automatically 1 for command button

        for _ in range(number_of_targets):
            - 4 bytes (singed int): Target name number (x) of bytes length.
            - x bytes (hexa text): Target name.


The script export pkr data in 3 different objects:

    PNG data:
        This is a one to one of the png binari data encapsulated in the pkr
        file.

    Title:
        As simple string

    Buttons:
        Translate the binari buttons as readable python dict!
        {
            "id": int,
            "x": int,
            "y": int,
            "w": int,
            "h": int,
            "action": str: "select" | "command",
            "lang": str: "mel" | "python",
            "bgcolor": [r:int, g:int, b:int],
            "txtcolor": [r:int, g:int, b:int],
            "label": str,
            "targets": List[str]
        }

"""

from binascii import hexlify, unhexlify
import json
import os

PNG_HEADER = b'89504e470d0a1a0a'
PNG_FOOTER = b'ae426082'


def split_data(content, number_of_bytes=4):
    if isinstance(number_of_bytes, bytes):
        number_of_bytes = int(number_of_bytes, 16)
    return content[:number_of_bytes * 2], content[number_of_bytes * 2:]


def bytes_to_string(stringdata):
    return ''.join(
        b.decode('cp1252')
        for b in unhexlify(stringdata).split(b'\x00'))


def bytes_to_int(i):
    if i[:4] == b'00' * 2:
        return int(i, 16)
    elif i[:4] == b'ff' * 2:
        return -65535 + int(i[-4:], 16)
    raise Exception('Count not interpret data as int')


def print_(data, max_bytes=64):
    string = repr(data)[2:-1][:max_bytes * 2]
    beautified = ''
    for i in range(len(string)):
        beautified += string[i].upper()
        if i % 2:
            beautified += ' '
        if (i + 1) % 16 == 0 and i != 0:
            beautified += '\n'
    print(beautified)


def bytes_to_rgb(data):
    data = int(data, 16)
    b = data & 255
    g = (data >> 8) & 255
    r = (data >> 16) & 255
    return r, g, b


def extract_string(data):
    string_size, data = split_data(data)
    string, data = split_data(data, string_size)
    string = bytes_to_string(string)
    return string, data


def extract_png_data(data):
    png_len_size, data = split_data(data)
    png_len_size = bytes_to_int(png_len_size)

    if not png_len_size:
        return None, data

    png_len, data = split_data(data, png_len_size)
    png_len = int(bytes_to_string(png_len))  # lol
    if png_len == 0:
        _, data = split_data(data, 4)  # remove some leftover data
        return None, data

    _, data = split_data(data, 4)
    png_end = int((data.find(PNG_FOOTER) + len(PNG_FOOTER)) / 2)
    return split_data(data, png_end)


def extract_button_targets(data):
    number_of_targets, data = split_data(data)
    targets = []
    number_of_targets = int(number_of_targets, 16)
    for _ in range(number_of_targets):
        target_name, data = extract_string(data)
        targets.append(target_name)
    return targets, data


def extract_button_data(data, version=5, verbose=True):
    button_id, data = split_data(data)
    button_id = bytes_to_int(button_id)
    if verbose:
        print('Button #{button_id}'.format(button_id=button_id))
    x, data = split_data(data)
    x = bytes_to_int(x)
    y, data = split_data(data)
    y = bytes_to_int(y)
    old_height, data = split_data(data)
    if version > 4:
        width, data = split_data(data)
        width = bytes_to_int(width)
        height, data = split_data(data)
        height = bytes_to_int(height)
    else:
        width, height = bytes_to_int(old_height), bytes_to_int(old_height)
    action, data = split_data(data)
    action = bytes_to_int(action)
    assert action in [0, 1]
    action = 'command' if action else 'select'
    lang, data = split_data(data)
    lang = bytes_to_int(lang)
    assert lang in [0, 1]
    lang = 'python' if lang else 'mel'
    bgcolor, data = split_data(data)
    bgcolor = bytes_to_rgb(bgcolor)
    txtcolor, data = split_data(data)
    txtcolor = bytes_to_rgb(txtcolor)
    label_size, data = split_data(data)
    if label_size == b'ff' * 4:
        label = ''
    else:
        label, data = split_data(data, label_size)
        label = bytes_to_string(label)
    targets, data = extract_button_targets(data)
    button = dict(
        id=button_id, x=x, y=y, w=width, h=height, action=action,
        lang=lang, bgcolor=bgcolor, txtcolor=txtcolor, label=label,
        targets=targets)
    return button, data


def parse_animschool_picker(picker_path, verbose=False):
    with open(picker_path, 'rb') as file:
        data = hexlify(file.read())

    # Get version
    version, data = split_data(data)
    version = bytes_to_int(version)
    print("this picker is build with AnimSchool v" + str(version))

    # Get title
    title, data = extract_string(data)
    if verbose:
        print('Title: "{title}"'.format(title=title))

    # Extract PNG
    png_data, data = extract_png_data(data)
    if verbose and png_data:
        print('PNG data found')

    # Get number of buttons
    number_of_buttons, data = split_data(data)
    number_of_buttons = int(number_of_buttons, 16)
    if verbose:
        print('Number of buttons: "{num}"'.format(num=number_of_buttons))

    # Parse buttons one by one:
    buttons = []
    while data:
        button, data = extract_button_data(data, version, verbose)
        buttons.append(button)

    if len(buttons) != number_of_buttons:
        raise Exception('Parsing buttons went wrong.')

    return title, buttons, png_data


def extract_to_files(pkr_path, verbose=False):
    """
    Extract data and image to .json and .png (if any) next to the .pkr
    """
    title, buttons, png_data = parse_animschool_picker(pkr_path, verbose)
    # Save to json
    with open(pkr_path + '.json', 'w') as f:
        json.dump([title, buttons], f, indent=4)
    # Write PNG to file:
    png_path = pkr_path + '.png'
    if png_data and not os.path.exists(png_path):
        save_png(png_data, png_path)
    return title, buttons, png_data


def save_png(png_data, dst):
    print('Saving PNG to "{dst}"'.format(dst=dst))
    with open(dst, 'wb') as f:
        f.write(unhexlify(png_data))


if __name__ == '__main__':
    import sys
    arg = sys.argv[-1]
    if arg == 'dir':
        # Extract json and png for all .pkr files in current dir:
        import glob
        for pkr_path in glob.glob('./*.pkr'):
            print(os.path.basename(pkr_path))
            try:
                extract_to_files(pkr_path)
            except BaseException:
                print('Failed to parse {pkr_path}'.format(pkr_path=pkr_path))
    elif arg.endswith('.pkr') and os.path.exists(arg):
        # Extract given path to json and png:
        import pprint
        print('Parsing {arg}'.format(arg=arg))
        title, buttons, png_data = extract_to_files(arg, verbose=True)
        print(title)
        pprint.pprint(buttons)
