#!/usr/bin/env python3
"""
Automate building and publishing helm charts and associated images.

This is used as part of the JupyterHub and Binder projects.
"""
import argparse
import os
import pipes
import re
import shlex
import shutil
import subprocess
import sys
from collections.abc import MutableMapping
from enum import Enum
from functools import lru_cache, partial
from tempfile import TemporaryDirectory

import docker
from ruamel.yaml import YAML

__version__ = "2.1.0"

# name of the environment variable with GitHub token
GITHUB_TOKEN_KEY = "GITHUB_TOKEN"
GITHUB_ACTOR_KEY = "GITHUB_ACTOR"

# name of possible repository keys used in image value
IMAGE_REPOSITORY_KEYS = {"name", "repository"}

# prefixes added to prerelease versions
# these do not include the trailing '.'
# which makes them valid prerelease fields on their own,
# but they cannot be empty.

# GIT is always added to start our git info
GIT_PREFIX = "git"
# this is the _full_ prefix we add to non-prerelease versions
PRERELEASE_PREFIX = f"0.dev.{GIT_PREFIX}"

# Container builders
class Builder(Enum):
    DOCKER_BUILD = "docker-build"
    DOCKER_BUILDX = "docker-buildx"

    def __str__(self):
        return self.value


# use safe roundtrip yaml loader capable or preserving usage of no/single/double
# quotes for a string for example
yaml = YAML(typ="rt")
yaml.preserve_quotes = True
yaml.indent(mapping=2, offset=2, sequence=4)


def _log(message):
    """Print messages to stderr

    to avoid conflicts with piped output, e.g. `--list-images`
    """
    print(message, file=sys.stderr)


def _run_cmd(call, cmd, *, echo=True, **kwargs):
    """Run a command and echo it first with censoring of GITHUB_TOKEN."""
    if echo:
        cmd_string = " ".join(map(pipes.quote, cmd))
        github_token = os.getenv(GITHUB_TOKEN_KEY)
        if github_token:
            cmd_string = cmd_string.replace(github_token, "CENSORED_GITHUB_TOKEN")
        _log("$> " + cmd_string)
    return call(cmd, **kwargs)


def _check_call(cmd, **kwargs):
    kwargs.setdefault("stdout", sys.stderr.fileno())
    return _run_cmd(subprocess.check_call, cmd, **kwargs)


_check_output = partial(_run_cmd, subprocess.check_output)


_semver2 = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


def _fix_chart_version(version, strict=False):
    """
    Helm 3 requires published chart versions to follow strict semantic versioning.

    Fix the version if it can be fixed (strip leading `v`),
    or warn about the chart being unpublishable (default).

    Use `strict=True` if a chart is to be published,
    since helm 3 will not install a chart with a version that doesn't pass this check.

    This validation is not relevant for charts not being published to a repository.
    """
    # semver.org provided this regular expression:
    # https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string

    if _semver2.fullmatch(version):
        return version

    if version.startswith("v") and _semver2.fullmatch(version[1:]):
        return version[1:]

    message = f"The version in Chart.yaml '{version}' doesn't follow semantic versioning. Helm 3 requires published charts to have strict semantic versions."
    if strict:
        raise ValueError(message)
    else:
        _log(message)
        return version


def _get_git_remote_url(git_repo):
    """Return the URL for remote git repository.

    Depending on the system setup it returns ssh or https remote.
    """
    # if not matching something/something
    # such as a local directory ".", then
    # simply return this unmodified.
    if not re.match(r"^[^/]+/[^/]+$", git_repo):
        return git_repo

    github_actor = os.getenv(GITHUB_ACTOR_KEY)
    github_token = os.getenv(GITHUB_TOKEN_KEY)
    if github_actor and github_token:
        # this format works for a token created for a github
        # workflow's job, no matter what we pass as github_actor.
        return f"https://{github_actor}:{github_token}@github.com/{git_repo}"
    elif github_token:
        # this format works for personal access token, but
        # not for a token created for a github workflow's job.
        return f"https://{github_token}@github.com/{git_repo}"
    return f"git@github.com:{git_repo}"


def _get_latest_commit_modifying_path(*paths, **kwargs):
    """Get the latest commit modifying the given path or return None."""
    return (
        _check_output(
            [
                "git",
                "log",
                "--max-count=1",
                "--pretty=format:%h",
                "--",
                *paths,
            ],
            **kwargs,
        )
        .decode("utf-8")
        .strip()
    )


@lru_cache()
def _count_commits(ref):
    """Return the number of commits for a given ref (branch, commit, etc.)"""
    return int(
        _check_output(
            ["git", "rev-list", "--count", ref],
            echo=False,
        )
        .decode("utf-8")
        .strip()
    )


