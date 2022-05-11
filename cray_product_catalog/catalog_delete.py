#!/usr/bin/env python3
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
# This script takes a PRODUCT and PRODUCT_VERSION and deletes the content
# in a Kubernetes ConfigMap in one of two ways:
#
# If a 'key' is specified within a PRODUCT/PRODUCT_VERSION:
#
# {PRODUCT}:
#   {PRODUCT_VERSION}:
#     {key}        # <- content to delete
#
# If a 'key' is not specified:
#
# {PRODUCT}:
#   {PRODUCT_VERSION}: # <- delete entire version
#
# Since updates to a configmap are not atomic, this script will continue to
# attempt to modify the config map until it has been patched successfully.
import logging
import os
import random
import sys
import time
import urllib3
from urllib3.util.retry import Retry

from kubernetes import client
from kubernetes.client.api_client import ApiClient
from kubernetes.client.configuration import Configuration
from kubernetes.client.rest import ApiException
import yaml

from cray_product_catalog.util import load_k8s

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Logging
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
LOGGER.addHandler(handler)


def modify_config_map(name, namespace, product, product_version, key=None):
    """Remove a product version from the catalog config map.

    If a key is specified, delete the `key` content from a specific section
    of the catalog config map. If there are no more keys after it has been
    removed, remove the version mapping as well.

    1. Wait for the config map to be present in the namespace
    2. Patch the config_map
    3. Read back the config_map
    4. Repeat steps 2-3 if config_map does not reflect the changes requested
    """
    k8sclient = ApiClient(configuration=Configuration())
    retries = 100
    retry = Retry(
        total=retries, read=retries, connect=retries, backoff_factor=0.3,
        status_forcelist=(500, 502, 503, 504)
    )
    k8sclient.rest_client.pool_manager.connection_pool_kw['retries'] = retry
    api_instance = client.CoreV1Api(k8sclient)
    attempt = 0
    max_attempts = 100

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
            if e.status == 404 and attempt < max_attempts:
                LOGGER.warning("ConfigMap %s/%s doesn't exist, attempting again.", namespace, name)
                continue
            else:
                raise  # unrecoverable

        # Determine if ConfigMap needs to be updated
        config_map_data = response.data or {}  # if no config map data exists
        if product not in config_map_data:
            break  # product doesn't exist, don't need to remove anything

        # Product exists in ConfigMap
        product_data = yaml.safe_load(config_map_data[product])
        if product_version not in product_data:
            LOGGER.info(
                "Version %s not in ConfigMap", product_version
            )
            break  # product version is gone, we are done

        # Product version exists in ConfigMap
        if key:
            # Key exists, remove it
            if key in product_data[product_version]:
                LOGGER.info(
                    "key=%s in version=%s exists; to be removed",
                    key, product_version
                )
                product_data[product_version].pop(key)
            else:
                # No keys left
                if not product_data[product_version].keys():
                    LOGGER.info(
                        "No keys remain in version=%s; removing version",
                        product_version
                    )
                    product_data.pop(product_version)
                else:
                    break  # key is gone, we are done
        else:
            LOGGER.info(
                "Removing product=%s, version=%s",
                product, product_version
            )
            product_data.pop(product_version)

        # Patch the config map
        config_map_data[product] = yaml.safe_dump(
            product_data, default_flow_style=False
        )
        LOGGER.info("ConfigMap update attempt=%s", attempt)
        try:
            api_instance.patch_namespaced_config_map(
                name, namespace, client.V1ConfigMap(data=config_map_data)
            )
            LOGGER.info("ConfigMap update attempt %s successful", attempt)
        except ApiException:
            LOGGER.exception("Error calling patch_namespaced_config_map")


def main():
    # Parameters to identify config map and product/version to remove
    PRODUCT = os.environ.get("PRODUCT").strip()  # required
    PRODUCT_VERSION = os.environ.get("PRODUCT_VERSION").strip()  # required
    CONFIG_MAP = os.environ.get("CONFIG_MAP", "cray-product-catalog").strip()
    CONFIG_MAP_NS = os.environ.get("CONFIG_MAP_NAMESPACE", "services").strip()
    KEY = os.environ.get("KEY", "").strip() or None

    args = (CONFIG_MAP, CONFIG_MAP_NS, PRODUCT, PRODUCT_VERSION, KEY)
    LOGGER.info(
        "Removing from config_map=%s in namespace=%s for %s/%s (key=%s)",
        *args
    )
    load_k8s()
    modify_config_map(*args)


if __name__ == "__main__":
    main()
