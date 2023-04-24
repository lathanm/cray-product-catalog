# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- dependabot: Bump `jsonschema` from 4.4.0 to 4.17.3
- dependabot: Bump `kubernetes` from 23.3.0 to 26.1.0
- dependabot: Bump `certifi` from 2021.10.8 to 2022.12.7
- dependabot: Bump `oauthlib` from 3.2.0 to 3.2.2
- dependabot: Bump `rsa` from 4.8 to 4.9
- dependabot: Bump `idna` from 3.3 to 3.4
- dependabot: Bump `cachetools` from 5.0.0 to 5.3.0
- dependabot: Bump `google-auth` from 2.17.2 to 2.17.3

## [1.8.5] - 2023-04-11

### Changed

- dependabot: Bump `charset-normalizer` from 2.0.12 to 3.1.0.
- dependabot: Bump `attrs` from 21.4.0 to 22.2.0.
- dependabot: Bump `pyrsistent` from 0.18.1 to 0.19.3.
- dependabot: Bump `requests` from 2.27.1 to 2.28.2

## [1.8.4] - 2023-04-07

### Changed

- dependabot: Bump `google-auth` from 2.6.0 to 2.17.2
- dependabot: Bump `websocket-client` from 1.3.1 to 1.5.1
- dependabot: Bump `urllib3` from 1.26.8 to 1.26.15

## [1.8.3] - 2023-04-06

### Fixed

- Fixed bad image path in the helm chart

### Changed

- Updated chart maintainer
- Correct version strings used in Chart

## [1.8.2] - 2023-01-10

### Fixed

- Fixed an issue where inserting certain types of data would loop forever.

## [1.8.1] - 2022-12-20

### Added

- Add Artifactory authentication to Jenkinsfile

## [1.8.0] - 2022-12-20

### Added

- Added an environment variable `REMOVE_ACTIVE_FIELD`. When set, the `catalog_update`
  script will remove the 'active' field for all versions of the given product.

### Changed

- Modified github workflow for checking license text to use authenticated access to
  artifactory server hosting license-checker image.

- Changed format of log messages to be prefixed with severity.

### Fixed

- Fixed an issue where log messages from child modules were not being printed.

## [1.7.0] - 2022-11-17

### Changed

- Added a github workflow for checking license text separate from the organization-
  wide "license-check" workflow.

- Reverted github workflows regarding image building and publishing and 
  releases back to Jenkins pipelines.

- Renamed `YAML_CONTENT` environment variable to `YAML_CONTENT_FILE`. For
  backwards compatibility, `YAML_CONTENT` can still be used.

### Added

- Added an environment variable `YAML_CONTENT_STRING` so that data can be passed in
  string form rather than in file form.

- Improved concurrency handling by checking for resource conflicts when updating
  the config map.

- Improved the ability to update more specific portions of the config map by adding
  a recursive `merge_dict` utility that is used to merge input data into the existing
  config map.

## [1.6.0] - 2022-05-09

### Added

- Added new `query` module to query the `cray-product-catalog` K8s ConfigMap to
  obtain information about the installed products.

### Changed

- Relaxed schema for product data added to `cray-product-catalog` K8s ConfigMap
  to allow additional properties.

- Update base image to artifactory.algol60.net/csm-docker/stable/docker.io/library/alpine:3.15

- Update license text to comply with automatic license-check tool.

- Update deploy script to work with CSM 1.2 systems and Nexus authentication

### Fixed

- Fixed location where Python module and Helm chart are published to
  Artifactory by "Build Artifacts" GitHub Actions workflow.

## [1.5.5] - 2022-03-04

### Changed

- Update the image signing and software bill of materials github actions (Cray
  HPE internal actions) to use the preferred GCP authentication.

- CASMCMS-7878 - switch build artifacts workflow build-prep step to ubuntu
  public runner per GitHub security recommendations

- Update python dependencies

## [1.5.4] - 2022-02-15

### Changed

- Save build artifacts for default of 90 days

- Push all semver docker image tags, not just the image:x.y.z-builddate.commit tag

- Bump jfrog/setup-jfrog-cli from 1 to 2.1.0

- Bump cardinalby/git-get-release-action from 1.1 to 1.2.2

- Bump rsa from 4.7 to 4.8

- Bump python-dateutil from 2.7.5 to 2.8.2


## [1.5.3] - 2022-02-08

### Changed

- Use csm-changelog-checker and csm-gitflow-mergeback actions in common workflows

## [1.5.2] - 2022-02-02

### Removed

- Autoapprove PR action for gitflow mergeback PRs

## [1.5.1] - 2022-02-02

### Added

- Automerge capabilities for gitflow mergeback PRs

### Changed

- PR title in gitflow mergeback PRs is repo-specific so including them in
  release notes and in different repo PRs, they refer to original PRs

## [1.5.0] - 2022-02-01

### Added

- Added reference to Keep a Changelog format to README file

- Added reference to CSM Gitflow development process to README file

