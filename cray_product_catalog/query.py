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
# Defines classes for querying for information about the installed products.
import logging
from pkg_resources import parse_version

from jsonschema.exceptions import ValidationError
from kubernetes.client import CoreV1Api
from kubernetes.client.rest import ApiException
from kubernetes.config import ConfigException
from urllib3.exceptions import MaxRetryError
from yaml import safe_load, YAMLError

from cray_product_catalog.constants import (
    COMPONENT_DOCKER_KEY,
    COMPONENT_REPOS_KEY,
    COMPONENT_VERSIONS_PRODUCT_MAP_KEY,
    PRODUCT_CATALOG_CONFIG_MAP_NAME,
    PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
)
from cray_product_catalog.schema.validate import validate
from cray_product_catalog.util import load_k8s

LOGGER = logging.getLogger(__name__)


class ProductCatalogError(Exception):
    """An error occurred reading or manipulating product installs."""
    pass


class ProductCatalog:
    """A collection of installed product versions.

    Attributes:
        name (str): The product catalog Kubernetes config map name.
        namespace (str): The product catalog Kubernetes config map namespace.
        products ([InstalledProductVersion]): A list of installed product
            versions.
    """
    @staticmethod
    def _get_k8s_api():
        """Load a Kubernetes CoreV1Api and return it.

        Returns:
            CoreV1Api: The Kubernetes API.

        Raises:
            ProductCatalogError: if there was an error loading the
                Kubernetes configuration.
        """
        try:
            load_k8s()
            return CoreV1Api()
        except ConfigException as err:
            raise ProductCatalogError(f'Unable to load kubernetes configuration: {err}.')

    def __init__(self, name=PRODUCT_CATALOG_CONFIG_MAP_NAME, namespace=PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE):
        """Create the ProductCatalog object.

        Args:
            name (str): The name of the product catalog Kubernetes config map.
            namespace (str): The namespace of the product catalog Kubernetes
                config map.

        Raises:
            ProductCatalogError: if reading the config map failed.
        """
        self.name = name
        self.namespace = namespace
        self.k8s_client = self._get_k8s_api()
        try:
            config_map = self.k8s_client.read_namespaced_config_map(name, namespace)
        except MaxRetryError as err:
            raise ProductCatalogError(
                f'Unable to connect to Kubernetes to read {namespace}/{name} ConfigMap: {err}'
            )
        except ApiException as err:
            # The full string representation of ApiException is very long, so just log err.reason.
            raise ProductCatalogError(
                f'Error reading {namespace}/{name} ConfigMap: {err.reason}'
            )

        if config_map.data is None:
            raise ProductCatalogError(
                f'No data found in {namespace}/{name} ConfigMap.'
            )

        try:
            self.products = [
                InstalledProductVersion(product_name, product_version, product_version_data)
                for product_name, product_versions in config_map.data.items()
                for product_version, product_version_data in safe_load(product_versions).items()
            ]
        except YAMLError as err:
            raise ProductCatalogError(
                f'Failed to load ConfigMap data: {err}'
            )

        invalid_products = [
            str(p) for p in self.products if not p.is_valid
        ]
        if invalid_products:
            LOGGER.debug(
                f'The following products have product catalog data that '
                f'is not valid against the expected schema: {", ".join(invalid_products)}'
            )

        self.products = [
            p for p in self.products if p.is_valid
        ]

    def get_product(self, name, version=None):
        """Get the InstalledProductVersion matching the given name/version.

        Args:
            name (str): The product name.
            version (str, optional): The product version. If omitted or None,
                get the latest installed version.

        Returns:
            An InstalledProductVersion with the given name and version.

        Raises:
            ProductCatalogError: If there is more than one matching
                InstalledProductVersion, or if there are none.
        """
        if not version:
            matching_name_products = [product for product in self.products if product.name == name]
            if not matching_name_products:
                raise ProductCatalogError(f'No installed products with name {name}.')
            latest = sorted(matching_name_products,
                            key=lambda p: parse_version(p.version))[-1]
            LOGGER.debug(f'Using latest version ({latest.version}) of product {name}')
            return latest

        matching_products = [
            product for product in self.products
            if product.name == name and product.version == version
        ]
        if not matching_products:
            raise ProductCatalogError(
                f'No installed products with name {name} and version {version}.'
            )
        elif len(matching_products) > 1:
            raise ProductCatalogError(
                f'Multiple installed products with name {name} and version {version}.'
            )

        return matching_products[0]


