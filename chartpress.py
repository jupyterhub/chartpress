#!/usr/bin/env python3
"""
Automate building and publishing helm charts and associated images.

This is used as part of the JupyterHub and Binder projects.
"""

import argparse
from collections.abc import MutableMapping
from functools import lru_cache, partial
import os
import pipes
import re
import shutil
import subprocess
from tempfile import TemporaryDirectory

import docker
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import SingleQuotedScalarString

__version__ = '0.4.3.dev'

# name of the environment variable with GitHub token
GITHUB_TOKEN_KEY = 'GITHUB_TOKEN'

# name of possible repository keys used in image value
IMAGE_REPOSITORY_KEYS = {'name', 'repository'}

# use safe roundtrip yaml loader
yaml = YAML(typ='rt')
yaml.preserve_quotes = True ## avoid mangling of quotes
yaml.indent(mapping=2, offset=2, sequence=4)


def run_cmd(call, cmd, *, echo=True, **kwargs):
    """Run a command and echo it first"""
    if echo:
        print('$> ' + ' '.join(map(pipes.quote, cmd)))
    return call(cmd, **kwargs)


check_call = partial(run_cmd, subprocess.check_call)
check_output = partial(run_cmd, subprocess.check_output)


def git_remote(git_repo):
    """Return the URL for remote git repository.

    Depending on the system setup it returns ssh or https remote.
    """
    # if not matching something/something
    # such as a local directory ".", then
    # simply return this unmodified.
    if not re.match(r'^[^/]+/[^/]+$', git_repo):
        return git_repo

    github_token = os.getenv(GITHUB_TOKEN_KEY)
    if github_token:
        return 'https://{0}@github.com/{1}'.format(
            github_token, git_repo)
    return 'git@github.com:{0}'.format(git_repo)


@lru_cache()
def latest_tag_or_mod_commit(*paths, **kwargs):
    """
    Get the latest of a) the latest tagged commit, or b) the latest modification
    commit to provided path.
    """
    latest_modification_commit = check_output(
        [
            'git', 'log',
            '--max-count=1',
            '--pretty=format:%h',
            '--',
            *paths,
        ],
        **kwargs,
    ).decode('utf-8').strip()

    try:
        git_describe_head = check_output(
            [
                'git', 'describe', '--tags', '--long',
            ],
            **kwargs,
        ).decode('utf-8').strip().rsplit("-", maxsplit=2)
    except subprocess.CalledProcessError:
        # no tags on branch
        return latest_modification_commit

    latest_tag = git_describe_head[0]
    latest_tagged_commit = check_output(
        [
            'git', 'rev-list', '--abbrev-commit', '-n', '1', latest_tag,
        ],
        **kwargs,
    ).decode('utf-8').strip()

    try:
        check_call(
            [
                'git', 'merge-base', '--is-ancestor', latest_tagged_commit, latest_modification_commit,
            ],
            **kwargs,
        )
    except subprocess.CalledProcessError:
        # latest_tagged_commit was newer than latest_modification_commit
        return latest_tagged_commit
    else:
        return latest_modification_commit


def render_build_args(image_options, ns):
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
    build_args = image_options.get('buildArgs', {})
    for key, value in build_args.items():
        build_args[key] = value.format(**ns)
    return build_args


def build_image(image_path, image_name, build_args=None, dockerfile_path=None):
    """Build an image

    Args:
    image_path (str): the path to the image directory
    image_name (str): image 'name:tag' to build
    build_args (dict, optional): dict of docker build arguments
    dockerfile_path (str, optional):
        path to dockerfile relative to image_path
        if not `image_path/Dockerfile`.
    """
    cmd = ['docker', 'build', '-t', image_name, image_path]
    if dockerfile_path:
        cmd.extend(['-f', dockerfile_path])

    for k, v in (build_args or {}).items():
        cmd += ['--build-arg', '{}={}'.format(k, v)]
    check_call(cmd)

@lru_cache()
def docker_client():
    """Cached getter for docker client"""
    return docker.from_env()


@lru_cache()
def image_needs_pushing(image):
    """Return whether an image needs pushing

    Args:

    image (str): the `repository:tag` image to be build.

    Returns:

    True: if image needs to be pushed (not on registry)
    False: if not (already present on registry)
    """
    d = docker_client()
    try:
        d.images.get_registry_data(image)
    except docker.errors.APIError:
        # image not found on registry, needs pushing
        return True
    else:
        return False

@lru_cache()
def image_needs_building(image):
    """Return whether an image needs building

    Checks if the image exists (ignores commit range),
    either locally or on the registry.

    Args:

    image (str): the `repository:tag` image to be build.

    Returns:

    True: if image needs to be built
    False: if not (image already exists)
    """
    d = docker_client()

    # first, check for locally built image
    try:
        print(image)
        d.images.get(image)
    except docker.errors.ImageNotFound:
        # image not found, check registry
        print("not found")
        pass
    else:
        # it exists locally, no need to check remote
        return False

    # image may need building if it's not on the registry
    return image_needs_pushing(image)


