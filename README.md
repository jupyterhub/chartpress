# [chartpress](https://github.com/jupyterhub/chartpress)

[![Latest PyPI version](https://img.shields.io/pypi/v/chartpress?logo=pypi)](https://pypi.python.org/pypi/chartpress)
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/jupyterhub/chartpress/Test?logo=github)](https://github.com/jupyterhub/chartpress/actions)
[![GitHub](https://img.shields.io/badge/issue_tracking-github-blue?logo=github)](https://github.com/jupyterhub/chartpress/issues)
[![Discourse](https://img.shields.io/badge/help_forum-discourse-blue?logo=discourse)](https://discourse.jupyter.org/c/jupyterhub)
[![Gitter](https://img.shields.io/badge/social_chat-gitter-blue?logo=gitter)](https://gitter.im/jupyterhub/jupyterhub)

Chartpress automate basic Helm chart development work. It is tightly used in development of the [JupyterHub](https://github.com/jupyterhub/zero-to-jupyterhub-k8s) and [BinderHub](https://github.com/jupyterhub/binderhub) Helm charts.

## Features

Chartpress can do the following with the help of some configuration.

- Update Chart.yaml's version appropriately
- Build docker images and tag them appropriately
- Push built images to a docker image repository
- Update values.yaml to reference the built images
- Publish a chart to a Helm chart registry based on GitHub pages
- Reset changes to Chart.yaml and values.yaml

## How chart version and image tags are determined

Chartpress will infer chart versions and image tags using a few key pieces of
information.

1. `tag`: If not directly set by `--tag`, it will be inferred from most recent
   commit that is tagged in the _current branch_
   (as determined by `git describe`)
   or be set to 0.0.1 if no commit is tagged.
   1. If the `tag` has a leading `v` but is otherwise a valid
      [SemVer2](https://semver.org) version, the `v` will be stripped from Chart.yaml
      before its set as Helm 3 requires Helm chart versions to be SemVer2
      compliant.
1. The latest commit modifying content in a _relevant path_ since `tag`.
   1. `n`: The number of commits since the latest tagged commit on the branch, as an integer.
   1. `hash`: The latest commit's abbreviated hash, which is often 7-8 characters,
      prefixed with `h`.
1. If `tag` (like `0.10.0` or `0.10.0-beta.1`) contains a `-`, a `tag.git.n.hash`
   format will be used, and otherwise a `tag-0.dev.git.n.hash` format will be used.
1. If `--long` is specified or not. If `--long` is specified, tagged commits
   will always be written out with the `.git.n.hash` part appended to it, looking something
   like `1.0.0-0.dev.git.0.habcd123`

When producing a development version (with `.git.n.hash` on the end),
The _base_ version can come from one of two places,
depending on your configuration.
See [Controlling development version](#controlling-development-versions-in-chart.yaml) for more info.

### Examples chart versions and image tags

This is a list of realistic chart versions and/or image tags in a chronological
order that could come from using chartpress.

```
0.8.0
0.8.0-0.dev.git.4.hasdf123
0.8.0-0.dev.git.10.hsdfg234
0.9.0-beta.1
0.9.0-beta.1.git.12.hdfgh345
0.9.0-beta.1.git.15.hfghj456
0.9.0-beta.2
0.9.0-beta.2.git.20.hghjk567
0.9.0-beta.3
0.9.0
```

## Requirements

The following binaries must be in your `PATH`:

- [git](https://www.git-scm.com/downloads)
- [docker](https://docs.docker.com/install/#supported-platforms)
- [helm](https://helm.sh/docs/using_helm/#installing-helm)

If you are publishing a chart to GitHub Pages create a `gh-pages` branch in the
destination repository.

## Installation

```
pip install chartpress
```

## Usage

In a directory containing a `chartpress.yaml`, run:

    chartpress

to build your chart(s) and image(s). Add `--push` to publish images to docker
hub and `--publish-chart` to publish the chart and index to gh-pages.

<!--
To update this help output run
COLUMNS=80 chartpress --help
-->

```
usage: chartpress [-h] [--push] [--force-push] [--publish-chart]
                  [--force-publish-chart] [--extra-message EXTRA_MESSAGE]
                  [--tag TAG | --long] [--image-prefix IMAGE_PREFIX] [--reset]
                  [--no-build | --force-build]
                  [--builder {docker-build,docker-buildx}]
                  [--platform PLATFORM] [--list-images] [--version]

Automate building and publishing helm charts and associated images. This is
used as part of the JupyterHub and Binder projects.

optional arguments:
  -h, --help            show this help message and exit
  --push                Push built images to their image registries, but not
                        if it would replace an existing image.
  --force-push          Push built images to their image registries,
                        regardless if it would replace an existing image.
  --publish-chart       Package a Helm chart and publish it to a Helm chart
                        registry constructed with a GitHub git repository and
                        GitHub pages, but not if it would replace an existing
                        chart version.
  --force-publish-chart
                        Package a Helm chart and publish it to a Helm chart
                        registry constructed with a GitHub git repository and
                        GitHub pages, regardless if it would replace an
                        existing chart version
  --extra-message EXTRA_MESSAGE
                        Extra message to add to the commit message when
                        publishing charts.
  --tag TAG             Explicitly set the image tags and chart version.
  --long                Use this to always get a build suffix for the
                        generated tag and chart version, even when the
                        specific commit has a tag.
  --image-prefix IMAGE_PREFIX
                        Override the configured image prefix with this value.
  --reset               Skip image build step and reset Chart.yaml's version
                        field and values.yaml's image tags. What it resets to
                        can be configured in chartpress.yaml with the resetTag
                        and resetVersion configurations.
  --no-build, --skip-build
                        Skip the image build step.
  --force-build         Enforce the image build step, regardless of if the
                        image already is available either locally or remotely.
  --builder {docker-build,docker-buildx}
                        Container build engine to use, docker-build is the
                        standard Docker build command.
  --platform PLATFORM   Build the image for this platform, e.g. linux/amd64 or
                        linux/arm64. This argument can be used multiple times
                        to build multiple platforms under the same tag. Only
                        supported for docker buildx. If --push is set or if
                        multiple platforms are passed the image will not be
                        loaded into the local docker engine.
  --list-images         print list of images to stdout. Images will not be
                        built.
  --version             show program's version number and exit
```

## Configuration

A `chartpress.yaml` file contains a specification of charts and images to build
for each chart. Below is an example `chartpress.yaml` file.

```yaml
charts:
  # list of charts by name
  # each name should be a directory containing a helm chart
  - name: binderhub
    # the prefix to use for built images
    imagePrefix: jupyterhub/k8s-
    # tag to use when resetting the chart values
    # with the --reset flag. It defaults to "set-by-chartpress".
    resetTag: latest
    # version to use when resetting the Chart.yaml's version field with the
    # --reset flag. It defaults to "0.0.1-set.by.chartpress". This is a valid
    # SemVer 2 version, which is required for a helm lint command to succeed.
    resetVersion: 1.2.3-dev

    # baseVersion sets the base version for development tags,
    # instead of using the latest tag from `git describe`.
    # This gives you more control over development version tags
    # and lets you ensure prerelease tags are always sorted in the right order.
    # Only useful when publishing development releases.
    baseVersion: 3.2.1-0.dev

    # The git repo whose gh-pages contains the charts. This can be a local
    # path such as "." as well but if matching <organization>/<repo> will be
    # assumed to be a separate GitHub repository.
    repo:
      git: jupyterhub/helm-chart
      published: https://jupyterhub.github.io/helm-chart
    # Additional paths that when modified should lead to an updated Chart.yaml
    # version, other than the chart directory in <chart name> or any path that
    # influence the images of the chart. These paths should be set relative to
    # chartpress.yaml's directory.
    paths:
      - ../setup.py
      - ../binderhub
    # images to build for this chart (optional)
    images:
      binderhub:
        # imageName overrides the default name of the image. The default name
        # is the imagePrefix augmented with the key of this configuration. It
        # would be jupyterhub/k8s-binderhub in this case.
        imageName: jupyterhub/k8s-custom-image-name
        # Build arguments to be passed using docker's --build-arg flag as
        # --build-arg <key>=<value>. TAG and LAST_COMMIT are expandable.
        buildArgs:
          MY_STATIC_BUILD_ARG: "hello world"
          MY_DYNAMIC_BUILD_ARG: "{TAG}-{LAST_COMMIT}"
        # Build options to be passed to the docker build command. Pass a list
        # of strings to be appended to the end of the build command. These are
        # passed directly to the command line, so prepend each option with "--"
        # like in the examples below. TAG and LAST_COMMIT are expandable.
        extraBuildCommandOptions:
          - --label=maintainer=octocat
          - --label=ref={TAG}-{LAST_COMMIT}
          - --rm
        # contextPath is the path to the directory that is to be considered the
        # current working directory during the build process of the Dockerfile.
        # This is by default the folder of the Dockerfile. This path should be
        # set relative to chartpress.yaml.
        contextPath: ..
        # By default, changes to the contextPath will make chartpress rebuild
        # the image, but this option make that configurable.
        rebuildOnContextPathChanges: false
        # Path to the Dockerfile, relative to chartpress.yaml. Defaults to
        # "images/<image name>/Dockerfile".
        dockerfilePath: images/binderhub/Dockerfile
        # Path(s) in <chart name>/values.yaml to be updated with image name and
        # tag.
        valuesPath:
          - singleuser.image
          - singleuser.profileList.0.kubespawner_override.image
        # Additional paths, relative to chartpress.yaml's directory, that should
        # be used to indicate that a new tag of the image is required, aside
        # from the contextPath and dockerfilePath for building the image itself.
        paths:
          - assets
        # If chartpress is used to build images for multiple architectures but
        # not all of those architectures are supported by an image they can be
        # skipped
        skipPlatforms:
          - linux/arm64
```

### Controlling development versions

Like some "package version in version control" tools,
you don't need to manage versions at all in chartpress except by tagging commits.

However, relying only on tags results in "development versions" (versions published from commits after a release)
having somewhat confusing prerelease versions.

After publishing e.g. `1.2.3`, the next version will be `1.2.3-0.dev.git.10.habc`.
According to Semantic Versioning,
this is a "pre release" (good, it should be excluded from default installation),
but it means it comes _before_ 1.2.3 (wrong! it's 1 commit _newer_ than 1.2.3).
This is because prereleases should be defined relative to the _next_ release,
not the _last_ release. But git tags only store the _last_ release!

Chartpress 2.0 adds an option `chart.baseVersion`,
which allows setting the base version of development tags explicitly,
instead of using the version of the last tag found via `git describe`.

The main benefits of this are:

1. ensuring that published prerelease versions show up in the right order, and
2. giving you control over the version of a prerelease chart (is it 2.0.0-0.dev or 1.3.1-0.dev?)

Instead of publishing the sequence:

- 1.2.3
- 1.2.3-0.dev.git.10.habc (later than 1.2.3, but sorts _before_ 1.2.3!)

You can publish

- 1.2.3
- 1.3.0-0.dev.git.10.habc (prerelease based on the _next_ version, not _last_)

where chartpress will use the version in your `baseVersion` config as the base version,
instead of the last tag on the branch.

This takes some extra configuration, and steps in your release process:

1. You must set `baseVersion: 1.2.3-0.dev` in your chartpress.yaml to your _next_ prerelease:

   ```yaml
   charts:
     - name: mychart
       baseVersion: 1.2.3-0.dev
   ```

2. You must update baseVersion, especially after making a release.

A release process would generally look like this:

```bash
V=1.2.3
git tag -am "release $V" "$V"
git push --atomic --follow-tags

# back to development
NEXT_V=1.2.4-0.dev
# edit chartpress.yaml to set baseVersion: $NEXT_V
git add chartpress.yaml
git commit -m "Back to $NEXT_V"
git push --atomic
```

Any prerelease fields (such as `-0.dev` above, or `-alpha.1`)
will be left as-is, with the `.git.n.hash` suffix added.

## Caveats

### Shallow clones

Chartpress detects the latest commit that changed a directory or file when
determining the version and tag to use for charts and images. This means that
shallow clones should not be used because if the last commit that changed a
relevant file is outside the shallow commit range, the wrong chart version and
image tag will be assigned.

#### Avoiding shallow clones with GitHub Actions

GitHub Workflow's commonly used GitHub Action called actions/checkout have a
clone clone-depth of 1 by default, configure it to make a full clone instead.

```yaml
steps:
  - uses: actions/checkout@v2
    with:
      # chartpress need the git branch's tags and commits
      fetch-depth: 0
```

### Command caching

Chartpress caches the results of some commands to improve performance.
This means chartpress should not be used as an importable library.

## Development

Testing of this python package can be done using
[`pytest`](https://github.com/pytest-dev/pytest). For more details on the
testing, see [tests/README.md](tests/README.md).

```bash
# install chartpress locally
pip install  -e .

# install dev dependencies
pip install -r dev-requirements.txt

# format and lint code
pre-commit run -a

# run tests
pytest --verbose --exitfirst
# some tests push to a local registry, you can skip these
pytest --verbose --exitfirst -m 'not registry'
```
