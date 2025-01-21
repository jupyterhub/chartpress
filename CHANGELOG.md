# Changelog for chartpress

## Unreleased

## 2.3

### 2.3.0 - 2025-01-21

#### New features added

- Allow specifying config file with cli option (#170) [#234](https://github.com/jupyterhub/chartpress/pull/234) ([@adamblake](https://github.com/adamblake), [@manics](https://github.com/manics))

#### Maintenance and upkeep improvements

- Remove `pipes` for compatibility with Python 3.13 [#242](https://github.com/jupyterhub/chartpress/pull/242) ([@adamblake](https://github.com/adamblake), [@minrk](https://github.com/minrk))

#### Documentation improvements

- Fix link to "Controlling development versions" section [#239](https://github.com/jupyterhub/chartpress/pull/239) ([@sunu](https://github.com/sunu), [@consideRatio](https://github.com/consideRatio))

#### Continuous integration improvements

- ci: test against python 3.12 and 3.13 [#245](https://github.com/jupyterhub/chartpress/pull/245) ([@consideRatio](https://github.com/consideRatio))

#### Other merged PRs

See [full changelog](https://github.com/jupyterhub/chartpress/compare/2.2.0...2.3.0) for dependabot and pre-commit.ci updates.

#### Contributors to this release

The following people contributed discussions, new ideas, code and documentation contributions, and review.
See [our definition of contributors](https://github-activity.readthedocs.io/en/latest/#how-does-this-tool-define-contributions-in-the-reports).

([GitHub contributors page for this release](https://github.com/jupyterhub/chartpress/graphs/contributors?from=2024-01-11&to=2025-01-21&type=c))

@adamblake ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Aadamblake+updated%3A2024-01-11..2025-01-21&type=Issues)) | @consideRatio ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3AconsideRatio+updated%3A2024-01-11..2025-01-21&type=Issues)) | @manics ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Amanics+updated%3A2024-01-11..2025-01-21&type=Issues)) | @minrk ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Aminrk+updated%3A2024-01-11..2025-01-21&type=Issues)) | @sunu ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Asunu+updated%3A2024-01-11..2025-01-21&type=Issues))

## 2.0

### 2.2.0 - 2024-01-11