def _get_latest_tag(**kwargs):
    """Get the latest tag on a commit in branch or return None."""
    return _get_latest_tag_and_count(**kwargs)[0]


@lru_cache()
def _get_latest_tag_and_count(ref="HEAD", **kwargs):
    """Get the latest tag on a commit in branch and the number of commits since then.

    If no tag is found, return (None, total number of commits in the branch).
    """
    kwargs.setdefault("echo", False)  # because we handle errors
    try:
        # If the git command output is my-tag-14-g0aed65e,
        # then the return value will become my-tag.
        git_describe = (
            _check_output(
                ["git", "describe", "--tags", "--long", ref],
                stderr=subprocess.DEVNULL,  # because we handle errors
                **kwargs,
            )
            .decode("utf-8")
            .strip()
        )
        latest_tag_in_branch, n_commits_since_tag, _g_sha = git_describe.rsplit(
            "-", maxsplit=2
        )
        return latest_tag_in_branch, int(n_commits_since_tag)
    except subprocess.CalledProcessError:
        # no tag found, count all commits
        return None, _count_commits(ref)


def _get_commit_from_tag(tag, **kwargs):
    """Return the abbreviated commit hash for the tag."""
    return (
        _check_output(
            [
                "git",
                "rev-list",
                "--abbrev-commit",
                "-n",
                "1",
                tag,
            ],
            **kwargs,
        )
        .decode("utf-8")
        .strip()
    )


@lru_cache()
def _get_latest_commit_tagged_or_modifying_paths(*paths, **kwargs):
    """
    Get the latest of a) the latest tagged commit, or b) the latest commit
    modifying any file in the the provided paths.
    """
    latest_commit_modifying_path = _get_latest_commit_modifying_path(*paths, **kwargs)

    latest_tag = _get_latest_tag(**kwargs)
    if not latest_tag:
        return latest_commit_modifying_path
    latest_commit_tagged = _get_commit_from_tag(latest_tag, **kwargs)

    # Is one commit is or isn't the ancestor of the other we can figure out what
    # commit is the latest.
    try:
        _check_call(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                latest_commit_tagged,
                latest_commit_modifying_path,
            ],
            **kwargs,
        )
    except subprocess.CalledProcessError:
        return latest_commit_tagged
    else:
        return latest_commit_modifying_path


def _get_image_build_args(image_options, ns):
    """
    Render buildArgs from chartpress.yaml that could be templates, using
    provided namespace that contains keys with dynamic values such as
    LAST_COMMIT or TAG.

    Args:
    image_options (dict):
        The dictionary for a given image from chartpress.yaml.
        Fields in `image_options['buildArgs']` will be rendered
        and returned, if defined.
    ns (dict): the namespace used when rendering templated arguments
    """
    build_args = image_options.get("buildArgs", {})
    for key, value in build_args.items():
        build_args[key] = value.format(**ns)
    return build_args


def _get_image_extra_build_command_options(image_options, ns):
    """
    Render extraBuildCommandOptions from chartpress.yaml that could be
    templates, using the provided namespace that contains keys with dynamic
    values such as LAST_COMMIT or TAG.

    Args:
    image_options (dict):
        The dictionary for a given image from chartpress.yaml.
        Strings in `image_options['extraBuildCommandOptions']` will be rendered
        and returned.
    ns (dict): the namespace used when rendering templated arguments
    """
    options = image_options.get("extraBuildCommandOptions", [])
    return [str(option).format(**ns) for option in options]


def _get_image_build_context_path(name, options):
    """
    Return the image's contextPath configuration value, or a default value based
    on the image name.
    """
    if options.get("contextPath"):
        return options["contextPath"]
    else:
        return os.path.join("images", name)


def _get_image_dockerfile_path(name, options):
    """
    Return the image dockerfilePath configuration value or a default value based
    on the contextPath.
    """
    if options.get("dockerfilePath"):
        return options["dockerfilePath"]
    else:
        return os.path.join(_get_image_build_context_path(name, options), "Dockerfile")


def _get_all_image_paths(name, options):
    """
    Returns the unique paths that when changed should trigger a rebuild of a
    chart's image. This includes the Dockerfile itself and the context of the
    Dockerfile during the build process.

    The first element will always be the context path, the second always the
    Dockerfile path, and the optional others for extra paths.
    """
    paths = []
    paths.append("chartpress.yaml")
    if options.get("rebuildOnContextPathChanges", True):
        paths.append(_get_image_build_context_path(name, options))
    paths.append(_get_image_dockerfile_path(name, options))
    paths.extend(options.get("paths", []))
    return list(set(paths))


