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
# Unit tests for the cray_product_catalog.util.merge_dict module

from copy import deepcopy
import unittest

from cray_product_catalog.util.merge_dict import merge_dict

from tests.util.mocks import (
    COMPLICATED_INPUT_DICT,
    COMPLICATED_EXISTING_DICT,
    COMPLICATED_EXPECTED_MERGE,
    PRODUCT_CATALOG_INPUT_DATA,
    PRODUCT_CATALOG_EXISTING_DATA,
    PRODUCT_CATALOG_EXPECTED_MERGE,
    TRIVIAL_INPUT_DICT,
    TRIVIAL_EXISTING_DICT,
    TRIVIAL_EXPECTED_MERGE,
)


class TestMergeDict(unittest.TestCase):
    """Tests for merge_dict."""

    def test_trivial_merge_dict(self):
        """Test a trivial case of merge_dict."""
        expected = TRIVIAL_EXPECTED_MERGE
        actual = merge_dict(TRIVIAL_INPUT_DICT, TRIVIAL_EXISTING_DICT)
        self.assertEqual(expected, actual)

    def test_simple_merge_dict(self):
        """Test a simple case of merge_dict."""
        expected = PRODUCT_CATALOG_EXPECTED_MERGE
        actual = merge_dict(PRODUCT_CATALOG_INPUT_DATA, PRODUCT_CATALOG_EXISTING_DATA)
        self.assertEqual(expected, actual)

    def test_complicated_merge_dict(self):
        """Test a more complicated example of merge_dict."""
        expected = COMPLICATED_EXPECTED_MERGE
        actual = merge_dict(COMPLICATED_INPUT_DICT, COMPLICATED_EXISTING_DICT)
        self.assertEqual(expected, actual)

    def test_merge_dict_unexpected_types(self):
        """Test giving a non-dict to merge_dict."""
        with self.assertRaises(TypeError):
            merge_dict('bad_input_data', {})

    def test_merge_dict_incompatible_types(self):
        """Test merge_dict with two types that can't be merged."""
        modified_input_data = deepcopy(COMPLICATED_INPUT_DICT)
        modified_input_data['age'] = 'undefined'
        with self.assertRaises(TypeError):
            merge_dict(modified_input_data, COMPLICATED_EXISTING_DICT)

    def test_inputs_unchanged(self):
        """Test that merge_dict doesn't change the input values."""
        input_dict = deepcopy(COMPLICATED_INPUT_DICT)
        existing = deepcopy(COMPLICATED_EXISTING_DICT)
        merge_dict(input_dict, existing)
        self.assertEqual(input_dict, COMPLICATED_INPUT_DICT)
        self.assertEqual(existing, COMPLICATED_EXISTING_DICT)