class InstalledProductVersion:
    """A representation of a version of a product that is currently installed.

    Attributes:
        name (str): The product name.
        version (str): The product version.
        data (dict): A dictionary representing the data within a given product and
            version in the product catalog, which is expected to contain a
            'component_versions' key that will point to the respective
            versions of product components, e.g. Docker images.
    """
    def __init__(self, name, version, data):
        self.name = name
        self.version = version
        self.data = data

    def __str__(self):
        return f'{self.name}-{self.version}'

    @property
    def is_valid(self):
        """bool: True if this product's version data fits the schema."""
        try:
            validate(self.data)
            return True
        except ValidationError:
            return False

    @property
    def component_data(self):
        """dict: a mapping from types of components to lists of components"""
        return self.data.get(COMPONENT_VERSIONS_PRODUCT_MAP_KEY, {})

    @property
    def docker_images(self):
        """Get Docker images associated with this InstalledProductVersion.

        Returns:
            A list of tuples of (image_name, image_version)
        """
        return [(component['name'], component['version'])
                for component in self.component_data.get(COMPONENT_DOCKER_KEY) or []]

    @property
    def repositories(self):
        """list of dict: the repositories for this product version."""
        return self.component_data.get(COMPONENT_REPOS_KEY, [])

    @property
    def group_repositories(self):
        """list of dict: the group-type repositories for this product version."""
        return [repo for repo in self.repositories if repo.get('type') == 'group']

    @property
    def hosted_repositories(self):
        """list of dict: the hosted-type repositories for this product version."""
        return [repo for repo in self.repositories if repo.get('type') == 'hosted']

    @property
    def hosted_and_member_repo_names(self):
        """set of str: all hosted repository names for this product version

        This includes all explicitly listed hosted repos plus any hosted repos
        which are listed only as members of any of the group repos
        """
        # Get all hosted repositories, plus any repos that might be under a group repo's "members" list.
        repository_names = set(repo.get('name') for repo in self.hosted_repositories)
        for group_repo in self.group_repositories:
            repository_names |= set(group_repo.get('members'))

        return repository_names

    @property
    def configuration(self):
        """dict: information about the config management repo for the product"""
        return self.data.get('configuration', {})

    @property
    def clone_url(self):
        """str or None: the clone url of the config repo for the product, if available."""
        return self.configuration.get('clone_url')

    @property
    def commit(self):
        """str or None: the commit hash of the config repo for the product, if available."""
        return self.configuration.get('commit')

    @property
    def import_branch(self):
        """str or None: the branch name of the config repo for the product, if available."""
        return self.configuration.get('import_branch')

    def _get_ims_resources(self, ims_resource_type):
        """Get IMS resources (images or recipes) provided by the product

        Args:
            ims_resource_type (str): Either 'images' or 'recipes'

        Returns:
            list of dict: the IMS resources of the given type provided by the
                product. Each has a 'name' and 'id' key.

        Raises:
            ValueError: if given an unrecognized `ims_resource_type`
        """
        if ims_resource_type not in ('recipes', 'images'):
            raise ValueError(f'Unrecognized IMS resource type "{ims_resource_type}"')

        ims_resource_data = self.data.get(ims_resource_type) or {}

        return [
            {'name': resource_name, 'id': resource_data.get('id')}
            for resource_name, resource_data in ims_resource_data.items()
        ]

    @property
    def images(self):
        """list of dict: the list of images provided by this product"""
        return self._get_ims_resources('images')

    @property
    def recipes(self):
        return self._get_ims_resources('recipes')

    @property
    def supports_active(self):
        """bool: whether this product version indicates whether or not it is the active version"""
        return 'active' in self.data

    @property
    def active(self):
        """bool: whether or not this product is active"""
        return self.data.get('active', False)
