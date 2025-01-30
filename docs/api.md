# `dwpicker` Module

## Overview

This module provides functionality for managing and interacting with the DwPicker tool in Autodesk Maya. DwPicker allows users to work with pickers for organizing and controlling elements within a scene.

## Core Functions

### `show`
```python
def show(
    editable=True,
    pickers=None,
    ignore_scene_pickers=False,
    replace_namespace_function=None,
    list_namespaces_function=None):
```
**Description**: Displays the DwPicker UI, optionally loading pickers or customizing namespace behaviors.

**Arguments**:
- `editable` (bool): Allows local edits without affecting the original file.
- `pickers` (list[str]): File paths to specific pickers to load.
- `ignore_scene_pickers` (bool): Ignores existing scene pickers.
- `replace_namespace_function` (callable): Custom namespace replacement function.
- `list_namespaces_function` (callable): Custom function to list scene namespaces.

**Returns**:
- A `DwPicker` instance.

---

### `toggle`
```python
def toggle():
```
**Description**: Toggles the visibility of the DwPicker UI.

---

### `close`
```python
def close():
```
**Description**: Closes the DwPicker UI and unregisters all associated callbacks.

---

## Utility Classes

### `disable`
```python
class disable():
```
**Description**: Context manager to temporarily disable picker callbacks, useful for preventing performance issues during batch operations.

**Methods**:
- `__enter__`: Unregisters callbacks.
- `__exit__`: Re-registers callbacks.

---

## Additional Functions

### `current`
```python
def current():
```
**Description**: Retrieves the currently visible picker widget in the main tab.

---

### `refresh`
```python
def refresh():
```
**Description**: Refreshes the picker UI after manual changes to the scene data.

---

### `open_picker_file`
```python
def open_picker_file(filepath):
```
**Description**: Programmatically adds a picker file to the DwPicker UI.

**Arguments**:
- `filepath` (str): Path to the picker file.

---

### `current_namespace`
```python
def current_namespace():
```
**Description**: Retrieves the namespace of the currently displayed picker.

**Returns**:
- A namespace string.

---

### `set_layer_visible`
```python
def set_layer_visible(layername, visible=True):
```
**Description**: Toggles the visibility of a specified layer in the current picker.

**Arguments**:
- `layername` (str): The name of the layer.
- `visible` (bool): Visibility state (default is `True`).

---

### `toggle_layer_visibility`
```python
def toggle_layer_visibility(layername):
```
**Description**: Toggles the visibility state of a specific layer in the current picker.

**Arguments**:
- `layername` (str): The name of the layer.

---

### `get_shape`
```python
def get_shape(shape_id):
```
**Description**: Retrieves a specific shape from the picker by its ID.

**Arguments**:
- `shape_id` (str): The ID of the shape to retrieve.

**Returns**:
- The shape object if found, otherwise `None`.

---