def _get_identifier(tag, n_commits, commit, long):
    """
    Returns a chartpress formatted chart version or image tag (identifier) with
    a build suffix.
    
    This function should provide valid Helm chart versions, which means they
    need to be valid SemVer 2 version strings. It also needs to return valid
    image tags, which means they need to not contain `+` signs either.

    Example:
        tag="0.1.2", n_commits="5", commit="asdf1234", long=True,
        should return "0.1.2-005.asdf1234".
    """
    n_commits = int(n_commits)

    if n_commits > 0 or long:
        if "-" in tag:
            # append a pre-release tag, with a . separator
            # 0.1.2-alpha.1 -> 0.1.2-alpha.1.n.sha
            return f"{tag}.{n_commits:03d}.{commit}"
        else:
            # append a release tag, with a - separator
            # 0.1.2 -> 0.1.2-n.sha
            return f"{tag}-{n_commits:03d}.{commit}"
    else:
        return f"{tag}"


def _strip_identifiers_build_suffix(identifier):
    """
    Return a stripped chart version or image tag (identifier) without its build
    suffix (.005.asdf1234), leaving it to represent a Semver 2 release or
    pre-release.

    Example:
        identifier: "0.1.2-005.asdf1234"            returns: "0.1.2"
        identifier: "0.1.2-alpha.1.005.asdf1234"    returns: "0.1.2-alpha.1"
    """
    # split away official SemVer 2 build specifications if used
    if "+" in identifier:
        return identifier.split("+", maxsplit=1)[0]

    # split away our custom build specification: something ending in either
    # . or - followed by three or more digits, a dot, an commit sha of four
    # or more alphanumeric characters.
    return re.sub(r'[-\.]\d{3,}\.\w{4,}\Z', "", identifier)


