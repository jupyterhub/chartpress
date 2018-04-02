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

## Usage

In a directory containing a `chartpress.yaml`, run:

    chartpress

to build your chart(s) and image(s). Add `--push` to publish images to docker hub and `--publish-chart` to publish the chart and index to gh-pages.

```
usage: chartpress [-h] [--commit-range COMMIT_RANGE] [--push]
                  [--publish-chart] [--tag TAG]
                  [--extra-message EXTRA_MESSAGE]

Automate building and publishing helm charts and associated images. This is
used as part of the JupyterHub and Binder projects.

optional arguments:
  -h, --help            show this help message and exit
  --commit-range COMMIT_RANGE
                        Range of commits to consider when building images
  --push                push built images to docker hub
  --publish-chart       publish updated chart to gh-pages
  --tag TAG             Use this tag for images & charts
  --extra-message EXTRA_MESSAGE
                        extra message to add to the commit message when
                        publishing charts
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
