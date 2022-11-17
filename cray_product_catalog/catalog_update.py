#!/usr/bin/env python3
#
# MIT License
#
# (C) Copyright 2020-2022 Hewlett Packard Enterprise Development LP
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
# This script takes a PRODUCT and PRODUCT_VERSION and applies the content of
# a YAML file to a Kubernetes ConfigMap as follows:
#
# {PRODUCT}:
#   {PRODUCT_VERSION}:
#     {content of yaml file}
#
# Since updates to a configmap are not atomic, this script will continue to
# attempt to update the config map until it has been patched successfully.
import logging
import os
import random
import sys
import time
import urllib3
from urllib3.util.retry import Retry

from jsonschema.exceptions import ValidationError
from kubernetes import client
from kubernetes.client.api_client import ApiClient
from kubernetes.client.models.v1_config_map import V1ConfigMap
from kubernetes.client.models.v1_object_meta import V1ObjectMeta
from kubernetes.client.rest import ApiException
import yaml

from cray_product_catalog.schema.validate import validate
from cray_product_catalog.util.k8s import load_k8s
from cray_product_catalog.util.merge_dict import merge_dict

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Logging
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
LOGGER.addHandler(handler)

# Parameters to identify config map and content in it to update
PRODUCT = os.environ.get("PRODUCT").strip()  # required
PRODUCT_VERSION = os.environ.get("PRODUCT_VERSION").strip()  # required
CONFIG_MAP = os.environ.get("CONFIG_MAP", "cray-product-catalog").strip()
CONFIG_MAP_NAMESPACE = os.environ.get("CONFIG_MAP_NAMESPACE", "services").strip()
# One of (YAML_CONTENT_FILE, YAML_CONTENT_STRING) required. For backwards compatibility, YAML_CONTENT
# may also be given in place of YAML_CONTENT_FILE.
YAML_CONTENT_FILE = (os.environ.get("YAML_CONTENT_FILE") or os.environ.get("YAML_CONTENT", "")).strip()
YAML_CONTENT_STRING = os.environ.get("YAML_CONTENT_STRING", "").strip()   # see above
SET_ACTIVE_VERSION = bool(os.environ.get("SET_ACTIVE_VERSION"))
VALIDATE_SCHEMA = bool(os.environ.get("VALIDATE_SCHEMA"))

ERR_NOT_FOUND = 404
ERR_CONFLICT = 409


def validate_schema(data):
    """ Validate data against the schema. """
    LOGGER.info(
        "Validating data against schema because VALIDATE_SCHEMA was set."
    )
    try:
        validate(data)
    except ValidationError as err:
        LOGGER.error("Data failed schema validation: %s", err)
        raise SystemExit(1)


def read_yaml_content(yaml_file):
    """ Read and return the raw content contained in the `yaml_file`. """
    LOGGER.info("Retrieving content from %s", yaml_file)
    with open(yaml_file) as yfile:
        return yaml.safe_load(yfile)


def read_yaml_content_string(yaml_string):
    """ Read and return the raw content contained in the `yaml_string` string. """
    LOGGER.info("Retrieving raw content specified as a string")
    return yaml.safe_load(yaml_string)


def set_active_version(product_data):
    """ Modify product_data in place to set the 'active' key for PRODUCT_VERSION.

    This also sets the 'active' key for other versions in product_data to False."""
    # Set the current version to 'active'
    for version in product_data:
        product_data[version]['active'] = version == PRODUCT_VERSION


def current_version_is_active(product_data):
    """ Return True if PRODUCT_VERSION is active and no other version of the product is active."""
    current_version = product_data[PRODUCT_VERSION]
    other_versions = [version for version in product_data if version != PRODUCT_VERSION]

    return current_version.get('active') and not any(
               [product_data[version].get('active') for version in other_versions]
           )


