# Configuration

A `chartpress.yaml` file contains a specification of charts and images to build
for each chart. Below is an example `chartpress.yaml` file.

```yaml
charts:
  # list of charts by name
  # each name should be the name of a Helm chart
  - name: binderhub
    # Directory containing the chart, relative to chartpress.yaml.
    # Can be omitted if the directory is the same as the chart name.
    chartPath: helm-charts/binderhub

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
    # Recommended together with a version-bumping tool like `tbump`.
    # if baseVersion is not a prerelease version (no -suffix),
    # the suffix `-0.dev` will be appended.
    #
    # Alternatively baseVersion can be set to "major", "minor", or "patch", then
    # baseVersion will be calculated based on the latest version tag from `git
    # describe`, but have its "major", "minor", or "patch" version increment if
    # the version isn't a pre-release.
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

## Controlling development versions

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
   We recommend using a version bumping tool like [tbump][] to keep your baseVersion config and git tags in sync.

[tbump]: https://github.com/your-tools/tbump

A release process would generally look like this:

```bash
V=1.2.3
# tbump updates version, commits changes, tags commit, pushes branch and tag
tbump "$V"

# back to development
NEXT_V=1.2.4-0.dev
# bump version config, but no tag for starting development
tbump --no-tag "${NEXT_V}"
```

Any prerelease fields (such as `-0.dev` above, or `-alpha.1`)
will be left as-is, with the `.git.n.hash` suffix added.
If there is no prerelease (e.g. on the exact commit of a tagged release),
`-0.dev` will be added to the base version.
You **must** update baseVersion after making a release,
or `chartpress --reset` will fail due to incorrect ordering of versions.

A sample tbump config file can be found in [our tests](./tests/test_helm_chart/tbump.toml).

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
