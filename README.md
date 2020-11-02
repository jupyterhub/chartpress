# [chartpress](https://github.com/jupyterhub/chartpress)

[![Latest PyPI version](https://img.shields.io/pypi/v/chartpress?logo=pypi)](https://pypi.python.org/pypi/chartpress)
[![TravisCI build status](https://img.shields.io/travis/com/jupyterhub/chartpress?logo=travis)](https://travis-ci.com/jupyterhub/chartpress)
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

1. `tag`: The latest commit that is tagged on the current branch, or 0.0.1 if no
   tag was found.
2. The latest commit that influenced anything on a path within the git
   repository that matters to the chart version or image tag. The paths that
   matters is determined using the image build contexts and additional specified
   paths.
   1. `n`: The latest commits commit distance count since the tag, described as
      3 or more numbers, prefixed with n.
   2. `h`: The latest commits abbreviated SHA hash, which is typically 7
      characters, prefixed with h.
3. If `--long` is specified or not. When it is specified tagged commits will be
   written out with `n000.h<hash>` appended to it.
4. If `tag` contains a `-`, `tag.n.h` will be used, and if not, `tag-n.h` will
   be used. There should be exactly one `-` in the final version specification
   to become a valid SemVer2 version.

### Examples chart versions and image tags

This is a list of realistic chart versions and/or image tags in a chronological
order that could come from using chartpress.

```
0.8.0
0.8.0-n004.hasdf123
0.8.0-n010.hsdfg234
0.9.0-beta.1
0.9.0-beta.1.n001.hdfgh345
0.9.0-beta.1.n005.hfghj456
0.9.0-beta.2
0.9.0-beta.2.n001.hghjk567
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

```
usage: chartpress [-h] [--push] [--force-push] [--publish-chart]
                  [--extra-message EXTRA_MESSAGE] [--tag TAG | --long]
                  [--image-prefix IMAGE_PREFIX] [--reset]
                  [--skip-build | --force-build] [--version]
                  [--commit-range COMMIT_RANGE]

Automate building and publishing helm charts and associated images. This is
used as part of the JupyterHub and Binder projects.

optional arguments:
  -h, --help            show this help message and exit
  --push                Push built images to their image registries, but not
                        if it would replace an existing image.
  --force-push          Push built images to their image registries,
                        regardless if it would replace an existing image.
  --publish-chart       Package a Helm chart and publish it to a Helm chart
                        repository contructed with a GitHub git repository and
                        GitHub pages.
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
  --skip-build          Skip the image build step.
  --force-build         Enforce the image build step, regardless of if the
                        image already is available either locally or remotely.
  --version             Print current chartpress version and exit.
  --commit-range COMMIT_RANGE
                        Deprecated: this flag will be ignored. The new logic
                        to determine if an image needs to be rebuilt does not
                        require this. It will find the time in git history
                        where the image was last in need of a rebuild due to
                        changes, and check if that build exists locally or
                        remotely already.
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
    resetVersion: 1.2.3
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
```

## Caveats

### TravisCI mirror image registry

If you run chartpress on TravisCI, its logic can be fooled by a mirror image
registry to rebuild something that didn't need rebuilding. A workaround for this
can be found in this repo's [.travis.yml](.travis.yml).

### Shallow clones

Chartpress detects the latest commit which changed a directory or file when
determining the version and tag to use for charts and images. This means that
shallow clones should not be used because if the last commit that changed a
relevant file is outside the shallow commit range, the wrong tag will be
assigned.

TravisCI uses a clone depth of 50 by default, which can result in incorrect
image tagging. You can [disable this shallow clone
behavior](https://docs.travis-ci.com/user/customizing-the-build/#Git-Clone-Depth)
in your `.travis.yml`:

```yaml
git:
  depth: false
```

## Development

Testing of this python package can be done using
[`pytest`](https://github.com/pytest-dev/pytest). For more details on the
testing, see [tests/README.md](tests/README.md).

```bash
# install chartpress locally
pip install  -e .

# install dev dependencies
pip install -r dev-requirements.txt

# run tests
pytest --verbose --flake8 --exitfirst
```
