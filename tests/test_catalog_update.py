# MIT License
#
# (C) Copyright 2022-2023 Hewlett Packard Enterprise Development LP
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

from copy import deepcopy
import unittest
from unittest.mock import patch, Mock

import yaml

from tests.mocks import MOCK_PRODUCT_CATALOG_DATA

from cray_product_catalog.catalog_update import (
    load_global_variables_from_environment,
    update_config_map
)


class TestUpdateConfigMap(unittest.TestCase):
    """Test cases for the update_config_map function."""

    def setUp(self):
        """Set up patches."""
        self.mock_api_client = patch('cray_product_catalog.catalog_update.ApiClient').start()
        self.mock_core_v1_api = patch('cray_product_catalog.catalog_update.CoreV1Api').start()
        self.mock_core_v1_api_object = self.mock_core_v1_api.return_value
        self.mock_product_catalog_data = deepcopy(MOCK_PRODUCT_CATALOG_DATA)
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
        self.mock_core_v1_api_object.read_namespaced_config_map.return_value.data = deepcopy(config_map_data)

    def fake_get_config_map(self):
        """Return the data returned by reading the config map."""
        return self.mock_core_v1_api_object.read_namespaced_config_map.return_value.data

    @staticmethod
    def _set_product_version_active(product_version, active_version):
        """Modify a dictionary of product versions to set one of them as 'active'."""
        for version, version_data in product_version.items():
            if version == active_version:
                version_data['active'] = True
            else:
                version_data['active'] = False

    def tearDown(self):
        """Stop patches."""
        patch.stopall()

    def test_update_config_map_empty(self):
        """Test calling update_config_map and inserting empty data for a new product."""
        update_config_map(data={}, namespace='mock_namespace', name='mock_config_map')
        expected_product_catalog_patch = self.mock_product_catalog_data
        expected_product_catalog_patch['example-product'] = yaml.safe_dump({
            '1.0.0': {}
        })
        self.mock_patch_config_map.assert_called_once_with(
            self.mock_core_v1_api_object, 'mock_config_map', 'mock_namespace',
            self.mock_product_catalog_resource_version, expected_product_catalog_patch
        )

    def test_update_config_map_with_data(self):
        """Test calling update_config_map and inserting some non-empty data for a new product."""
        update_config_map(
            data={'vcs': {'clone_url': 'https://example.com'}}, namespace='mock_namespace', name='mock_config_map'
        )

        expected_product_catalog_patch = self.mock_product_catalog_data
        expected_product_catalog_patch['example-product'] = yaml.safe_dump({
            '1.0.0': {'vcs': {'clone_url': 'https://example.com'}}
        })
        self.mock_patch_config_map.assert_called_once_with(
            self.mock_core_v1_api_object, 'mock_config_map', 'mock_namespace',
            self.mock_product_catalog_resource_version, expected_product_catalog_patch
        )

    def test_update_config_map_with_active(self):
        """Test calling update_config_map and setting a product version as 'active'."""
        self.set_up_mock_environment({
            'PRODUCT': 'sat',
            'PRODUCT_VERSION': '2.0.0',
            'SET_ACTIVE_VERSION': "true"
        })
        update_config_map(data={}, namespace='mock_namespace', name='mock_config_map')

        expected_product_catalog_patch = self.mock_product_catalog_data
        sat_patch_data = yaml.safe_load(expected_product_catalog_patch['sat'])
        self._set_product_version_active(sat_patch_data, active_version='2.0.0')
        expected_product_catalog_patch['sat'] = yaml.safe_dump(sat_patch_data)

        self.mock_patch_config_map.assert_called_once_with(
            self.mock_core_v1_api_object, 'mock_config_map', 'mock_namespace',
            self.mock_product_catalog_resource_version, expected_product_catalog_patch
        )

    def test_update_config_map_switch_active(self):
        """Test setting a product version as 'active' when a different one was active before."""

        # Set up the config map with '1.0.0' as 'active'
        original_mock_sat_data = yaml.safe_load(self.mock_product_catalog_data['sat'])
        self._set_product_version_active(original_mock_sat_data, '1.0.0')
        self.mock_product_catalog_data['sat'] = yaml.safe_dump(original_mock_sat_data)

        self.set_up_mock_environment({
            'PRODUCT': 'sat',
            'PRODUCT_VERSION': '2.0.0',
            'SET_ACTIVE_VERSION': "true"
        })

        update_config_map(data={}, namespace='mock_namespace', name='mock_config_map')

        expected_product_catalog_patch = self.mock_product_catalog_data
        sat_data = yaml.safe_load(expected_product_catalog_patch['sat'])
        self._set_product_version_active(sat_data, active_version='2.0.0')
        expected_product_catalog_patch['sat'] = yaml.safe_dump(sat_data)

        self.mock_patch_config_map.assert_called_once_with(
            self.mock_core_v1_api_object, 'mock_config_map', 'mock_namespace',
            self.mock_product_catalog_resource_version, expected_product_catalog_patch
        )

    def test_update_config_map_clear_active(self):
        """Test clearing the 'active' field when one was active before."""

        # Set up the config map with '2.0.0' as 'active'
        original_mock_sat_data = yaml.safe_load(self.mock_product_catalog_data['sat'])
        self._set_product_version_active(original_mock_sat_data, active_version='2.0.0')
        self.mock_product_catalog_data['sat'] = yaml.safe_dump(original_mock_sat_data)

        self.set_up_mock_environment({
            'PRODUCT': 'sat',
            'PRODUCT_VERSION': '2.0.0',
            'REMOVE_ACTIVE_FIELD': 'true'
        })

        update_config_map(data={}, namespace='mock_namespace', name='mock_config_map')

    @unittest.skip('This test only passes with the hotfix from CASM-3589')
    def test_insert_repo_component_versions_already_present(self):
        """Test inserting 'repositories' data into the component_versions when it is already present."""
        data_to_insert = {
            'component_versions': {
                'repositories': [
                    {'name': 'sat-sle-15sp2', 'type': 'group', 'members': ['sat-2.0.0-sle-15sp2']},
                    {'name': 'sat-2.0.0-sle-15sp2', 'type': 'hosted'}
                ]
            }
        }
        self.set_up_mock_environment({
            'PRODUCT': 'sat',
            'PRODUCT_VERSION': '2.0.0'
        })
        update_config_map(data=data_to_insert, namespace='mock_namespace', name='mock_config_map')
