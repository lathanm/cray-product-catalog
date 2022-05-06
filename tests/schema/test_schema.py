#
# MIT License
#
# (C) Copyright 2021-2022 Hewlett Packard Enterprise Development LP
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
# Tests for schema validation

import copy
import unittest

from jsonschema.exceptions import ValidationError
import yaml

from cray_product_catalog.schema.validate import validate

SAT_OLD_FORMAT = yaml.safe_load("""
    component_versions:
      sat: 3.7.1
      sat-podman: 1.4.7-20210727154931_9200ae9
    configuration:
      clone_url: https://vcs.local/vcs/cray/sat-config-management.git
      commit: e69dd25299df0645d5bbfa5e1efc7cb8b6f2395a
      import_branch: cray/sat/2.1.13
      import_date: "2021-07-27 22:26:08.489078"
      ssh_url: git@vcs.local:cray/sat-config-management.git
""")


SAT_NEW_FORMAT = yaml.safe_load("""
    active: false
    component_versions:
      docker:
        - name: cray/cray-sat
          version: 3.9.0
        - name: cray/sat-install-utility
          version: 1.0.6
      rpm:
        - name: cray-sat-podman
          version: 1.6.0
      repositories:
        - name: sat-sle-15sp2
          type: group
          members:
          - sat-2.2.0-sle-15sp2
        - name: sat-another-repo-sle-15sp2
          type: hosted
    configuration:
      clone_url: https://vcs.local/vcs/cray/sat-config-management.git
      commit: cbd90ecfcc9566ab2de6d7cdd8d43cacc0dfb92a
      import_branch: cray/sat/2.2.0
      import_date: "2021-08-27 22:26:08.489078"
      ssh_url: git@vcs.local:cray/sat-config-management.git
""")


IMAGES_AND_RECIPES = yaml.safe_load("""
    configuration:
      clone_url: https://vcs.local/vcs/cray/cos-config-management.git
      commit: b95c3793e2c0d27e59181f1032bbb8530304e2e2
      import_branch: cray/cos/2.1.61
      import_date: 2021-09-03 23:23:54.277606
      ssh_url: git@vcs.local:cray/cos-config-management.git
    images:
      cray-shasta-compute-sles15sp2.x86_64-1.5.59:
        id: 0812a07f-0a00-4a32-bd4a-d52a9a95b837
    recipes:
      cray-shasta-compute-sles15sp2.x86_64-1.5.59:
        id: de22a4ff-cf27-4b46-8003-14ce2cab99ec
""")


CONFIG_ONLY_FORMAT = yaml.safe_load("""
    configuration:
      clone_url: https://vcs.local/vcs/cray/sat-config-management.git
      commit: cbd90ecfcc9566ab2de6d7cdd8d43cacc0dfb92a
      import_branch: cray/sat/2.2.0
      import_date: "2021-08-27 22:26:08.489078"
      ssh_url: git@vcs.local:cray/sat-config-management.git
""")


class TestSchemaValidation(unittest.TestCase):
    """Tests for schema validation."""

    def test_old_style(self):
        """Test the old format can be validated."""
        validate(SAT_OLD_FORMAT)

    def test_new_style(self):
        """Test the new format can be validated."""
        validate(SAT_NEW_FORMAT)

    def test_config_only(self):
        """Test when only a "configuration" key is present"""
        validate(CONFIG_ONLY_FORMAT)

    def test_with_images_and_recipes(self):
        """Test when images and recipes are present."""
        validate(IMAGES_AND_RECIPES)

    def test_extra_top_level_key(self):
        """Test adding an extra top level key still validates."""
        data_to_validate = copy.deepcopy(SAT_NEW_FORMAT)
        data_to_validate['foo'] = 'bar'
        validate(data_to_validate)

    @unittest.skip('There is no way to assert a UUID format yet.')
    def test_non_uuid(self):
        """Test something other than a UUID where a UUID should be does not validate."""
        data_to_validate = copy.deepcopy(IMAGES_AND_RECIPES)
        data_to_validate.update({
            'recipes': {'my great recipe': {'id': 'recipe.exe'}}
        })
        with self.assertRaises(ValidationError):
            validate(data_to_validate)

    def test_extra_component_key(self):
        """Test adding additional properties to component_versions still validates."""
        data_to_validate = copy.deepcopy(SAT_NEW_FORMAT)
        data_to_validate['component_versions']['apk'] = [{'name': 'foo', 'version': 'bar'}]
        validate(data_to_validate)

    def test_extra_component_version_key(self):
        """Test adding unrecognized component version properties still validates."""
        data_to_validate = copy.deepcopy(SAT_NEW_FORMAT)
        data_to_validate['component_versions']['rpm'][0]['lastUpdated'] = 'yesterday'
        validate(data_to_validate)

    def test_missing_component_version_key(self):
        """Test a component missing a required key does not validate."""
        data_to_validate = copy.deepcopy(SAT_NEW_FORMAT)
        del data_to_validate['component_versions']['rpm'][0]['name']
        with self.assertRaises(ValidationError):
            validate(data_to_validate)

    def test_with_extra_repository_key(self):
        """Test a component with additional property in a repository still validates."""
        data_to_validate = copy.deepcopy(SAT_NEW_FORMAT)
        data_to_validate['component_versions']['repositories'][0]['another_field'] = 'other_stuff'
        validate(data_to_validate)

    def test_invalid_repo_key(self):
        """Test a component with invalid repository type does not validate."""
        data_to_validate = copy.deepcopy(SAT_NEW_FORMAT)
        data_to_validate['component_versions']['repositories'][0]['type'] = 'not_hosted_or_group'
        with self.assertRaises(ValidationError):
            validate(data_to_validate)

    def test_group_repo_with_no_members_key(self):
        """Test a group type repo that does not have a 'members' key does not validate."""
        data_to_validate = copy.deepcopy(SAT_NEW_FORMAT)
        del data_to_validate['component_versions']['repositories'][0]['members']
        with self.assertRaises(ValidationError):
            validate(data_to_validate)


if __name__ == '__main__':
    unittest.main()
