# MIT License
#
# (C) Copyright 2022 Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# Contains a utility function for merging two dictionaries together.

from copy import deepcopy


def _dict_contains_no_subdicts_or_lists(dict_to_check):
    """Return true if the given dict has no list or dictionary values.

    Helper for merge_dict.

    Args:
        dict_to_check (dict): The dict to check for list/dictionary values.

    Returns:
        bool: True if the dict has no dict or list values.
    """
    return not any(isinstance(value, dict) or isinstance(value, list)
                   for value in dict_to_check.values())


def _values_are_dicts(*values):
    """Return true if all given values are dict type.

    Helper for merge_dict.

    Args:
        *values: A list of values to check.

    Returns:
        bool: True if the values are dicts.
    """
    return all(isinstance(v, dict) for v in values)


def _values_are_lists(*values):
    """Return true if all values are list type.

    Helper for merge_dict.

    Args:
        *values: A list of values to check.

    Returns:
        bool: True if the values are lists.
    """
    return all(isinstance(v, list) for v in values)


def _values_are_different_types(first_value, second_value):
    """Return true if two values are not the same type.

    Helper for merge_dict.

    Args:
        first_value: the value to compare with second_value.
        second_value: the value to compare with first_value.

    Returns:
        bool: True if the two values are not the same type.
    """
    return not (
        isinstance(first_value, type(second_value)) and
        isinstance(second_value, type(first_value))
    )


def _merge_input_with_existing(input_key, input_value, dict_to_update):
    """Merge the given input with an existing dictionary.

    Helper for merge_dict.

    Args:
        input_key: The key under which to insert the new data.
        input_value: The new value to insert.
        dict_to_update: The dictionary in which to insert the new data.

    Returns:
        None. Modifies dict_to_update in place.

    Raises:
        TypeError: if two values contain conflicting types that can't
            be merged (e.g. merging a string with a list).
    """
    # If adding a new key not in the existing dict, just add it.
    if input_key not in dict_to_update:
        dict_to_update[input_key] = input_value
    else:
        if _values_are_dicts(dict_to_update[input_key], input_value):
            # Merging two dicts, use merge_dict() recursively.
            dict_to_update[input_key] = merge_dict(input_value, dict_to_update[input_key])
        elif _values_are_lists(dict_to_update[input_key], input_value):
            # Merging two lists, use extend().
            dict_to_update[input_key].extend(input_value)
        else:
            if _values_are_different_types(input_value, dict_to_update[input_key]):
                raise TypeError(
                    f'Cannot merge {input_value} (type {type(input_value)}) '
                    f'with {dict_to_update[input_key]} (type {type(dict_to_update[input_key])})'
                )
            # Data can't be merged, but should replace old with new.
            dict_to_update[input_key] = input_value


def merge_dict(input_dict, existing_dict):
    """Merge two dictionaries and return the result.

    Args:
        input_dict: The dictionary to merge in.
        existing_dict: The dictionary to which the input_dict data should be
            added.

    Returns:
        dict: The updated dict.

    Raises:
        TypeError: if given arguments are not dict type.
    """
    if not _values_are_dicts(input_dict, existing_dict):
        raise TypeError('Inputs to merge_dict must be dictionary type.')

    # Avoid updating existing_dict in place
    dict_to_return = deepcopy(existing_dict)

    if _dict_contains_no_subdicts_or_lists(dict_to_return):
        # Base case: can just use update().
        dict_to_return.update(input_dict)
        return dict_to_return

    else:
        # Recursive case: iterate over keys/values to add and update existing_dict.
        for input_key, input_value in input_dict.items():
            _merge_input_with_existing(input_key, input_value, dict_to_return)

        return dict_to_return
