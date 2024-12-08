
# Dreamwall Picker

Animation picker for Audodesk Maya 2017 (or higher)

Authors: Lionel Brouyère, Olivier Evers
> This tool is a fork of Hotbox Designer (Lionel Brouyère).
> A menus, markmenu and hotbox designer cross DCC.
> https://github.com/luckylyk/hotbox_designer


### Features
- Easy and fast picker creation.
- Import AnimSchool pickers done before 2022.
- Store picker in maya scene.
- Advanced picker editor.
- Does whatever AnimSchool picker does and many more ...
<center><img  src="https://raw.githubusercontent.com/DreamWall-Animation/dwpicker/main/screenshots/picker.gif"  alt="drawing"  align="center"  width="250"/> <img  src="https://s10.gifyu.com/images/createbuttons.gif"  alt="drawing"  align="center"  width="400"/>
<img  src="https://raw.githubusercontent.com/DreamWall-Animation/dwpicker/main/screenshots/editor.gif"  alt="drawing"  align="center"  width="370"/>


### Installation
place the folder named "dwpicker" (not dwpicker-main) into the maya script folder

| os       | path                                                  |
| ------   | ------                                                |
| linux    | ~/<username>/maya/scripts                             |
| windows  | \Users\<username>\Documents\maya\scripts              |
| mac os x | ~<username>/Library/Preferences/Autodesk/maya/scripts |


### How to run

```python
import dwpicker
dwpicker.show()
```


### FAQ

#### Does it runs with Maya 2025 ?
Yes ! (since version 0.11.2). But still a workaround implementation.
Check this fork to get a proper maya 25 release:
https://github.com/jdrese/dwpicker

#### My rig contains multiples namespaces or has nested namespace.
This function isn't currently supported. The picker was designed to offer flexibility with a single level of namespace, allowing for one picker to serve multiple instances of the same rig within a scene. Switching the picker's namespace is straightforward. However, despite our efforts to maintain this flexibility, we haven't yet discovered a straightforward method to support nested namespaces. While there are potential solutions, they all appear rather complex to implement and understand for the user. Perhaps a brilliant idea will emerge in the future, but for now, this feature is not on our roadmap.
We welcome any suggestions you may have!

#### Why can't I utilize relative paths for my image files?
When you open a picker, it imports the files directly into the scene, losing the original path reference. We opt to import the data rather than reference them directly, as many animators prefer to customize the picker for their specific shot needs (e.i. adding a button for a prop or constraint unique to a particular shot). This approach complicates the usage of relative paths."

#### How to preserve images when I share my picker to another person, storing his files somewhere else?
Despite the lacks of support for relative paths, similar to any other Maya path attribute, you can include environment variable in the path. Setting up a custom environment variable might be complexe. Therefore, we propose a default variable one: DWPICKER_PROJECT_DIRECTORY, available in the picker preferences window.

If you configure DWPICKER_PROJECT_DIRECTORY=`c:/my_pickers` and you have an image with this path:
`c:/my_pickers/my_character/background.png`, type this to make the path dynamic: `$DWPICKER_PROJECT_DIRECTORY/my_character/background.png`
When you select a file from the UI, it automatically creates the path containing the variable.


### Support
Preferably, post an issue on the github page.\
If you don't hold a github account, you can send a mail to `brouyere |a| dreamwall.be`.\
Please start you mail subject by ***[dwpicker]***. (Note that the replying delay can be longer using that way).