def _get_all_chart_paths(options):
    """
    Returns the unique paths that when changed should trigger a version update
    of the chart. These paths includes all the chart's images' paths as well.
    """
    paths = []
    paths.append("chartpress.yaml")
    paths.append(options["name"])
    paths.extend(options.get("paths", []))
    if "images" in options:
        for image_name, image_config in options["images"].items():
            paths.extend(_get_all_image_paths(image_name, image_config))
    return list(set(paths))


def build_image(
    image_spec,
    context_path,
    dockerfile_path=None,
    build_args=None,
    extra_build_command_options=None,
    *,
    push=False,
    builder=Builder.DOCKER_BUILD,
    platforms=None,
):
    """Build an image

    Args:
    image_spec (str):
        The image name, including tag, and optionally a registry prefix for
        other image registries than DockerHub.

        Examples:
        - jupyterhub/k8s-hub:0.9.0
        - index.docker.io/library/ubuntu:latest
        - eu.gcr.io/my-gcp-project/my-image:0.1.0
    context_path (str):
        The path to the directory that is to be considered the current working
        directory during the build process of the Dockerfile. This is typically
        the same folder as the Dockerfile resides in.
    dockerfile_path (str, optional):
        Path to Dockerfile relative to chartpress.yaml's directory if not
        "<context_path>/Dockerfile".
    build_args (dict, optional):
        Dictionary of docker build arguments.
    extra_build_command_options (list, optional):
        List of other docker build options to use. Each item should be a string
        that gets appended to the build command (e.g. "--label=version=0.1.0").
    push (bool, optional):
        Whether to push the image to a registry
    builder (str):
        The container build engine.
    platforms (iterable[str], optional):
        List of platforms to build for
    """
    if builder == Builder.DOCKER_BUILD:
        cmd = ["docker", "build"]
    elif builder == Builder.DOCKER_BUILDX:
        # plain shows the container output, similar to docker build
        cmd = ["docker", "buildx", "build", "--progress", "plain"]
    else:
        raise ValueError(f"Unknown builder: {builder}")

    if not platforms:
        platforms = []

    cmd.extend(["-t", image_spec, context_path])
    if dockerfile_path:
        cmd.extend(["-f", dockerfile_path])
    for k, v in (build_args or {}).items():
        cmd += ["--build-arg", f"{k}={v}"]
    if platforms:
        # sort platforms to make testing easier
        cmd.extend(["--platform", ",".join(sorted(platforms))])
    if builder == Builder.DOCKER_BUILDX:
        # Limitations of docker buildx 0.5.1:
        # - Can't load into the local Docker host and push to a registry at the
        #   same time
        # - Can't load multiple platforms into the local docker host
        if push:
            cmd.append("--push")
        elif len(platforms) <= 1:
            cmd.append("--load")
    if extra_build_command_options:
        cmd.extend(extra_build_command_options)
    _check_call(cmd)

    if builder == Builder.DOCKER_BUILD and push:
        _check_call(["docker", "push", image_spec])


@lru_cache()
def _get_docker_client():
    """Cached getter for docker client"""
    return docker.from_env()


@lru_cache()
def _image_needs_pushing(image, platforms):
    """
    Returns a boolean whether an image needs pushing by checking if the image
    exists on the image registry.

    Args:

    image (str):
        The name of an image to be passed to the docker push command.

        Examples:
        - jupyterhub/k8s-hub:0.9.0
        - index.docker.io/library/ubuntu:latest
        - eu.gcr.io/my-gcp-project/my-image:0.1.0
    platforms (frozenset[str]):
        Set of platforms to build for
    """
    d = _get_docker_client()
    try:
        data = d.images.get_registry_data(image)
        if platforms:
            for platform in platforms:
                if not data.has_platform(platform):
                    return True
    except docker.errors.APIError:
        # image not found on registry, needs pushing
        return True
    else:
        return False


@lru_cache()
def _image_needs_building(image, platforms):
    """
    Returns a boolean whether an image needs building by checking if the image
    exists either locally or on the registry.

    Args:

    image (str):
        The name of an image to be passed to the docker build command.

        Examples:
        - jupyterhub/k8s-hub:0.9.0
        - index.docker.io/library/ubuntu:latest
        - eu.gcr.io/my-gcp-project/my-image:0.1.0
    platforms (frozenset[str]):
        Set of platforms to build for
    """
    # Since docker buildx builds for multiple platforms we can't tell whether the
    # image already exists in the host so just check remote registry
    if platforms:
        return _image_needs_pushing(image, platforms)

    d = _get_docker_client()

    # first, check for locally built image
    try:
        d.images.get(image)
    except docker.errors.ImageNotFound:
        # image not found, check registry
        pass
    else:
        # it exists locally, no need to check remote
        return False

    # image may need building if it's not on the registry
    return _image_needs_pushing(image, platforms)


