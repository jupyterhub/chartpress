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

## Command caching

Chartpress caches the results of some commands to improve performance.
This means chartpress should not be used as an importable library.
