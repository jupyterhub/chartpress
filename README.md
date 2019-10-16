# chartpress

Automate building and publishing helm charts and associated images.

This is used as part of the JupyterHub and Binder projects.

Chartpress will:

- build docker images and tag them with the latest git commit
- publish those images to DockerHub
- rerender a chart to include the tagged images
- publish the chart and index to gh-pages

A `chartpress.yaml` file contains a specification of charts and images to build.

For example:

```yaml
charts:
  # list of charts by name
  # each name should be a directory containing a helm chart
  - name: binderhub
    # the prefix to use for built images
    imagePrefix: jupyterhub/k8s-
    # tag to use when resetting the chart values
    # with --reset command-line option (defaults to "set-by-chartpress")
    resetTag: latest
    # the git repo whose gh-pages contains the charts
    repo:
      git: jupyterhub/helm-chart
      published: https://jupyterhub.github.io/helm-chart
    # additional paths (if any) relevant to the chart version
    # outside the chart directory itself
    paths:
      - ../setup.py
      - ../binderhub
    # images to build for this chart (optional)
    images:
      binderhub:
        # Template docker build arguments to be passed using docker's
        # --build-arg flag as --build-arg <key>=<value>. Available dynamic
        # values are TAG and LAST_COMMIT.
        buildArgs:
          MY_STATIC_BUILD_ARG: "hello world"
          MY_DYNAMIC_BUILD_ARG: "{TAG}-{LAST_COMMIT}"
        # Context to send to docker build for use by the Dockerfile
        # (if different from the current directory)
        contextPath: ..
        # Dockerfile path, if different from the default
        # (may be needed if contextPath is set)
        dockerfilePath: images/binderhub/Dockerfile
        # path in values.yaml to be updated with image name and tag
        valuesPath: image
        # additional paths (if any) relevant to the image
        # outside the image directory itself
        paths:
          - ../setup.py
          - ../binderhub
```

## Requirements

The following binaries must be in your `PATH`:
- git
- helm

If you are publishing a chart to GitHub Pages create a `gh-pages` branch in the destination repository.

## Usage

In a directory containing a `chartpress.yaml`, run:

    chartpress

to build your chart(s) and image(s). Add `--push` to publish images to docker hub and `--publish-chart` to publish the chart and index to gh-pages.

```
usage: chartpress [-h] [--commit-range COMMIT_RANGE] [--push]
                  [--publish-chart] [--tag TAG]
                  [--extra-message EXTRA_MESSAGE]
                  [--image-prefix IMAGE_PREFIX] [--reset] [--skip-build]

Automate building and publishing helm charts and associated images. This is
used as part of the JupyterHub and Binder projects.

optional arguments:
  -h, --help            show this help message and exit
  --commit-range COMMIT_RANGE
                        Range of commits to consider when building images
  --push                Push built images to docker hub
  --publish-chart       Publish updated chart to gh-pages
  --tag TAG             Use this tag for images & charts
  --extra-message EXTRA_MESSAGE
                        Extra message to add to the commit message when
                        publishing charts
  --image-prefix IMAGE_PREFIX
                        Override image prefix with this value
  --reset               Reset image tags
  --skip-build          Skip image build, only render the charts
  --version             Print current chartpress version
```

### Caveats

#### Shallow clones

Chartpress detects the latest commit which changed a directory or file when determining the tag to use for charts and images.
This means that shallow clones should not be used because if the last commit that changed a relevant file is outside the shallow commit range, the wrong tag will be assigned.

Travis uses a clone depth of 50 by default, which can result in incorrect image tagging.
You can [disable this shallow clone behavior](https://docs.travis-ci.com/user/customizing-the-build/#Git-Clone-Depth) in your `.travis.yml`:

```yaml
git:
  depth: false
```
