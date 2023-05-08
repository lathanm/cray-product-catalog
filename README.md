# Cray Product Catalog

This repository contains the Docker image definition for the cray-product-catalog-update
image. This image provides a script that uploads the contents of a yaml file to
a product catalog entry, which serves as a kubernetes config map.

See the [CSM Compatibility Matrix](https://github.com/Cray-HPE/cray-product-catalog/wiki/CSM-Compatibility-Matrix)
for more information about what version of the Cray Product Catalog Update image to
use in your product.

At minimum, the `catalog_update.py` script takes environment variables `PRODUCT`
and `PRODUCT_VERSION` and applies the content of a file denoted by
`YAML_CONTENT_FILE` file as follows:

```yaml
{PRODUCT}:
  {PRODUCT_VERSION}:
    {content of yaml file (in YAML_CONTENT_FILE)}
```

For backwards compatibility, the environment variable `YAML_CONTENT` is
equivalent to `YAML_CONTENT_FILE`. As an alternative to `YAML_CONTENT_FILE`,
a YAML-formatted string may be passed using the environment variable
`YAML_CONTENT_STRING`.

The product catalog is a lightweight software inventory of sorts, and allows for
system users to view a product and its associated versions and version metadata
that have been _installed_ on the system.

The cray-product-catalog-update image is assumed to be running in the CSM
Kubernetes cluster by an actor that has permissions to read and update config
maps in the namespace that is configured.

Additionally, this repository provides the `cray-product-catalog` config map,
which is managed by the cray-product-catalog Helm chart.

## Getting Started

The main use case for cray-product-catalog is for a product to add install-time
information and metadata to the cray-product-catalog config map located in the
services namespace via a Kubernetes job as part of a Helm chart. The image
could also be used via podman on an NCN, but this has not been tested.

## Example Usage

### Helm Chart

Two seminal examples of using cray-product-catalog are the `cray-import-config`
and `cray-import-kiwi-recipe-image` base charts. Review the values files and
Kubernetes job template to see cray-product-catalog in action.

* [cray-import-config](https://github.com/Cray-HPE/cray-product-install-charts/tree/master/charts/cray-import-config)
* [cray-import-kiwi-recipe-image](https://github.com/Cray-HPE/cray-product-install-charts/tree/master/charts/cray-import-kiwi-recipe-image)

### Podman on NCN

To create an entry in the config map for an "example" product with version
1.2.3, you can use podman on a Kubernetes worker/master node. Be sure to mount
the Kubernetes config file into the running container as well as the
`YAML_CONTENT_FILE`.

```bash
ncn-w001:~/ # podman run --rm --name example-cpc --network podman-cni-config \
    -e PRODUCT=example \
    -e PRODUCT_VERSION=1.2.3 \
    -e YAML_CONTENT_FILE=/results/example.yaml \
    -e KUBECONFIG=/.kube/admin.conf \
    -v /etc/kubernetes:/.kube:ro \
    -v ${PWD}:/results:ro \
    artifactory.algol60.net/csm-docker/stable/cray-product-catalog-update:1.2.57
Updating config_map=cray-product-catalog in namespace=services for product/version=example/1.2.3
Retrieving content from /results/example.yaml
Resting 3s before reading ConfigMap
Product=example does not exist; will update
ConfigMap update attempt=1
Resting 2s before reading ConfigMap
ConfigMap data updates exist; Exiting.
```

View the results in a nice format:

```bash
ncn-w001:~/ # kubectl get cm -n services cray-product-catalog -o json | jq .data.example | ./yq r -
1.2.3:
  this:
    is: some
    yaml: stuff
```

## Configuration

All configuration options are provided as environment variables.

### Required Environment Variables

* `PRODUCT` = (no default)

> The name of the Cray/Shasta product that is being cataloged.

* `PRODUCT_VERSION` = (no default)

> The SemVer version of the Cray/Shasta product that is being imported, e.g.
  `1.2.3`.

* One of:

    * `YAML_CONTENT_FILE` = (no default)

      > The filesystem location of the YAML that will be added to the config map.

    * `YAML_CONTENT` = (no default)

      > Equivalent to `YAML_CONTENT_FILE`, included for backwards compatibility.

    * `YAML_CONTENT_STRING` = (no default)

      > A YAML-formatted string to be used as an alternative to `YAML_CONTENT_FILE`.

### Optional Environment Variables

 * `CONFIG_MAP` = `cray-product-catalog`

 > The name of the config map to add the `YAML_CONTENT_FILE` to.

 * `CONFIG_MAP_NAMESPACE` = `services`

 > The Kubernetes namespace of the `CONFIG_MAP`.

 * `SET_ACTIVE_VERSION` = `''`

 > When set, the given product-version will have a field called 'active' set to `true`. Other
 > versions of the product will automatically have the field set to `false.` Cannot be used with
 > `REMOVE_ACTIVE_FIELD` (see below).

 * `REMOVE_ACTIVE_FIELD` = `''`

 > When set, all versions of the given product will have the 'active' field removed from the
 > ConfigMap data. Cannot be used with `SET_ACTIVE_VERSION` (see above).

 * `UPDATE_OVERWRITE` = `''`

> When set, the catalog_update function will perform an update that will
> overwrite the keys in the config map. Contrasted to the default implementation
> which will perform a merge operation between the two maps.
> This is useful for removing nested data or just simply removing entire
> entries from the config map.

## Versioning and Releases

Versions are calculated automatically using `gitversion`. The full SemVer
output is governed by the `GitVersion.yml` file in the root of this repo.

Run `gitversion -output json` to see the current version based on the checked
out commit.

Create a release by triggering the [Draft New Release](https://github.com/Cray-HPE/cray-product-catalog/actions/workflows/draft-new-release.yml)
workflow with the version that will be released.

Releases are automatically published when pull requests to the master branch
are merged.

## Contributing

This repo uses [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
and the [CSM Gitflow Development Process]( https://github.com/Cray-HPE/community/wiki/Gitflow-Development-Process).

CMS-core-product-support team members should make a branch. Others, make a fork.

## Built With

* Alpine Linux
* Python 3
* Python Requests
* Kubernetes Python Client
* Docker
* [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
* [Gitversion](https://gitversion.net)
* Good intentions

## Changelog

See the [CHANGELOG](CHANGELOG.md) for changes. This file uses the [Keep A Changelog](https://keepachangelog.com)
format.

## Copyright and License
This project is copyrighted by Hewlett Packard Enterprise Development LP and is under the MIT
license. See the [LICENSE](LICENSE) file for details.

