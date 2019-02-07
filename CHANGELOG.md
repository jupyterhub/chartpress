# Changelog for chartpress

## 0.3

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
