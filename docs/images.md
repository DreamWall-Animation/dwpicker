
# Relatives Images Paths

Despite the lacks of support for relative paths, similar to any other Maya path attribute, you can include environment variable in the path. Setting up a custom environment variable might be complexe. Therefore, we propose a default variable one: DWPICKER_PROJECT_DIRECTORY, available in the picker preferences window.

If you configure DWPICKER_PROJECT_DIRECTORY=`c:/my_pickers` and you have an image with this path:
`c:/my_pickers/my_character/background.png`, type this to make the path dynamic: `$DWPICKER_PROJECT_DIRECTORY/my_character/background.png`
When you select a file from the UI, it automatically creates the path containing the variable.
