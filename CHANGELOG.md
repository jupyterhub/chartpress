# Changelog for chartpress

## Unreleased

## [0.7]

### [0.7.0] - UNRELEASED

#### Enhancements made

* Image config option added: rebuildOnContextPathChanges [#98](https://github.com/jupyterhub/chartpress/pull/98) ([@consideRatio](https://github.com/consideRatio))
* add chartpress --list-images [#96](https://github.com/jupyterhub/chartpress/pull/96) ([@minrk](https://github.com/minrk))
* support overriding imageName [#90](https://github.com/jupyterhub/chartpress/pull/90) ([@minrk](https://github.com/minrk))

#### Maintenance and upkeep improvements

* CI: publish tags without tests and test python 3.6-3.8 [#95](https://github.com/jupyterhub/chartpress/pull/95) ([@consideRatio](https://github.com/consideRatio))
* CI: Test chartpress usage with both helm2 and helm3 [#92](https://github.com/jupyterhub/chartpress/pull/92) ([@consideRatio](https://github.com/consideRatio))

#### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterhub/chartpress/graphs/contributors?from=2020-01-12&to=2020-11-01&type=c))

[@consideRatio](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3AconsideRatio+updated%3A2020-01-12..2020-11-01&type=Issues) | [@manics](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Amanics+updated%3A2020-01-12..2020-11-01&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyterhub%2Fchartpress+involves%3Aminrk+updated%3A2020-01-12..2020-11-01&type=Issues)


## [0.6]

### [0.6.0] - 2020-01-12

0.6.0 include a single fix to avoid breaking SemVer 2 validity, which is
essential for Helm 3 compatibility. The change is to prefix build number and
build hash with `n` and `h` respectively. The reason for doing this is that it
ensures we don't break the SemVer 2 assumption to not have a numerical segment
starting with zero, like for example `0.1.0-002.sdfg234` has with its `002`.
Helm 3 enforce this, while Helm 2 doesn't.

#### Fixes

- Prefix build info with n and h to ensure SemVer 2 validity, in order to solve Helm 3 compatibility [#87](https://github.com/jupyterhub/chartpress/pull/87) ([@consideRatio](https://github.com/consideRatio))

## [0.5]

### [0.5.0] - 2019-12-01

#### Added

- Add --force-build / --force-push, and don't let --tag imply it [#70](https://github.com/jupyterhub/chartpress/pull/70) ([@consideRatio](https://github.com/consideRatio))
- `helm dependency update` is now run as part of publishing, this ensures we honor requirements.yaml before publishing a chart [#69](https://github.com/jupyterhub/chartpress/pull/69) ([@consideRatio](https://github.com/consideRatio))

#### Fixes

- Fix regression to make a chart's `images` configuration optional again [#77](https://github.com/jupyterhub/chartpress/pull/77) ([@jacobtomlinson](https://github.com/jacobtomlinson))
- Fix regarding image paths as part of setting up thorough testing with PyTest [#68](https://github.com/jupyterhub/chartpress/pull/68) ([@consideRatio](https://github.com/consideRatio))

#### Maintenance

- Setup CD of PyPI releases on git tag pushes [#83](https://github.com/jupyterhub/chartpress/pull/83) ([@consideRatio](https://github.com/consideRatio))
- Adopt bump2version for automating version bumps [#74](https://github.com/jupyterhub/chartpress/pull/74) ([@minrk](https://github.com/minrk))

## [0.4]

### [0.4.3] - 2019-10-29 (Breaking changes)

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
        image: "image:tag"  #  <--sets this here
  ```

### [0.4.2] - 2019-10-19 (broken)

- --long flag to always output build information in image tags and chart version [#57](https://github.com/jupyterhub/chartpress/pull/57) ([@consideRatio](https://github.com/consideRatio))
- Refactor publish_pages for comprehensibility [#56](https://github.com/jupyterhub/chartpress/pull/56) ([@consideRatio](https://github.com/consideRatio))

### [0.4.1] - 2019-10-17 (broken)

- Deprecate --commit-range [#55](https://github.com/jupyterhub/chartpress/pull/55) ([@consideRatio](https://github.com/consideRatio))
- Reset Chart.yaml's version to a valid value [#54](https://github.com/jupyterhub/chartpress/pull/54) ([@consideRatio](https://github.com/consideRatio))
- Don't append +build on tagged commits [#53](https://github.com/jupyterhub/chartpress/pull/53) ([@consideRatio](https://github.com/consideRatio))

### 0.4.0 - 2019-10-17 (broken)

- Chart and image versioning, and Chart.yaml's --reset interaction [#52](https://github.com/jupyterhub/chartpress/pull/52) ([@consideRatio](https://github.com/consideRatio))
- Add --version flag [#45](https://github.com/jupyterhub/chartpress/pull/45) ([@consideRatio](https://github.com/consideRatio))

## [0.3]

### [0.3.2] - 2019-10-05

- Update chartpress --help output in README.md [#42](https://github.com/jupyterhub/chartpress/pull/42) ([@consideRatio](https://github.com/consideRatio))
- Add initial setup when starting from scratch [#36](https://github.com/jupyterhub/chartpress/pull/36) ([@manics](https://github.com/manics))
- avoid mangling of quotes in rendered charts (#1) [#34](https://github.com/jupyterhub/chartpress/pull/34) ([@rokroskar](https://github.com/rokroskar))
- Add --skip-build and add --reset to reset image tags as well as chart version [#28](https://github.com/jupyterhub/chartpress/pull/28) ([@rokroskar](https://github.com/rokroskar))

### [0.3.1] - 2019-02-07

- Fix conditionals for builds with new tagging scheme,
  by checking if images exist locally or on the registry
  rather than assuming the correct tag was pushed based on commit range.
- Echo shell commands that are executed during the chartpress process

### [0.3.0] - 2019-02-07

- Add chart version as prefix to image tags (e.g. 0.8-abc123)
- Fix requires-python metadata to specify that Python 3.6 is required

## [0.2]

### [0.2.2] - 2018-09-19

- Another ruamel.yaml type fix

### [0.2.1] - 2018-09-10

- Add `--image-prefix` option
- Workaround ruamel.yaml bug when strings are all-digits
  and start with 0 and contain an 8 or 9.
- Fix type checking for recent ruamel.yaml

### [0.2.0] - 2018-05-29

- Fix image tagging when building multiple images
- Make image-building optional
- Show changes being made
- Support GITHUB_TOKEN env for pushing to gh-pages
- Include chartpress.yaml when resolving last changed ref
- Update only necessary fields

## [0.1]

### [0.1.1] - 2018-02-23

- Add missing dependency on ruamel.yaml

### [0.1.0] - 2018-02-23

first release!
