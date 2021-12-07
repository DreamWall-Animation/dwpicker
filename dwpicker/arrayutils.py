
def move_elements_to_array_end(array, elements):
    return [e for e in array if e not in elements] + [e for e in elements]


def move_elements_to_array_begin(array, elements):
    return [e for e in elements] + [e for e in array if e not in elements]


def move_up_array_elements(array, elements):
    for element in reversed(array):
        if element not in elements:
            continue
        index = array.index(element)
        if index == len(array):
            continue
        array.insert(index + 2, element)
        array.pop(index)


def move_down_array_elements(array, elements):
    for shape in array:
        if shape not in elements:
            continue
        index = array.index(shape)
        if index == 0:
            continue
        array.pop(index)
        array.insert(index - 1, shape)