def _get_identifier_from_paths(*paths, long=False, base_version=None):
    latest_commit = _get_latest_commit_tagged_or_modifying_paths(*paths, echo=False)

    # always use monotonic counter since the beginning of the branch
    # avoids counter resets when using explicit base_version
    n_commits = _count_commits(latest_commit)

    latest_tag_in_branch, n_commits_since_tag = _get_latest_tag_and_count(latest_commit)
    if latest_tag_in_branch:
        if n_commits_since_tag == 0:
            # don't use baseVersion config for development versions
            # when we are exactly on a tag
            base_version = latest_tag_in_branch
            if not long:
                # set n_commits=0 to ensure exact tag is used without suffix
                # in _get_identifier_from_parts
                n_commits = 0

        if base_version is None:
            base_version = latest_tag_in_branch

    if base_version is None:
        base_version = "0.0.1-0.dev"

    return _get_identifier_from_parts(base_version, n_commits, latest_commit, long)


def _get_identifier_from_parts(tag, n_commits, commit, long):
    """
    Returns a chartpress formatted chart version or image tag (identifier) with
    a build suffix.

    This function should provide valid Helm chart versions, which means they
    need to be valid SemVer 2 version strings. It also needs to return valid
    image tags, which means they need to not contain `+` signs either. We prefix
    with h to ensure we don't get a numerical hash starting with 0 because
    those are invalid SemVer 2 versions.

    If tag is already a prelease, we append fields so we sort later than the prerelease.
    If the tag is a stable release, we start the prerelease with `-0.dev.` to ensure we sort lower
    than labeled prereleases such as 'alpha'.

    Typical tags in descending order:

    - 0.1.2
    - 0.1.2-alpha.2
    - 0.1.2-alpha.1.git.5.habc
    - 0.1.2-alpha.1
    - 0.1.2-0.dev.git.3.habc

    Example:
        tag="0.1.2", n_commits="5", commit="asdf1234", long=True,
        should return "0.1.2-0.dev.git.5.hasdf1234".
    """
    n_commits = int(n_commits)

    if n_commits > 0 or long:
        if "-" in tag:
            # add fields to an existing prerelease tag
            # 0.1.2-alpha.1 -> 0.1.2-alpha.1.git.n.hsha
            pre = f".{GIT_PREFIX}"
        else:
            # create a new '-0.dev.' prerelease tag
            # 0.1.2 -> 0.1.2-0.dev.git.5.hsha
            pre = f"-{PRERELEASE_PREFIX}"
        return f"{tag}{pre}.{n_commits}.h{commit}"
    else:
        return f"{tag}"


def build_images(
    prefix,
    images,
    tag=None,
    push=False,
    force_push=False,
    force_build=False,
    skip_build=False,
    long=False,
    *,
    builder=Builder.DOCKER_BUILD,
    platforms=None,
    base_version=None,
):
    """Build a collection of docker images

    Args:
    prefix (str): the prefix to add to image names
    images (dict): dict of image-specs from chartpress.yaml
    tag (str):
        Specific tag to use instead of the last modified commit.
        If unspecified the tag for each image will be the hash of the last commit
        to modify the image's files.
    push (bool):
        Whether to push the resulting images (default: False).
    force_push (bool):
        Whether to push the built images even if they already exist in the image
        registry (default: False).
    force_build (bool):
        To build even if the image is available locally or remotely already.
    skip_build (bool):
        Whether to skip the actual image build (only updates tags).
    long (bool):
        Whether to include the generated tag's build suffix even when the commit
        has a tag. Setting long to true could be useful if you have two build
        pipelines, one for commits and one for tags, and want to avoid
        generating conflicting build artifacts.

        Example 1:
        - long=False: 0.9.0
        - long=True:  0.9.0-0.dev.git.0.hasdf1234

        Example 2:
        - long=False: 0.9.0-0.dev.git.4.hsdfg2345
        - long=True:  0.9.0-0.dev.git.4.hsdfg2345

    builder (str):
        The container build engine.
    platforms (list[str]):
        List of platforms to build for if not the same as the Docker host.
    base_version (str):
        The base version string (before '.git'), used when useChartVersion is True
        instead of the tag found via `git describe`.
    """
    values_file_modifications = {}
    for name, options in images.items():
        # include chartpress.yaml in the image paths to inspect as
        # chartpress.yaml can contain build args influencing the image
        all_image_paths = _get_all_image_paths(name, options)

        if tag is None:
            image_tag = _get_identifier_from_paths(
                *all_image_paths, long=long, base_version=base_version
            )
        else:
            image_tag = tag

        image_name = options.get("imageName", prefix + name)

        # update values_file_modifications to return
        values_path_list = options.get("valuesPath", [])
        if isinstance(values_path_list, str):
            values_path_list = [values_path_list]
        for values_path in values_path_list:
            values_file_modifications[values_path] = {
                "repository": image_name,
                "tag": image_tag,
            }

        if skip_build:
            continue

        image_spec = f"{image_name}:{image_tag}"

        skip_platforms = options.get("skipPlatforms", [])
        if platforms:
            platforms = frozenset(platforms)
        if platforms and skip_platforms:
            platforms = platforms.difference(skip_platforms)
            if not platforms:
                _log(f"Skipping build for {image_spec}, no matching platforms")
                continue

        # build image and optionally push image
        if force_build or _image_needs_building(image_spec, platforms):
            expansion_namespace = {
                "LAST_COMMIT": _get_latest_commit_tagged_or_modifying_paths(
                    *all_image_paths, echo=False
                ),
                "TAG": image_tag,
            }
            build_image(
                image_spec,
                _get_image_build_context_path(name, options),
                dockerfile_path=_get_image_dockerfile_path(name, options),
                build_args=_get_image_build_args(options, expansion_namespace),
                extra_build_command_options=_get_image_extra_build_command_options(
                    options, expansion_namespace
                ),
                push=push or force_push,
                builder=builder,
                platforms=platforms,
            )
        else:
            _log(f"Skipping build for {image_spec}, it already exists")

            # push image
            if push or force_push:
                if force_push or _image_needs_pushing(image_spec, platforms):
                    _check_call(["docker", "push", image_spec])
                else:
                    _log(f"Skipping push for {image_spec}, already on registry")

    return values_file_modifications


