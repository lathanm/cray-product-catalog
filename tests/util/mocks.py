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
# Mock data for the cray_product_catalog.util module.

# Trivial mock data: two dictionaries that can be merged just by
# using the update() method, and the expected result.
TRIVIAL_INPUT_DICT = {'apple': 'red'}

TRIVIAL_EXISTING_DICT = {'pear': 'yellow'}

TRIVIAL_EXPECTED_MERGE = {
    'apple': 'red',
    'pear': 'yellow'
}

# Product catalog mock data: two dictionaries that look like
# what appears in the product catalog, and the expected results.
PRODUCT_CATALOG_INPUT_DATA = {
    'component_versions': {
        'docker': [
            {
                'name': 'cray-pear',
                'version': '2.0.0'
            }
        ]
    }
}

PRODUCT_CATALOG_EXISTING_DATA = {
    'component_versions': {
        'docker': [
            {
                'name': 'cray-apple',
                'version': '1.0.0'
            }
        ]
    }
}

PRODUCT_CATALOG_EXPECTED_MERGE = {
    'component_versions': {
        'docker': [
            {
                'name': 'cray-apple',
                'version': '1.0.0'
            },
            {
                'name': 'cray-pear',
                'version': '2.0.0'
            }
        ]
    }
}

# "Complicated" mock data: two dictionaries that contain extra levels
# of nesting and other data types to test a more complicated case for
# merge_dict.
COMPLICATED_INPUT_DICT = {
    'recipe': ['flour'],
    'steps': {
        'prep': ['dice'],
        'simmer': ['soup'],
        'bake': ['time'],
        'cleanup': {
            'sweep': {'broom': 'floor'},
            'dishes': {'towel': 'plates'}
        }
    },
    'states': ['georgia'],
    'age': 40,
}

COMPLICATED_EXISTING_DICT = {
    'recipe': ['cinnamon', 'apples', 'sugar'],
    'steps': {
        'prep': ['chop', 'slice'],
        'bake': ['preheat'],
        'cleanup': {
            'dishes': {'soap': 'plates', 'water': 'sink'}
        }
    },
    'states': ['minnesota', 'texas'],
    'age': 30,
}


COMPLICATED_EXPECTED_MERGE = {
    'recipe': ['cinnamon', 'apples', 'sugar', 'flour'],
    'steps': {
        'prep': ['chop', 'slice', 'dice'],
        'simmer': ['soup'],
        'bake': ['preheat', 'time'],
        'cleanup': {
            'sweep': {'broom': 'floor'},
            'dishes': {'soap': 'plates', 'water': 'sink', 'towel': 'plates'},
        },
    },
    'states': ['minnesota', 'texas', 'georgia'],
    'age': 40,
}