def build_images(prefix, images, tag=None, push=False, chart_version=None, skip_build=False, long=False):
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
    chart_version (str):
        The latest chart version, trimmed from its build suffix, will be included
        as a prefix on image tags if `tag` is not specified.
    skip_build (bool):
        Whether to skip the actual image build (only updates tags).
    long (bool):
        Whether to include the generated tag's build suffix even when the commit
        has a tag. Setting long to true could be useful if you have two build
        pipelines, one for commits and one for tags, and want to avoid
        generating conflicting build artifacts.

        Example 1:
        - long=False: 0.9.0
        - long=True:  0.9.0-000.asdf1234

        Example 2:
        - long=False: 0.9.0-004.sdfg2345
        - long=True:  0.9.0-004.sdfg2345
    """
    value_modifications = {}
    for name, options in images.items():
        image_path = options.get('contextPath', os.path.join('images', name))
        image_tag = tag
        chart_version = _strip_identifiers_build_suffix(chart_version)
        # include chartpress.yaml itself as it can contain build args and
        # similar that influence the image that would be built
        paths = list(options.get('paths', [])) + [image_path, 'chartpress.yaml']
        image_commit = latest_tag_or_mod_commit(*paths, echo=False)
        if image_tag is None:
            n_commits = check_output(
                [
                    'git', 'rev-list', '--count',
                    # Note that the 0.0.1 chart_version may not exist as it was a
                    # workaround to handle git histories with no tags in the
                    # current branch. Also, if the chart_version is a later git
                    # reference than the image_commit, this
                    # command will return 0.
                    f'{"" if chart_version == "0.0.1" else chart_version + ".."}{image_commit}',
                ],
                echo=False,
            ).decode('utf-8').strip()
            image_tag = _get_identifier(chart_version, n_commits, image_commit, long)
        image_name = prefix + name
        image_spec = '{}:{}'.format(image_name, image_tag)

        values_path_list = options['valuesPath']
        if isinstance(values_path_list, str):
            # single path, wrap it in a list
            values_path_list = [values_path_list]

        for values_path in values_path_list:
            value_modifications[values_path] = {
                'repository': image_name,
                'tag': SingleQuotedScalarString(image_tag),
            }

        if skip_build:
            continue

        if tag or image_needs_building(image_spec):
            build_args = render_build_args(
                options,
                {
                    'LAST_COMMIT': image_commit,
                    'TAG': image_tag,
                },
            )
            build_image(image_path, image_spec, build_args, options.get('dockerfilePath'))
        else:
            print(f"Skipping build for {image_spec}, it already exists")

        if push:
            if tag or image_needs_pushing(image_spec):
                check_call([
                    'docker', 'push', image_spec
                ])
            else:
                print(f"Skipping push for {image_spec}, already on registry")
    return value_modifications


def build_values(name, values_mods):
    """Update name/values.yaml with modifications"""
    values_file = os.path.join(name, 'values.yaml')

    with open(values_file) as f:
        values = yaml.load(f)

    for key, value in values_mods.items():
        if not isinstance(value, dict) or set(value.keys()) != {'repository', 'tag'}:
            raise ValueError(f"I only understand image updates with 'repository', 'tag', not: {value!r}")
        parts = key.split('.')
        mod_obj = parent = values
        for p in parts:
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
                    if before != value['repository']:
                        print(f"Updating {values_file}: {key}.{repo_key}: {value}")
                    mod_obj[repo_key] = value['repository']
            else:
                possible_keys = ' or '.join(IMAGE_REPOSITORY_KEYS)
                raise KeyError(
                    f'Could not find {possible_keys} in {values_file}:{key}'
                )

            before = mod_obj.get('tag', None)
            if before != value['tag']:
                print(f"Updating {values_file}: {key}.tag: {value}")
            mod_obj['tag'] = value['tag']
        elif isinstance(mod_obj, str):
            # scalar image string, not dict with separate repository, tag keys
            image = "{repository}:{tag}".format(**value)
            try:
                before = parent[last_part]
            except (KeyError, IndexError):
                before = None
            if before != image:
                print(f"Updating {values_file}: {key}: {image}")
            parent[last_part] = image
        else:
            raise TypeError(
                f'The key {key} in {values_file} must be a mapping or string, not {type(mod_obj)}.'
            )


    with open(values_file, 'w') as f:
        yaml.dump(values, f)


def build_chart(name, version=None, paths=None, long=False):
    """
    Update Chart.yaml's version, using specified version or by constructing one.
    
    Chart versions are constructed using:
        a) the latest commit that is tagged,
        b) the latest commit that modified provided paths

    Example versions constructed:
        - 0.9.0-alpha.1
        - 0.9.0-alpha.1.000.asdf1234 (--long)
        - 0.9.0-alpha.1.005.sdfg2345
        - 0.9.0-alpha.1.005.sdfg2345 (--long)
        - 0.9.0
        - 0.9.0-002.dfgh3456
    """
    chart_file = os.path.join(name, 'Chart.yaml')
    with open(chart_file) as f:
        chart = yaml.load(f)

    if version is None:
        chart_commit = latest_tag_or_mod_commit(*paths, echo=False)

        try:
            git_describe = check_output(
                [
                    'git', 'describe', '--tags', '--long', chart_commit
                ],
                echo=False,
            ).decode('utf8').strip()
            latest_tag_in_branch, n_commits, sha = git_describe.rsplit('-', maxsplit=2)
            # remove "g" prefix output by the git describe command
            # ref: https://git-scm.com/docs/git-describe#_examples
            sha = sha[1:]
            version = _get_identifier(latest_tag_in_branch, n_commits, sha, long)
        except subprocess.CalledProcessError:
            # no tags on branch: fallback to the SemVer 2 compliant version
            # 0.0.1-<n_commits>.<chart_commit>
            latest_tag_in_branch = "0.0.1"
            n_commits = check_output(
                [
                    'git', 'rev-list', '--count', chart_commit
                ],
                echo=False,
            ).decode('utf-8').strip()

            version = _get_identifier(latest_tag_in_branch, n_commits, chart_commit, long)

    if chart['version'] != version:
        print(f"Updating {chart_file}: version: {version}")
        chart['version'] = version

    with open(chart_file, 'w') as f:
        yaml.dump(chart, f)

    return version


def publish_pages(chart_name, chart_version, chart_repo_github_path, chart_repo_url, extra_message=''):
    """Publish Helm chart index to github pages"""
    # clone the Helm chart repo and checkout its gh-pages branch,
    # note the use of cwd (current working directory)
    checkout_dir = '{}-{}'.format(chart_name, chart_version)
    check_call(
        [
            'git', 'clone', '--no-checkout',
            git_remote(chart_repo_github_path),
            checkout_dir,
        ],
        # warning: if echoed, this call could reveal the github token
        echo=True,
    )
    check_call(['git', 'checkout', 'gh-pages'], cwd=checkout_dir, echo=True)

    # package the latest version into a temporary directory
    # and run helm repo index with --merge to update index.yaml
    # without refreshing all of the timestamps
    with TemporaryDirectory() as td:
        check_call([
            'helm', 'package', chart_name,
            '--destination', td + '/',
        ])

        check_call([
            'helm', 'repo', 'index', td,
            '--url', chart_repo_url,
            '--merge', os.path.join(checkout_dir, 'index.yaml'),
        ])

        # equivalent to `cp td/* checkout/`
        # copies new helm chart and updated index.yaml
        for f in os.listdir(td):
            shutil.copy2(
                os.path.join(td, f),
                os.path.join(checkout_dir, f)
            )

    # git add, commit, and push
    extra_message = f'\n\n{extra_message}' if extra_message else ''
    message = f'[{chart_name}] Automatic update for commit {chart_version}{extra_message}'

    check_call(['git', 'add', '.'], cwd=checkout_dir)
    check_call(['git', 'commit', '-m', message], cwd=checkout_dir)
    check_call(['git', 'push', 'origin', 'gh-pages'], cwd=checkout_dir)



class ActionStoreDeprecated(argparse.Action):
    """Used with argparse as a deprecation action."""
    def __call__(self, parser, namespace, values, option_string=None):
        print(f"Warning: use of {'|'.join(self.option_strings)} is deprecated.")
        setattr(namespace, self.dest, values)


class ActionAppendDeprecated(argparse.Action):
    """Used with argparse as a deprecation action."""
    def __call__(self, parser, namespace, values, option_string=None):
        print(f"Warning: use of {'|'.join(self.option_strings)} is deprecated.")
        if not getattr(namespace, self.dest):
            setattr(namespace, self.dest, [])
        getattr(namespace, self.dest).append(values)



def main(args=None):
    """Run chartpress"""
    argparser = argparse.ArgumentParser(description=__doc__)

    argparser.add_argument(
        '--push',
        action='store_true',
        help='Push built images to their docker image registry.',
    )
    argparser.add_argument(
        '--publish-chart',
        action='store_true',
        help='Package a Helm chart and publish it to a Helm chart repository contructed with a GitHub git repository and GitHub pages.',
    )
    argparser.add_argument(
        '--extra-message',
        default='',
        help='Extra message to add to the commit message when publishing charts.',
    )
    tag_or_long_group = argparser.add_mutually_exclusive_group()
    tag_or_long_group.add_argument(
        '--tag',
        default=None,
        help="Explicitly set the image tags and chart version.",
    )
    tag_or_long_group.add_argument(
        '--long',
        action='store_true',
        help='Use this to always get a build suffix for the generated tag and chart version, even when the specific commit has a tag.',
    )
    argparser.add_argument(
        '--image-prefix',
        default=None,
        help='Override the configured image prefix with this value.',
    )
    argparser.add_argument(
        '--reset',
        action='store_true',
        help="Skip image build step and reset Chart.yaml's version field and values.yaml's image tags. What it resets to can be configured in chartpress.yaml with the resetTag and resetVersion configurations.",
    )
    argparser.add_argument(
        '--skip-build',
        action='store_true',
        help='Skip the image build step.',
    )
    argparser.add_argument(
        '--version',
        action='store_true',
        help='Print current chartpress version and exit.',
    )

    argparser.add_argument(
        '--commit-range',
        action=ActionStoreDeprecated,
        help='Deprecated: this flag will be ignored. The new logic to determine if an image needs to be rebuilt does not require this. It will find the time in git history where the image was last in need of a rebuild due to changes, and check if that build exists locally or remotely already.',
    )

    args = argparser.parse_args(args)

    if args.version:
        print(f"chartpress version {__version__}")
        return

    with open('chartpress.yaml') as f:
        config = yaml.load(f)

    # main logic
    # - loop through each chart listed in chartpress.yaml
    #   - build chart.yaml (--reset)
    #   - build images (--skip-build | --reset)
    #     - push images (--push)
    #   - build values.yaml (--reset)
    #   - push chart (--publish-chart, --extra-message)
    for chart in config['charts']:
        chart_paths = ['.'] + list(chart.get('paths', []))

        chart_version = args.tag
        if chart_version:
            # The chart's version shouldn't have leading 'v' prefix if tag is of
            # the form 'v1.2.3', as that would break Chart.yaml's SemVer 2
            # requirement on the version field.
            chart_version = chart_version.lstrip('v')
        if args.reset:
            chart_version = chart.get('resetVersion', '0.0.1-set.by.chartpress')
        chart_version = build_chart(chart['name'], paths=chart_paths, version=chart_version, long=args.long)

        if 'images' in chart:
            image_prefix = args.image_prefix if args.image_prefix is not None else chart['imagePrefix']
            value_mods = build_images(
                prefix=image_prefix,
                images=chart['images'],
                tag=args.tag if not args.reset else chart.get('resetTag', 'set-by-chartpress'),
                push=args.push,
                chart_version=chart_version,
                skip_build=args.skip_build or args.reset,
                long=args.long,
            )
            build_values(chart['name'], value_mods)

        if args.publish_chart:
            publish_pages(
                chart_name=chart['name'],
                chart_version=chart_version,
                chart_repo_github_path=chart['repo']['git'],
                chart_repo_url=chart['repo']['published'],
                extra_message=args.extra_message,
            )


if __name__ == '__main__':
    main()