def update_config_map(data, name, namespace):
    """
    Get the config map `data` to be added.

    1. Wait for the config map to be present in the namespace
    2. Read the config map
    3. Patch the config_map
    4. Read back the config_map
    5. Repeat steps 2-4 if config_map does not include the changes requested,
       or if step 3 failed due to a conflict.
    """
    k8sclient = ApiClient()
    retries = 100
    retry = Retry(
        total=retries, read=retries, connect=retries, backoff_factor=0.3,
        status_forcelist=(500, 502, 503, 504)
    )
    k8sclient.rest_client.pool_manager.connection_pool_kw['retries'] = retry
    api_instance = client.CoreV1Api(k8sclient)
    attempt = 0

    while True:

        # Wait a while to check the config map in case multiple products are
        # attempting to update the same config map, or the config map doesn't
        # exist yet
        attempt += 1
        sleepy_time = random.randint(1, 3)
        LOGGER.info("Resting %ss before reading ConfigMap", sleepy_time)
        time.sleep(sleepy_time)

        # Read in the config map
        try:
            response = api_instance.read_namespaced_config_map(name, namespace)
        except ApiException as e:
            LOGGER.exception("Error calling read_namespaced_config_map")

            # Config map doesn't exist yet
            if e.status == ERR_NOT_FOUND:
                LOGGER.warning("ConfigMap %s/%s doesn't exist, attempting again.", namespace, name)
                continue
            else:
                raise  # unrecoverable

        # Determine if ConfigMap needs to be updated
        config_map_data = response.data or {}  # if no config map data exists
        if PRODUCT not in config_map_data:
            LOGGER.info("Product=%s does not exist; will update", PRODUCT)
            config_map_data[PRODUCT] = product_data = {PRODUCT_VERSION: {}}
        # Product exists in ConfigMap
        else:
            product_data = yaml.safe_load(config_map_data[PRODUCT])
            if PRODUCT_VERSION not in product_data:
                LOGGER.info(
                    "Version=%s does not exist; will update", PRODUCT_VERSION
                )
                product_data[PRODUCT_VERSION] = {}
            # Key with same version exists in ConfigMap
            else:
                if (merge_dict(data, product_data[PRODUCT_VERSION]) == product_data[PRODUCT_VERSION]
                        and (current_version_is_active(product_data) or not SET_ACTIVE_VERSION)):
                    LOGGER.info("ConfigMap data updates exist; Exiting.")
                    break

        # Patch the config map if needed
        product_data[PRODUCT_VERSION] = merge_dict(data, product_data[PRODUCT_VERSION])
        if SET_ACTIVE_VERSION:
            set_active_version(product_data)
        config_map_data[PRODUCT] = yaml.safe_dump(
            product_data, default_flow_style=False
        )
        LOGGER.info("ConfigMap update attempt=%s", attempt)
        try:
            new_config_map = V1ConfigMap(data=config_map_data)
            new_config_map.metadata = V1ObjectMeta(
                name=name, resource_version=response.metadata.resource_version
            )
            api_instance.patch_namespaced_config_map(
                name, namespace, body=new_config_map
            )
        except ApiException as e:
            if e.status == ERR_CONFLICT:
                # A conflict is raised if the resourceVersion field was unexpectedly
                # incremented, e.g. if another process updated the config map. This
                # provides concurrency protection.
                LOGGER.warning("Conflict updating config map")
            else:
                LOGGER.exception("Error calling replace_namespaced_config_map")


def main():
    LOGGER.info(
        "Updating config_map=%s in namespace=%s for product/version=%s/%s",
        CONFIG_MAP, CONFIG_MAP_NAMESPACE, PRODUCT, PRODUCT_VERSION
    )

    if SET_ACTIVE_VERSION:
        LOGGER.info(
            "Setting %s:%s to active because SET_ACTIVE_VERSION was set.",
            PRODUCT, PRODUCT_VERSION
        )

    load_k8s()
    if YAML_CONTENT_FILE:
        data = read_yaml_content(YAML_CONTENT_FILE)
    elif YAML_CONTENT_STRING:
        data = read_yaml_content_string(YAML_CONTENT_STRING)
    else:
        LOGGER.error(
            "One of the environment variables YAML_CONTENT_FILE or "
            "YAML_CONTENT_STRING must be specified."
        )
        raise SystemExit(1)
    if VALIDATE_SCHEMA:
        validate_schema(data)

    update_config_map(data, CONFIG_MAP, CONFIG_MAP_NAMESPACE)


if __name__ == "__main__":
    main()