### Removed

- Remove redundant license/copyright info from README

## [1.4.23] - 2022-01-27

### Changed

- Restrict the changelog and artifact pr workflows to not run on gitflow and
  dependency update PRs

- dependabot update python dep attrs from 21.2.0 to 21.4.0

## [1.4.22] - 2022-01-27

### Changed

- Fixed gitflow mergeback workflow to use correct app key/id

## [1.4.21] - 2022-01-26

### Changed

- Let PR artifacts deploy workflow time out if it doesn't find a matching build

## [1.4.20] - 2022-01-26

### Changed

- Update gitflow mergeback workflow to use continuous update strategy

## [1.4.19] - 2022-01-26

### Added

- Add gitflow mergeback workflow

## [1.4.18] - 2022-01-26

### Added

- Allow Github releases to be updated when rebuilding tagged releases
  (for rebuilds to fix CVEs, etc)

## [1.4.17] - 2022-01-26

### Changed

- Fix release note rendering for stable releases

## [1.4.15] - 2022-01-25

### Changed

- Update to use new "no ref needed" reusable workflow

## [1.4.14] - 2022-01-21

### Added

- Update CSM manifest workflow

- Release workflow to build artifacts and create GH releases on tags

### Changed

- Build artifacts workflow is now reusable, no longer builds on tag events

### Removed

- Removed old and unused release prep workflows

## [1.4.13] - 2022-01-20

### Added

- Add changelog checker workflow

## [1.4.12] - 2022-01-19

- Test release with only CHANGELOG updates

## [1.4.11] - 2022-01-19

### Added

- Added workflows for finishing gitflow release and merging back to develop

## [1.4.10] - 2022-01-13

### Changed

- Only build artifacts on push events, not PRs. Change PR comments to point to the individual commit, not the overall PR.

## [1.4.6] - 2022-01-07

### Changed

- Fix the draft release PR workflow to add labels

## [1.4.5] - 2022-01-07

### Added

- Add workflows for creating PRs for a draft release, and tagging and release creation when a release branch is merged to master.

## [1.4.4] - 2022-01-07

### Added

- Build docker image, helm chart, python module with GH actions (CASMCMS-7698)

## [1.4.3] - 2022-01-05

### Changed

- Change default behavior to stop setting "active" key unless `SET_ACTIVE_VERSION` variable is given.

## 1.4.2 - 2021-12-01

### Changed

- Updated README to reflect versioning change in v1.4.1.

## 1.4.1 - 2021-12-01

### Changed

- Changed GitVersion.yml to ignore previous CSM release branches

## 1.4.0 - 2021-11-29

### Added

- Build docker image with CSM-provided build-scan-sign GH action

- Add GitVersion.yml for automatic git versioning using Gitflow

- Pull python requirements from PyPI, not arti.dev.cray.com to enable GH actions builds

## 1.3.1 - 2021-11-19

### Added

- Added pull request template

- Added Chart lint, test, scan action

### Changed

- Conformed chart to CASM-2670 specifications (CASMCMS-7619)

## 1.2.71 - 2017-11-15

### Added

- Included cray-product-catalog python module

- Introduce new catalog entry delete functionality

### Changed

- Updated repo to Gitflow branching strategy; develop branch now base branch

- Change default reviewers to CMS-core-product-support

[Unreleased]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.8.5...HEAD

[1.8.5]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.8.4...v1.8.5

[1.8.4]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.8.3...v1.8.4

[1.8.3]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.8.2...v1.8.3

[1.8.2]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.8.1...v1.8.2

[1.8.1]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.8.0...v1.8.1

[1.8.0]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.7.0...v1.8.0

[1.7.0]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.6.0...v1.7.0

[1.6.0]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.5.5...v1.6.0

[1.5.5]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.5.4...v1.5.5

[1.5.4]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.5.3...v1.5.4

[1.5.3]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.5.2...v1.5.3

[1.5.2]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.5.1...v1.5.2

[1.5.1]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.5.0...v1.5.1

[1.5.0]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.4.23...v1.5.0

[1.4.23]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.4.22...v1.4.23

[1.4.22]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.4.21...v1.4.22

[1.4.21]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.4.20...v1.4.21

[1.4.20]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.4.19...v1.4.20

[1.4.19]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.4.18...v1.4.19

[1.4.18]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.4.17...v1.4.18

[1.4.17]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.4.15..v.1.4.17

[1.4.15]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.4.14...v1.4.15

[1.4.14]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.4.13...v1.4.14

[1.4.13]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.4.12...v1.4.13

[1.4.12]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.4.11...v1.4.12

[1.4.11]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.4.10...v1.4.11

[1.4.10]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.4.6...v1.4.10

[1.4.6]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.4.5...v1.4.6

[1.4.5]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.4.4...v1.4.5

[1.4.4]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.4.3...v1.4.4

[1.4.3]: https://github.com/Cray-HPE/cray-product-catalog/compare/v1.4.2...v1.4.3