([full changelog](https://github.com/jupyterhub/chartpress/compare/2.1.0...2.2.0))

#### Enhancements made

- Autoincrement base version from tag if not specified [#230](https://github.com/jupyterhub/chartpress/pull/230) ([@manics](https://github.com/manics), [@consideRatio](https://github.com/consideRatio), [@minrk](https://github.com/minrk))
- `chartPath`: Chart directory can be different from the chart name [#229](https://github.com/jupyterhub/chartpress/pull/229) ([@manics](https://github.com/manics), [@consideRatio](https://github.com/consideRatio))
- Add BRANCH expansion [#190](https://github.com/jupyterhub/chartpress/pull/190) ([@bleggett](https://github.com/bleggett), [@minrk](https://github.com/minrk))

#### Bugs fixed

- fix: skipPlatform for one image influenced other images [#193](https://github.com/jupyterhub/chartpress/pull/193) ([@consideRatio](https://github.com/consideRatio), [@manics](https://github.com/manics))

#### Maintenance and upkeep improvements

- maint: let tests check the output against another set of strings [#222](https://github.com/jupyterhub/chartpress/pull/222) ([@consideRatio](https://github.com/consideRatio), [@minrk](https://github.com/minrk))
- maint: make tests handle buildx 0.10+ and OCI index/manifest responses [#215](https://github.com/jupyterhub/chartpress/pull/215) ([@consideRatio](https://github.com/consideRatio), [@minrk](https://github.com/minrk))

#### Other merged PRs

See [full changelog](https://github.com/jupyterhub/chartpress/compare/2.1.0...2.2.0) for dependabot and pre-commit.ci updates.

#### Contributors to this release

The following people contributed discussions, new ideas, code and documentation contributions, and review.
See [our definition of contributors](https://github-activity.readthedocs.io/en/latest/#how-does-this-tool-define-contributions-in-the-reports).

([GitHub contributors page for this release](https://github.com/jupyterhub/chartpress/graphs/contributors?from=2022-09-08&to=2024-01-10&type=c))

@bleggett ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Ableggett+updated%3A2022-09-08..2024-01-10&type=Issues)) | @consideRatio ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3AconsideRatio+updated%3A2022-09-08..2024-01-10&type=Issues)) | @manics ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Amanics+updated%3A2022-09-08..2024-01-10&type=Issues)) | @minrk ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Aminrk+updated%3A2022-09-08..2024-01-10&type=Issues))

## 2.1

### 2.1.0 - 2022-09-08

#### Enhancements made

- accept non-prerelease baseVersion (append -0.dev) [#184](https://github.com/jupyterhub/chartpress/pull/184) ([@minrk](https://github.com/minrk), [@consideRatio](https://github.com/consideRatio))

## 2.0

### 2.0.0 - 2022-08-30

Make sure to read about the breaking changes and the release highlights below!

#### Breaking changes

If you are using chartpress to publish development releases should be aware that
the suffix appended to chart versions and image tags is changed to look like
`1.2.3-0.dev.git.n.hash`, where the following things has changed:

- `-0.dev` is appended by default for non pre-release versions.
- `n` is the number of commits on the branch, where it previously was the number
  of commits since the last tag on the branch.

#### Release highlights

- The option `baseVersion` is added to chart configuration in chartpress.yaml,
  for more details see the [README.md section on controlling development
  versions](https://github.com/jupyterhub/chartpress#controlling-development-versions).

#### New features added

- use baseVersion config to set the base version for development releases (supersedes useChartVersion config) [#179](https://github.com/jupyterhub/chartpress/pull/179) ([@minrk](https://github.com/minrk))

#### Enhancements made

- Allow extra options to be passed to docker build [#142](https://github.com/jupyterhub/chartpress/pull/142) ([@adamblake](https://github.com/adamblake))

#### Bugs fixed

- fix check for first-time publishing chart [#161](https://github.com/jupyterhub/chartpress/pull/161) ([@minrk](https://github.com/minrk))

#### Maintenance and upkeep improvements

- upload test coverage to codecov [#181](https://github.com/jupyterhub/chartpress/pull/181) ([@minrk](https://github.com/minrk))
- Enforce that `--reset` is an exclusive argument [#180](https://github.com/jupyterhub/chartpress/pull/180) ([@minrk](https://github.com/minrk))
- count commits on branch instead of commits since last tag on branch [#178](https://github.com/jupyterhub/chartpress/pull/178) ([@minrk](https://github.com/minrk))
- pre-commit: add pyupgrade and isort (replaces reorder-python-imports) [#173](https://github.com/jupyterhub/chartpress/pull/173) ([@consideRatio](https://github.com/consideRatio))
- (reverted) accept --tag arg in --reset [#152](https://github.com/jupyterhub/chartpress/pull/152) ([@minrk](https://github.com/minrk))
- (reverted) Add `useChartVersion` and change appended version suffix (now like `1.2.3-0.dev.git.3.h123`) [#150](https://github.com/jupyterhub/chartpress/pull/150) ([@minrk](https://github.com/minrk))
- Add tests with dev tags and backport branches [#145](https://github.com/jupyterhub/chartpress/pull/145) ([@minrk](https://github.com/minrk))
- Drop support for py36 and misc ci maintenance [#144](https://github.com/jupyterhub/chartpress/pull/144) ([@consideRatio](https://github.com/consideRatio))
- Remove six (no longer needed by docker) [#140](https://github.com/jupyterhub/chartpress/pull/140) ([@manics](https://github.com/manics))

#### Documentation improvements

- docs: update README about use with GitHub actions [#139](https://github.com/jupyterhub/chartpress/pull/139) ([@consideRatio](https://github.com/consideRatio))

#### Continuous integration improvements

- upload test coverage to codecov [#181](https://github.com/jupyterhub/chartpress/pull/181) ([@minrk](https://github.com/minrk))

#### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterhub/chartpress/graphs/contributors?from=2021-07-26&to=2022-08-30&type=c))

[@adamblake](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Aadamblake+updated%3A2021-07-26..2022-08-30&type=Issues) | [@consideRatio](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3AconsideRatio+updated%3A2021-07-26..2022-08-30&type=Issues) | [@manics](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Amanics+updated%3A2021-07-26..2022-08-30&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Aminrk+updated%3A2021-07-26..2022-08-30&type=Issues)

## 1.3

### 1.3.0 - 2021-07-26

This release improve performance significantly when building images for multiple
platforms. Chartpress can now can now also decide if such images needs to be
built and pushed, like it can for single platform images.

#### Enhancements made

- _image_needs_\[building|pushing\]: check platforms when using docker buildx [#136](https://github.com/jupyterhub/chartpress/pull/136) ([@manics](https://github.com/manics))

#### Maintenance and upkeep improvements

- remove unused \_strip_build_suffix_from_identifier [#137](https://github.com/jupyterhub/chartpress/pull/137) ([@manics](https://github.com/manics))

#### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterhub/chartpress/graphs/contributors?from=2021-07-23&to=2021-07-26&type=c))

[@consideRatio](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3AconsideRatio+updated%3A2021-07-23..2021-07-26&type=Issues) | [@manics](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Amanics+updated%3A2021-07-23..2021-07-26&type=Issues)

## 1.2

### 1.2.2 - 2021-07-23

The release of 1.2.1 was made incorrectly to PyPI, so this is another release to
fix the situation.

### 1.2.1 - 2021-07-23

#### Bugs fixed

- fix: use of github workflow tokens - different from PATs [#134](https://github.com/jupyterhub/chartpress/pull/134) ([@consideRatio](https://github.com/consideRatio))
- fix: mute handled git error messages [#133](https://github.com/jupyterhub/chartpress/pull/133) ([@consideRatio](https://github.com/consideRatio))

#### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterhub/chartpress/graphs/contributors?from=2021-06-23&to=2021-07-23&type=c))

[@consideRatio](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3AconsideRatio+updated%3A2021-06-23..2021-07-23&type=Issues) | [@yuvipanda](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Ayuvipanda+updated%3A2021-06-23..2021-07-23&type=Issues)

### 1.2.0 - 2021-06-23

#### New features added

- Define pre-commit hook [#127](https://github.com/jupyterhub/chartpress/pull/127) ([@minrk](https://github.com/minrk))

#### Maintenance and upkeep improvements

- Rename master to main [#128](https://github.com/jupyterhub/chartpress/pull/128) ([@consideRatio](https://github.com/consideRatio))

#### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterhub/chartpress/graphs/contributors?from=2021-04-12&to=2021-06-23&type=c))

[@consideRatio](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3AconsideRatio+updated%3A2021-04-12..2021-06-23&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Aminrk+updated%3A2021-04-12..2021-06-23&type=Issues)

## 1.1

### 1.1.0 - 2021-04-12

#### Enhancements made

- Optionally use buildx to build for multiple platforms [#123](https://github.com/jupyterhub/chartpress/pull/123) ([@manics](https://github.com/manics))
- Add skipPlatforms option for multi-platform docker buildx images [#124](https://github.com/jupyterhub/chartpress/pull/124) ([@manics](https://github.com/manics))

#### Maintenance and upkeep improvements

- Add mock tests for public chartpress methods that call commands [#120](https://github.com/jupyterhub/chartpress/pull/120) ([@manics](https://github.com/manics))
- Add pre-commit [#119](https://github.com/jupyterhub/chartpress/pull/119) ([@manics](https://github.com/manics))
- Update readme [#122](https://github.com/jupyterhub/chartpress/pull/122) ([@manics](https://github.com/manics))
- Fix pytest lru_cache invalidation [#121](https://github.com/jupyterhub/chartpress/pull/121) ([@manics](https://github.com/manics))

#### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterhub/chartpress/graphs/contributors?from=2021-01-20&to=2021-04-11&type=c))

[@consideRatio](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3AconsideRatio+updated%3A2021-01-20..2021-04-11&type=Issues) | [@manics](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Amanics+updated%3A2021-01-20..2021-04-11&type=Issues)

## 1.0

### 1.0.4 - 2021-01-20

#### Bugs fixed

- fix: preserve quote formatting for image tags also [#115](https://github.com/jupyterhub/chartpress/pull/115) ([@consideRatio](https://github.com/consideRatio))

#### Maintenance and upkeep improvements

- refactor: rename two local variables for readability [#114](https://github.com/jupyterhub/chartpress/pull/114) ([@consideRatio](https://github.com/consideRatio))

### 1.0.3 - 2020-12-14

#### Enhancements made

- allow standard `--no-build` prefix for disabling builds [#110](https://github.com/jupyterhub/chartpress/pull/110) ([@minrk](https://github.com/minrk))

#### Bugs fixed

- Fix --list-images to not update Chart.yaml's version [#112](https://github.com/jupyterhub/chartpress/pull/112) ([@consideRatio](https://github.com/consideRatio))

#### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterhub/chartpress/graphs/contributors?from=2020-12-04&to=2020-12-14&type=c))

[@consideRatio](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3AconsideRatio+updated%3A2020-12-04..2020-12-14&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Aminrk+updated%3A2020-12-04..2020-12-14&type=Issues)

### 1.0.2 - 2020-12-04

#### Bugs fixed

- only apply strict version checking for charts to be published [#109](https://github.com/jupyterhub/chartpress/pull/109) ([@minrk](https://github.com/minrk))
- fix: compute tag per image [#108](https://github.com/jupyterhub/chartpress/pull/108) ([@danielnorberg](https://github.com/danielnorberg))

#### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterhub/chartpress/graphs/contributors?from=2020-12-03&to=2020-12-04&type=c))

[@consideRatio](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3AconsideRatio+updated%3A2020-12-03..2020-12-04&type=Issues) | [@danielnorberg](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Adanielnorberg+updated%3A2020-12-03..2020-12-04&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Aminrk+updated%3A2020-12-03..2020-12-04&type=Issues)

### 1.0.1 - 2020-12-03

#### Bugs fixed

- bugfix: multiple images built was evaluating to a single tag [#107](https://github.com/jupyterhub/chartpress/pull/107) ([@consideRatio](https://github.com/consideRatio))

#### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterhub/chartpress/graphs/contributors?from=2020-11-21&to=2020-12-03&type=c))

[@consideRatio](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3AconsideRatio+updated%3A2020-11-21..2020-12-03&type=Issues)

### 1.0.0 - 2020-11-21

[@betatim](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Abetatim+updated%3A2018-02-23..2020-11-21&type=Issues) | [@consideRatio](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3AconsideRatio+updated%3A2018-02-23..2020-11-21&type=Issues) | [@jacobtomlinson](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Ajacobtomlinson+updated%3A2018-02-23..2020-11-21&type=Issues) | [@jirikuncar](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Ajirikuncar+updated%3A2018-02-23..2020-11-21&type=Issues) | [@leafty](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Aleafty+updated%3A2018-02-23..2020-11-21&type=Issues) | [@manics](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Amanics+updated%3A2018-02-23..2020-11-21&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Aminrk+updated%3A2018-02-23..2020-11-21&type=Issues) | [@rokroskar](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Arokroskar+updated%3A2018-02-23..2020-11-21&type=Issues) | [@yuvipanda](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Ayuvipanda+updated%3A2018-02-23..2020-11-21&type=Issues)

The 1.0.0 release can be seen as a reflection of chartpress having become quite
reliable, thank you everyone for your contributions and work on it!!!

#### Enhancements made

- Strip v prefixes for Chart.yaml versions for Helm3 compliancy [#106](https://github.com/jupyterhub/chartpress/pull/106) ([@consideRatio](https://github.com/consideRatio))
- Add --force-publish-chart and default to not overwriting [#102](https://github.com/jupyterhub/chartpress/pull/102) ([@consideRatio](https://github.com/consideRatio))

#### Maintenance and upkeep improvements

- Major refactor for readability pre 1.0.0 release [#105](https://github.com/jupyterhub/chartpress/pull/105) ([@consideRatio](https://github.com/consideRatio))
- Migrate from Travis CI to GitHub Actions [#101](https://github.com/jupyterhub/chartpress/pull/101) ([@consideRatio](https://github.com/consideRatio))
- CI: fix syntax typo making us not run tests before publish [#100](https://github.com/jupyterhub/chartpress/pull/100) ([@consideRatio](https://github.com/consideRatio))

## 0.7

### 0.7.0 - 2020-11-02

#### Enhancements made

- Image config option added: rebuildOnContextPathChanges [#98](https://github.com/jupyterhub/chartpress/pull/98) ([@consideRatio](https://github.com/consideRatio))
- add chartpress --list-images [#96](https://github.com/jupyterhub/chartpress/pull/96) ([@minrk](https://github.com/minrk))
- support overriding imageName [#90](https://github.com/jupyterhub/chartpress/pull/90) ([@minrk](https://github.com/minrk))

#### Maintenance and upkeep improvements

- CI: publish tags without tests and test python 3.6-3.8 [#95](https://github.com/jupyterhub/chartpress/pull/95) ([@consideRatio](https://github.com/consideRatio))
- CI: Test chartpress usage with both helm2 and helm3 [#92](https://github.com/jupyterhub/chartpress/pull/92) ([@consideRatio](https://github.com/consideRatio))

#### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterhub/chartpress/graphs/contributors?from=2020-01-12&to=2020-11-01&type=c))

[@consideRatio](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3AconsideRatio+updated%3A2020-01-12..2020-11-01&type=Issues) | [@manics](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Amanics+updated%3A2020-01-12..2020-11-01&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Aminrk+updated%3A2020-01-12..2020-11-01&type=Issues)

## 0.6

### 0.6.0 - 2020-01-12

0.6.0 include a single fix to avoid breaking SemVer 2 validity, which is
essential for Helm 3 compatibility. The change is to prefix build number and
build hash with `n` and `h` respectively. The reason for doing this is that it
ensures we don't break the SemVer 2 assumption to not have a numerical segment
starting with zero, like for example `0.1.0-002.sdfg234` has with its `002`.
Helm 3 enforce this, while Helm 2 doesn't.

#### Fixes

- Prefix build info with n and h to ensure SemVer 2 validity, in order to solve Helm 3 compatibility [#87](https://github.com/jupyterhub/chartpress/pull/87) ([@consideRatio](https://github.com/consideRatio))

## 0.5

### 0.5.0 - 2019-12-01

#### Added

- Add --force-build / --force-push, and don't let --tag imply it [#70](https://github.com/jupyterhub/chartpress/pull/70) ([@consideRatio](https://github.com/consideRatio))
- `helm dependency update` is now run as part of publishing, this ensures we honor requirements.yaml before publishing a chart [#69](https://github.com/jupyterhub/chartpress/pull/69) ([@consideRatio](https://github.com/consideRatio))

#### Fixes

- Fix regression to make a chart's `images` configuration optional again [#77](https://github.com/jupyterhub/chartpress/pull/77) ([@jacobtomlinson](https://github.com/jacobtomlinson))
- Fix regarding image paths as part of setting up thorough testing with PyTest [#68](https://github.com/jupyterhub/chartpress/pull/68) ([@consideRatio](https://github.com/consideRatio))

#### Maintenance

- Setup CD of PyPI releases on git tag pushes [#83](https://github.com/jupyterhub/chartpress/pull/83) ([@consideRatio](https://github.com/consideRatio))
- Adopt bump2version for automating version bumps [#74](https://github.com/jupyterhub/chartpress/pull/74) ([@minrk](https://github.com/minrk))

## 0.4

### 0.4.3 - 2019-10-29 (Breaking changes)

0.4.3 contains important bug fixes for versions `0.4.0` to `0.4.2`. A big bug
fixed was that charts published using `--publish-chart` replaced previous charts
in the helm chart repositories' `index.yaml` file that only differed by a SemVer
2 compliant build suffix like `+001.asdf123`. The bugfixes introduced in this
release avoid this issue, caused by a bug in helm, by using a build suffix of
`.001.asdf123` instead - a breaking change.

Example versions to expect in this release and onwards are given below where
some commits were made in between git tagged (`0.1.0` and `0.2.0-beta.1`)
commits.

```
# without --long
0.1.0
0.1.0-002.sdfg234
0.2.0-beta.1
0.2.0-beta.1.003.asdf123

# with --long
0.1.0-000.qwer123
0.1.0-002.sdfg234
0.2.0-beta.1.000.wert234
0.2.0-beta.1.003.asdf123
```

- Fix latest tagged commit
  [#66](https://github.com/jupyterhub/chartpress/pull/66)
  ([@minrk](https://github.com/minrk))
- Fix bugs: index merge, image tag, g prefix, ignored tags
  [#64](https://github.com/jupyterhub/chartpress/pull/64)
  ([@consideRatio](https://github.com/consideRatio))
- Support `valuesPath` pointing to a single `image:tag` string in addition to a
  dict with separate `repository` and `tag` keys
  [#63](https://github.com/jupyterhub/chartpress/pull/63)
  ([@minrk](https://github.com/minrk)).
- Support lists in `valuesPath` by using integer indices
  [#65](https://github.com/jupyterhub/chartpress/pull/65)
  ([@minrk](https://github.com/minrk)), e.g. `section.list.1.image` for the
  yaml:
  ```yaml
  section:
    list:
      - first: item
        image: "not set"
      - second: item
        image: "image:tag" #  <--sets this here
  ```

### 0.4.2 - 2019-10-19 (broken)

- --long flag to always output build information in image tags and chart version [#57](https://github.com/jupyterhub/chartpress/pull/57) ([@consideRatio](https://github.com/consideRatio))
- Refactor publish_pages for comprehensibility [#56](https://github.com/jupyterhub/chartpress/pull/56) ([@consideRatio](https://github.com/consideRatio))

### 0.4.1 - 2019-10-17 (broken)

- Deprecate --commit-range [#55](https://github.com/jupyterhub/chartpress/pull/55) ([@consideRatio](https://github.com/consideRatio))
- Reset Chart.yaml's version to a valid value [#54](https://github.com/jupyterhub/chartpress/pull/54) ([@consideRatio](https://github.com/consideRatio))
- Don't append +build on tagged commits [#53](https://github.com/jupyterhub/chartpress/pull/53) ([@consideRatio](https://github.com/consideRatio))

### 0.4.0 - 2019-10-17 (broken)

- Chart and image versioning, and Chart.yaml's --reset interaction [#52](https://github.com/jupyterhub/chartpress/pull/52) ([@consideRatio](https://github.com/consideRatio))
- Add --version flag [#45](https://github.com/jupyterhub/chartpress/pull/45) ([@consideRatio](https://github.com/consideRatio))

## 0.3

### 0.3.2 - 2019-10-05

- Update chartpress --help output in README.md [#42](https://github.com/jupyterhub/chartpress/pull/42) ([@consideRatio](https://github.com/consideRatio))
- Add initial setup when starting from scratch [#36](https://github.com/jupyterhub/chartpress/pull/36) ([@manics](https://github.com/manics))
- avoid mangling of quotes in rendered charts (#1) [#34](https://github.com/jupyterhub/chartpress/pull/34) ([@rokroskar](https://github.com/rokroskar))
- Add --skip-build and add --reset to reset image tags as well as chart version [#28](https://github.com/jupyterhub/chartpress/pull/28) ([@rokroskar](https://github.com/rokroskar))

### 0.3.1 - 2019-02-07

- Fix conditionals for builds with new tagging scheme,
  by checking if images exist locally or on the registry
  rather than assuming the correct tag was pushed based on commit range.
- Echo shell commands that are executed during the chartpress process

### 0.3.0 - 2019-02-07

- Add chart version as prefix to image tags (e.g. 0.8-abc123)
- Fix requires-python metadata to specify that Python 3.6 is required

## 0.2

### 0.2.2 - 2018-09-19

- Another ruamel.yaml type fix

### 0.2.1 - 2018-09-10

- Add `--image-prefix` option
- Workaround ruamel.yaml bug when strings are all-digits
  and start with 0 and contain an 8 or 9.
- Fix type checking for recent ruamel.yaml

### 0.2.0 - 2018-05-29

- Fix image tagging when building multiple images
- Make image-building optional
- Show changes being made
- Support GITHUB_TOKEN env for pushing to gh-pages
- Include chartpress.yaml when resolving last changed ref
- Update only necessary fields

## 0.1

### 0.1.1 - 2018-02-23

- Add missing dependency on ruamel.yaml

### 0.1.0 - 2018-02-23

first release!