def _update_values_file_with_modifications(name, modifications):
    """
    Update <name>/values.yaml file with a dictionary of modifications with its
    root level keys representing a path within the values.yaml file.

    Example of a modifications dictionary:

        {
            "server.image": {
                "repository": "my-docker-org/server",
                "tag": "v1.0.0",
            },
            "server.initContainers.0.image": {
                "repository": "my-docker-org/server-init",
                "tag": "v1.0.0",
            }
        }
    """
    values_file = os.path.join(name, "values.yaml")

    with open(values_file) as f:
        values = yaml.load(f)

    for path_key, path_value in modifications.items():
        if not isinstance(path_value, dict) or set(path_value.keys()) != {
            "repository",
            "tag",
        }:
            raise ValueError(
                f"I only understand image updates with 'repository', 'tag', not: {path_value!r}"
            )

        mod_obj = parent = values
        for p in path_key.split("."):
            if p.isdigit():
                # integers are indices in lists
                p = int(p)
            parent = mod_obj
            mod_obj = mod_obj[p]
            last_part = p

        if isinstance(mod_obj, MutableMapping):
            keys = IMAGE_REPOSITORY_KEYS & mod_obj.keys()
            if keys:
                for repo_key in keys:
                    before = mod_obj.get(repo_key, None)
                    if before != path_value["repository"]:
                        _log(
                            f"Updating {values_file}: {path_key}.{repo_key}: {path_value}"
                        )
                    mod_obj[repo_key] = path_value["repository"]
            else:
                possible_keys = " or ".join(IMAGE_REPOSITORY_KEYS)
                raise KeyError(
                    f"Could not find {possible_keys} in {values_file}:{path_key}"
                )

            before = mod_obj.get("tag", None)
            if before != path_value["tag"]:
                _log(f"Updating {values_file}: {path_key}.tag: {path_value}")
            mod_obj["tag"] = path_value["tag"]
        elif isinstance(mod_obj, str):
            # scalar image string, not dict with separate repository, tag keys
            image = "{repository}:{tag}".format(**path_value)
            try:
                before = parent[last_part]
            except (KeyError, IndexError):
                before = None
            if before != image:
                _log(f"Updating {values_file}: {path_key}: {image}")
            parent[last_part] = image
        else:
            raise TypeError(
                f"{path_key} in {values_file} must be a mapping or string, not {type(mod_obj)}."
            )

    with open(values_file, "w") as f:
        yaml.dump(values, f)


_suffix_version_pat = re.compile(r"(.*)\.git\.\d+\.h[a-f0-9]+$")


def _trim_version_suffix(version):
    """Trim trailing .git... suffix from a version

    Turns 1.0.0-0.dev.git.5.habc back into 1.0.0-0.dev
    """
    m = _suffix_version_pat.match(version)
    if m:
        # matches, strip suffix
        return m.group(1)
    return version


