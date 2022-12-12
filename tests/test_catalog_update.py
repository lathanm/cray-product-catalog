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
# Unit tests for catalog_update

import copy
import unittest
from unittest.mock import patch, Mock

import yaml

from tests.mocks import MOCK_PRODUCT_CATALOG_DATA

from cray_product_catalog.catalog_update import (
    load_global_variables_from_environment,
    update_config_map
)


class TestCatalogUpdate(unittest.TestCase):
    def setUp(self):
        """Set up patches."""
        self.mock_api_client = patch('cray_product_catalog.catalog_update.ApiClient').start()
        self.mock_core_v1_api = patch('cray_product_catalog.catalog_update.CoreV1Api').start()
        self.mock_core_v1_api_object = self.mock_core_v1_api.return_value
        self.mock_product_catalog_data = copy.deepcopy(MOCK_PRODUCT_CATALOG_DATA)
        self.original_product_catalog_data = copy.deepcopy(self.mock_product_catalog_data)
        self.mock_product_catalog_resource_version = '123'
        patch('cray_product_catalog.catalog_update.V1ConfigMap', Mock).start()
        self.mock_config_map_response = self.mock_core_v1_api_object.read_namespaced_config_map.return_value
        self.mock_config_map_response.data = self.mock_product_catalog_data
        self.mock_config_map_response.metadata.resource_version = self.mock_product_catalog_resource_version
        self.mock_patch_config_map = patch(
            'cray_product_catalog.catalog_update.patch_config_map', side_effect=self.fake_patch_config_map
        ).start()

        fake_env = {
            'PRODUCT': 'example-product',
            'PRODUCT_VERSION': '1.0.0'
        }
        self.set_up_mock_environment(fake_env)
        patch('cray_product_catalog.catalog_update.time.sleep').start()

    @staticmethod
    def set_up_mock_environment(fake_env):
        """Set up mocks for global variables."""
        with patch('cray_product_catalog.catalog_update.os.environ', fake_env):
            load_global_variables_from_environment()

    def fake_patch_config_map(self, api_instance, name, namespace, resource_version, config_map_data):
        """Fake version of patch_config_map."""
        # NOTE: "patch" is slightly inaccurate here in that this function completely
        # overwrites the target data, but it is close enough for the purposes of this testing.
        self.mock_core_v1_api_object.read_namespaced_config_map.return_value.data = config_map_data

    def tearDown(self):
        """Stop patches."""
        patch.stopall()

    def test_update_config_map_empty(self):
        """Test calling update_config_map and inserting empty data for a new product."""
        update_config_map(data={}, namespace='mock_namespace', name='mock_config_map')
        expected_product_catalog_data = self.original_product_catalog_data
        expected_product_catalog_data['example-product'] = yaml.safe_dump({
            '1.0.0': {}
        })
        self.mock_patch_config_map.assert_called_once_with(
            self.mock_core_v1_api_object, 'mock_config_map', 'mock_namespace',
            self.mock_product_catalog_resource_version, self.original_product_catalog_data
        )

    def test_update_config_map_with_data(self):
        """Test calling update_config_map and inserting some non-empty data for a new product."""
        update_config_map(
            data={'vcs': {'clone_url': 'https://example.com'}}, namespace='mock_namespace', name='mock_config_map'
        )
        expected_product_catalog_data = self.original_product_catalog_data
        expected_product_catalog_data['example-product'] = yaml.safe_dump({
            '1.0.0': {'vcs': {'clone_url': 'https://example.com'}}
        })
        self.mock_patch_config_map.assert_called_once_with(
            self.mock_core_v1_api_object, 'mock_config_map', 'mock_namespace',
            self.mock_product_catalog_resource_version, self.original_product_catalog_data
        )

    def test_update_config_map_with_active(self):
        """Test calling update_config_map and setting a product version as 'active'."""
        self.set_up_mock_environment({
            'PRODUCT': 'sat',
            'PRODUCT_VERSION': '2.0.0',
            'SET_ACTIVE_VERSION': "true"
        })
        update_config_map(data={}, namespace='mock_namespace', name='mock_config_map')
        expected_product_catalog_data = self.original_product_catalog_data
        sat_data = yaml.safe_load(expected_product_catalog_data['sat'])

        # Create expected 'sat' data with the desired version set active.
        new_sat_data = {}
        for version, version_data in sat_data.items():
            if version == '2.0.0':
                version_data['active'] = True
            else:
                version_data['active'] = False
            new_sat_data[version] = version_data
        expected_product_catalog_data['sat'] = yaml.safe_dump(new_sat_data)

        self.mock_patch_config_map.assert_called_once_with(
            self.mock_core_v1_api_object, 'mock_config_map', 'mock_namespace',
            self.mock_product_catalog_resource_version, expected_product_catalog_data
        )

    def test_update_config_map_switch_active(self):
        """Test setting a product version as 'active' when a different one was active before."""

        # Set up the config map with '1.0.0' as 'active'
        original_mock_sat_data = yaml.safe_load(self.mock_product_catalog_data['sat'])
        new_mock_sat_data = {}
        for version, version_data in original_mock_sat_data.items():
            if version == '1.0.0':
                version_data['active'] = True
            else:
                version_data['active'] = False
            new_mock_sat_data[version] = version_data
        self.mock_product_catalog_data['sat'] = yaml.safe_dump(new_mock_sat_data)

        self.set_up_mock_environment({
            'PRODUCT': 'sat',
            'PRODUCT_VERSION': '2.0.0',
            'SET_ACTIVE_VERSION': "true"
        })

        update_config_map(data={}, namespace='mock_namespace', name='mock_config_map')

        expected_product_catalog_data = self.original_product_catalog_data
        sat_data = yaml.safe_load(expected_product_catalog_data['sat'])

        # Create expected 'sat' data with the desired version set active.
        new_sat_data = {}
        for version, version_data in sat_data.items():
            if version == '2.0.0':
                version_data['active'] = True
            else:
                version_data['active'] = False
            new_sat_data[version] = version_data
        expected_product_catalog_data['sat'] = yaml.safe_dump(new_sat_data)

        self.mock_patch_config_map.assert_called_once_with(
            self.mock_core_v1_api_object, 'mock_config_map', 'mock_namespace',
            self.mock_product_catalog_resource_version, expected_product_catalog_data
        )

    def test_update_config_map_clear_active(self):
        """Test clearing the 'active' field when one was active before."""

        # Set up the config map with '1.0.0' as 'active'
        original_mock_sat_data = yaml.safe_load(self.mock_product_catalog_data['sat'])
        new_mock_sat_data = {}
        for version, version_data in original_mock_sat_data.items():
            if version == '1.0.0':
                version_data['active'] = True
            else:
                version_data['active'] = False
            new_mock_sat_data[version] = version_data
        self.mock_product_catalog_data['sat'] = yaml.safe_dump(new_mock_sat_data)

        self.set_up_mock_environment({
            'PRODUCT': 'sat',
            'PRODUCT_VERSION': '2.0.0',
            'REMOVE_ACTIVE_FIELD': 'true'
        })

        update_config_map(data={}, namespace='mock_namespace', name='mock_config_map')

        self.mock_patch_config_map.assert_called_once_with(
            self.mock_core_v1_api_object, 'mock_config_map', 'mock_namespace',
            self.mock_product_catalog_resource_version, self.original_product_catalog_data
        )
