# Changelog for chartpress

## Unreleased

## 0.4

### 0.4.1

- Deprecate --commit-range [#55](https://github.com/jupyterhub/chartpress/pull/55) ([@consideRatio](https://github.com/consideRatio))
- Reset Chart.yaml's version to a valid value [#54](https://github.com/jupyterhub/chartpress/pull/54) ([@consideRatio](https://github.com/consideRatio))
- Don't append +build on tagged commits [#53](https://github.com/jupyterhub/chartpress/pull/53) ([@consideRatio](https://github.com/consideRatio))

### 0.4.0

- Chart and image versioning, and Chart.yaml's --reset interaction [#52](https://github.com/jupyterhub/chartpress/pull/52) ([@consideRatio](https://github.com/consideRatio))
- Add --version flag [#45](https://github.com/jupyterhub/chartpress/pull/45) ([@consideRatio](https://github.com/consideRatio))

## 0.3

### 0.3.2

- Update chartpress --help output in README.md [#42](https://github.com/jupyterhub/chartpress/pull/42) ([@consideRatio](https://github.com/consideRatio))
- Add initial setup when starting from scratch [#36](https://github.com/jupyterhub/chartpress/pull/36) ([@manics](https://github.com/manics))
- avoid mangling of quotes in rendered charts (#1) [#34](https://github.com/jupyterhub/chartpress/pull/34) ([@rokroskar](https://github.com/rokroskar))
- Add --skip-build and add --reset to reset image tags as well as chart version [#28](https://github.com/jupyterhub/chartpress/pull/28) ([@rokroskar](https://github.com/rokroskar))

### 0.3.1

- Fix conditionals for builds with new tagging scheme,
  by checking if images exist locally or on the registry
  rather than assuming the correct tag was pushed based on commit range.
- Echo shell commands that are executed during the chartpress process

### 0.3.0

- Add chart version as prefix to image tags (e.g. 0.8-abc123)
- Fix requires-python metadata to specify that Python 3.6 is required

## 0.2

### 0.2.2

- Another ruamel.yaml type fix

### 0.2.1

- Add `--image-prefix` option
- Workaround ruamel.yaml bug when strings are all-digits
  and start with 0 and contain an 8 or 9.
- Fix type checking for recent ruamel.yaml

### 0.2.0

- Fix image tagging when building multiple images
- Make image-building optional
- Show changes being made
- Support GITHUB_TOKEN env for pushing to gh-pages
- Include chartpress.yaml when resolving last changed ref
- Update only necessary fields

## 0.1

### 0.1.1

- Add missing dependency on ruamel.yaml

### 0.1.0

first release!