def build_chart(
    name,
    version=None,
    paths=None,
    long=False,
    strict_version=False,
    base_version=None,
):
    """
    Update Chart.yaml's version, using specified version or by constructing one.

    Chart versions are constructed using:
        a) a base version, derived from either Chart.yaml's version field or the latest git tag on branch
        b) the latest commit that was tagged on the current branch (n)
        c) the latest commit that modified provided paths (hash)


    Example versions constructed:
        - 0.9.0-0.dev.git.2.hdfgh3456
        - 0.9.0-alpha.1
        - 0.9.0-alpha.1.git.0.hasdf1234 (--long)
        - 0.9.0-alpha.1.git.5.hsdfg2345
        - 0.9.0-alpha.1.git.5.hsdfg2345 (--long)
        - 0.9.0
    """
    # read Chart.yaml
    chart_file = os.path.join(name, "Chart.yaml")
    with open(chart_file) as f:
        chart = yaml.load(f)

    # decide a version string
    if version is None:
        # derive the full version, with possible '.git...'
        version = _get_identifier_from_paths(
            *paths, long=long, base_version=base_version
        )

    version = _fix_chart_version(version, strict=strict_version)

    # update Chart.yaml
    if chart["version"] == version:
        _log(f"Leaving {chart_file} version unchanged: {version}")
    else:
        _log(f"Updating {chart_file}: version: {version}")
        chart["version"] = version
        with open(chart_file, "w") as f:
            yaml.dump(chart, f)

    # return version
    return version


def publish_pages(
    chart_name,
    chart_version,
    chart_repo_github_path,
    chart_repo_url,
    extra_message="",
    force=False,
):
    """
    Update a Helm chart registry hosted in the gh-pages branch of a GitHub git
    repository.

    The strategy adopted to do this is:

    1. Clone the Helm chart registry as found in the gh-pages branch of a git
       reposistory.
    2. If --force-publish-chart isn't specified, then verify that we won't
       overwrite an existing chart version.
    3. Create a temporary directory and `helm package` the chart into a file
       within this temporary directory now only containing the chart .tar file.
    4. Generate a index.yaml with `helm repo index` based on charts found in the
       temporary directory folder (a single one), and then merge in the bigger
       and existing index.yaml from the cloned Helm chart registry using the
       --merge flag.
    5. Copy the new index.yaml and packaged Helm chart .tar into the gh-pages
       branch, commit it, and push it back to the origin remote.

    Note that if we would add the new chart .tar file next to the other .tar
    files and use `helm repo index` we would recreate `index.yaml` and update
    all the timestamps etc. which is something we don't want. Using `helm repo
    index` on a directory with only the new chart .tar file allows us to avoid
    this issue.

    Also note that the --merge flag will not override existing entries to the
    fresh index.yaml file with the index.yaml from the --merge flag. Due to
    this, it is as we would have a --force-publish-chart by default.
    """

    # clone/fetch the Helm chart repo and checkout its gh-pages branch, note the
    # use of cwd (current working directory)
    checkout_dir = f"{chart_name}-{chart_version}"
    if not os.path.isdir(checkout_dir):
        _check_call(
            [
                "git",
                "clone",
                "--no-checkout",
                _get_git_remote_url(chart_repo_github_path),
                checkout_dir,
            ],
            # We don't echo the GITHUB_TOKEN, it is censored in run_call
            echo=True,
        )
    else:
        _check_call(["git", "fetch"], cwd=checkout_dir, echo=True)
    _check_call(["git", "checkout", "gh-pages"], cwd=checkout_dir, echo=True)

    # check if a chart with the same name and version has already been published. If
    # there is, the behaviour depends on `--force-publish-chart`
    # and chart_version and make a decision based on the --force-publish-chart
    # flag if that is the case, but always log what's done
    if os.path.isfile(os.path.join(checkout_dir, "index.yaml")):
        with open(os.path.join(checkout_dir, "index.yaml")) as f:
            chart_repo_index = yaml.load(f)
            published_charts = chart_repo_index["entries"].get(chart_name, [])

        if published_charts and any(
            c["version"] == chart_version for c in published_charts
        ):
            if force:
                _log(
                    f"Chart of version {chart_version} already exists, overwriting it."
                )
            else:
                _log(
                    f"Skipping chart publishing of version {chart_version}, it is already published"
                )
                return

    # package the latest version into a temporary directory
    # and run helm repo index with --merge to update index.yaml
    # without refreshing all of the timestamps
    with TemporaryDirectory() as td:
        _check_call(
            [
                "helm",
                "package",
                chart_name,
                "--dependency-update",
                "--destination",
                td + "/",
            ]
        )

        _check_call(
            [
                "helm",
                "repo",
                "index",
                td,
                "--url",
                chart_repo_url,
                "--merge",
                os.path.join(checkout_dir, "index.yaml"),
            ]
        )

        # equivalent to `cp td/* checkout/`
        # copies new helm chart and updated index.yaml
        for f in os.listdir(td):
            shutil.copy2(os.path.join(td, f), os.path.join(checkout_dir, f))

    # git add, commit, and push
    extra_message = f"\n\n{extra_message}" if extra_message else ""
    message = (
        f"[{chart_name}] Automatic update for commit {chart_version}{extra_message}"
    )

    _check_call(["git", "add", "."], cwd=checkout_dir)
    _check_call(["git", "commit", "-m", message], cwd=checkout_dir)
    _check_call(["git", "push", "origin", "gh-pages"], cwd=checkout_dir)


def _check_base_version(base_version):
    """Verify that a baseVersion config is valid

    If specified, base version needs to:

    1. be a valid semver prerelease
    2. sort after the latest tag on the branch
    """

    if "-" not in base_version:
        # config version is a stable release,
        # append default '-0.dev' so we always produce a prerelease
        base_version = f"{base_version}-0.dev"
    # check valid value (baseVersion must be semver prerelease)
    match = _semver2.fullmatch(base_version)
    if not match:
        raise ValueError(
            f"baseVersion: {base_version} must be a valid semver version (e.g. 1.2.3-0.dev), but doesn't appear to be valid."
        )
    base_version_groups = match.groupdict()

    def _version_number(groups):
        """Return comparable semver"""

        return (
            int(groups["major"]),
            int(groups["minor"]),
            int(groups["patch"]),
        )

    # check ordering with latest tag
    # do not check on a tagged commit
    tag, count = _get_latest_tag_and_count()
    if tag and count:
        tag_match = _semver2.fullmatch(tag.lstrip("v"))
        sort_error = f"baseVersion {base_version} is not greater than latest tag {tag}. Please update baseVersion config in chartpress.yaml."
        if tag_match:
            base_version_number = _version_number(base_version_groups)
            tag_version_number = _version_number(tag_match.groupdict())
            if base_version_number < tag_version_number:
                raise ValueError(sort_error)
            elif base_version_number == tag_version_number:
                # numbers equal, need to check prerelease
                if tag_match["prerelease"]:
                    # If we want to be pedantic about inter-prerelease ordering (alpha before beta, etc.),
                    # that would go here. We should import a full semver implementation for that, though.
                    pass
                else:
                    raise ValueError(sort_error)
        else:
            # tag not semver. ignore? Not really our problem.
            _log(f"Latest tag {tag} does not appear to be a semver version")

    # return base_version, in case it was modified
    return base_version


class ActionStoreDeprecated(argparse.Action):
    """Used with argparse as a deprecation action."""

    def __call__(self, parser, namespace, values, option_string=None):
        _log(f"Warning: use of {'|'.join(self.option_strings)} is deprecated.")
        setattr(namespace, self.dest, values)


class ActionAppendDeprecated(argparse.Action):
    """Used with argparse as a deprecation action."""

    def __call__(self, parser, namespace, values, option_string=None):
        _log(f"Warning: use of {'|'.join(self.option_strings)} is deprecated.")
        if not getattr(namespace, self.dest):
            setattr(namespace, self.dest, [])
        getattr(namespace, self.dest).append(values)


def main(argv=None):
    """Run chartpress"""
    argparser = argparse.ArgumentParser(description=__doc__)

    argparser.add_argument(
        "--push",
        action="store_true",
        help="Push built images to their image registries, but not if it would replace an existing image.",
    )
    argparser.add_argument(
        "--force-push",
        action="store_true",
        help="Push built images to their image registries, regardless if it would replace an existing image.",
    )
    argparser.add_argument(
        "--publish-chart",
        action="store_true",
        help="Package a Helm chart and publish it to a Helm chart registry constructed with a GitHub git repository and GitHub pages, but not if it would replace an existing chart version.",
    )
    argparser.add_argument(
        "--force-publish-chart",
        action="store_true",
        help="Package a Helm chart and publish it to a Helm chart registry constructed with a GitHub git repository and GitHub pages, regardless if it would replace an existing chart version",
    )
    argparser.add_argument(
        "--extra-message",
        default="",
        help="Extra message to add to the commit message when publishing charts.",
    )
    tag_or_long_group = argparser.add_mutually_exclusive_group()
    tag_or_long_group.add_argument(
        "--tag",
        default=None,
        help="Explicitly set the image tags and chart version.",
    )
    tag_or_long_group.add_argument(
        "--long",
        action="store_true",
        help="Use this to always get a build suffix for the generated tag and chart version, even when the specific commit has a tag.",
    )
    argparser.add_argument(
        "--image-prefix",
        default=None,
        help="Override the configured image prefix with this value.",
    )
    argparser.add_argument(
        "--reset",
        action="store_true",
        help="Skip image build step and reset Chart.yaml's version field and values.yaml's image tags. What it resets to can be configured in chartpress.yaml with the resetTag and resetVersion configurations.",
    )
    skip_or_force_build_group = argparser.add_mutually_exclusive_group()
    skip_or_force_build_group.add_argument(
        "--no-build",
        "--skip-build",
        action="store_true",
        help="Skip the image build step.",
    )
    skip_or_force_build_group.add_argument(
        "--force-build",
        action="store_true",
        help="Enforce the image build step, regardless of if the image already is available either locally or remotely.",
    )

    argparser.add_argument(
        "--builder",
        choices=list(Builder),
        default=Builder.DOCKER_BUILD,
        type=Builder,
        help=f"Container build engine to use, {Builder.DOCKER_BUILD} is the standard Docker build command.",
    )

    argparser.add_argument(
        "--platform",
        action="append",
        help=(
            "Build the image for this platform, e.g. linux/amd64 or linux/arm64. "
            "This argument can be used multiple times to build multiple platforms under the same tag. "
            "Only supported for docker buildx. "
            "If --push is set or if multiple platforms are passed the image will not be loaded into the local docker engine."
        ),
    )

    argparser.add_argument(
        "--list-images",
        action="store_true",
        help="print list of images to stdout. Images will not be built.",
    )
    argparser.add_argument(
        "--version",
        action="version",
        version=f"chartpress version {__version__}",
    )

    args = argparser.parse_args(argv)
    if args.builder == Builder.DOCKER_BUILD and args.platform:
        argparser.error(f"--platform is not supported with {Builder.DOCKER_BUILD}")

    if args.reset:
        # reset conflicts with everything
        # this could probably be clearer by using subparsers
        argv = list(argv or sys.argv[1:])
        if len(argv) > 1:
            argv = list(argv)
            argv.remove("--reset")
            extra_args = " ".join(shlex.quote(arg) for arg in argv if arg != "--reset")
            argparser.error(
                f"`chartpress --reset` takes no additional arguments: {extra_args}"
            )

    # allow simple checks for whether publish will happen
    if args.force_publish_chart:
        args.publish_chart = True

    if args.list_images or args.reset:
        args.no_build = True
        args.publish_chart = False

    with open("chartpress.yaml") as f:
        config = yaml.load(f)

    # main logic
    # - loop through each chart listed in chartpress.yaml
    #   - build chart.yaml (--reset)
    #   - build images (--skip-build | --reset)
    #     - push images (--push)
    #   - build values.yaml (--reset)
    #   - push chart (--publish-chart, --extra-message)
    for chart in config["charts"]:
        forced_version = None
        base_version = None

        if args.tag:
            # tag specified, use that version
            forced_version = args.tag
        elif args.reset:
            forced_version = chart.get("resetVersion", "0.0.1-set.by.chartpress")

        if not args.tag:
            # Load base_version config when building a dev tag
            # (i.e. not a tagged commit or explicit tag).
            # add the check here so `--reset` will fail with an invalid baseVersion
            # (e.g. forgetting to update after release)
            base_version = chart.get("baseVersion", None)
            if base_version:
                base_version = _check_base_version(base_version)

        if not args.list_images:
            # update Chart.yaml with a version
            chart_version = build_chart(
                chart["name"],
                paths=_get_all_chart_paths(chart),
                version=forced_version,
                base_version=base_version,
                long=args.long,
                strict_version=args.publish_chart,
            )

        if "images" in chart:
            # set common image tag if `--tag` specified _or_ resetting
            common_image_tag = None
            if args.tag:
                common_image_tag = args.tag
            elif args.reset:
                common_image_tag = chart.get("resetTag", "set-by-chartpress")

            # build images
            values_file_modifications = build_images(
                prefix=args.image_prefix or chart.get("imagePrefix", ""),
                images=chart["images"],
                tag=common_image_tag,
                push=args.push,
                force_push=args.force_push,
                force_build=args.force_build,
                skip_build=args.no_build or args.reset,
                base_version=base_version,
                long=args.long,
                builder=args.builder,
                platforms=args.platform,
            )

            # list images
            if args.list_images:
                seen_images = set()
                for key, image_dict in values_file_modifications.items():
                    image = "{repository}:{tag}".format(**image_dict)
                    if image not in seen_images:
                        print(image)
                        # record image, in case the same image occurs in multiple places
                        seen_images.add(image)
                return

            # update values.yaml
            _update_values_file_with_modifications(
                chart["name"], values_file_modifications
            )

        # publish chart
        if args.publish_chart:
            publish_pages(
                chart_name=chart["name"],
                chart_version=chart_version,
                chart_repo_github_path=chart["repo"]["git"],
                chart_repo_url=chart["repo"]["published"],
                extra_message=args.extra_message,
                force=args.force_publish_chart,
            )


if __name__ == "__main__":
    main()
