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
import shutil
import subprocess
from tempfile import TemporaryDirectory

import docker
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import SingleQuotedScalarString

__version__ = '0.3.2.dev'

# name of the environment variable with GitHub token
GITHUB_TOKEN_KEY = 'GITHUB_TOKEN'

# name of possible repository keys used in image value
IMAGE_REPOSITORY_KEYS = {'name', 'repository'}

# use safe roundtrip yaml loader
yaml = YAML(typ='rt')
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
    github_token = os.getenv(GITHUB_TOKEN_KEY)
    if github_token:
        return 'https://{0}@github.com/{1}'.format(
            github_token, git_repo)
    return 'git@github.com:{0}'.format(git_repo)


def last_modified_commit(*paths, **kwargs):
    """Get the last commit to modify the given paths"""
    return check_output([
        'git',
        'log',
        '-n', '1',
        '--pretty=format:%h',
        '--',
        *paths
    ], **kwargs).decode('utf-8')


def last_modified_date(*paths, **kwargs):
    """Return the last modified date (as a string) for the given paths"""
    return check_output([
        'git',
        'log',
        '-n', '1',
        '--pretty=format:%cd',
        '--date=iso',
        '--',
        *paths
    ], **kwargs).decode('utf-8')


def path_touched(*paths, commit_range):
    """Return whether the given paths have been changed in the commit range

    Used to determine if a build is necessary

    Args:
    *paths (str):
        paths to check for changes
    commit_range (str):
        range of commits to check if paths have changed
    """
    return check_output([
        'git', 'diff', '--name-only', commit_range, '--', *paths
    ]).decode('utf-8').strip() != ''


def render_build_args(options, ns):
    """Get docker build args dict, rendering any templated args.

    Args:
    options (dict):
        The dictionary for a given image from chartpress.yaml.
        Fields in `options['buildArgs']` will be rendered and returned,
        if defined.
    ns (dict): the namespace used when rendering templated arguments
    """
    build_args = options.get('buildArgs', {})
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
        d.images.get(image)
    except docker.errors.ImageNotFound:
        # image not found, check registry
        pass
    else:
        # it exists locally, no need to check remote
        return False

    # image may need building if it's not on the registry
    return image_needs_pushing(image)


def build_images(prefix, images, tag=None, commit_range=None, push=False, chart_version=None):
    """Build a collection of docker images

    Args:
    prefix (str): the prefix to add to images
    images (dict): dict of image-specs from chartpress.yml
    tag (str):
        Specific tag to use instead of the last modified commit.
        If unspecified the tag for each image will be the hash of the last commit
        to modify the image's files.
    commit_range (str):
        The range of commits to consider, e.g. for building in CI.
        If an image hasn't changed in the given range,
        it will not be rebuilt.
    push (bool):
        Whether to push the resulting images (default: False).
    chart_version (str):
        The chart version, included as a prefix on image tags
        if `tag` is not specified.
    """
    value_modifications = {}
    for name, options in images.items():
        image_path = options.get('contextPath', os.path.join('images', name))
        image_tag = tag
        # include chartpress.yaml itself as it can contain build args and
        # similar that influence the image that would be built
        paths = list(options.get('paths', [])) + [image_path, 'chartpress.yaml']
        last_commit = last_modified_commit(*paths)
        if tag is None:
            if chart_version:
                image_tag = "{}-{}".format(chart_version, last_commit)
            else:
                image_tag = last_commit
        image_name = prefix + name
        image_spec = '{}:{}'.format(image_name, image_tag)

        value_modifications[options['valuesPath']] = {
            'repository': image_name,
            'tag': SingleQuotedScalarString(image_tag),
        }

        template_namespace = {
            'LAST_COMMIT': last_commit,
            'TAG': image_tag,
        }

        if tag or image_needs_building(image_spec):
            build_args = render_build_args(options, template_namespace)
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
        parts = key.split('.')
        mod_obj = values
        for p in parts:
            mod_obj = mod_obj[p]
        print(f"Updating {values_file}: {key}: {value}")

        if isinstance(mod_obj, MutableMapping):
            keys = IMAGE_REPOSITORY_KEYS & mod_obj.keys()
            if keys:
                for key in keys:
                    mod_obj[key] = value['repository']
            else:
                possible_keys = ' or '.join(IMAGE_REPOSITORY_KEYS)
                raise KeyError(
                    f'Could not find {possible_keys} in {values_file}:{key}'
                )

            mod_obj['tag'] = value['tag']
        else:
            raise TypeError(
                f'The key {key} in {values_file} must be a mapping.'
            )


    with open(values_file, 'w') as f:
        yaml.dump(values, f)


def build_chart(name, version=None, paths=None):
    """Update chart with specified version or last-modified commit in path(s)"""
    chart_file = os.path.join(name, 'Chart.yaml')
    with open(chart_file) as f:
        chart = yaml.load(f)

    if version is None:
        if paths is None:
            paths = ['.']
        commit = last_modified_commit(*paths)
        # parse prerelease version, preserving only the first part
        # which will be the prerelease category (alpha, beta, etc.)
        # if nothing is found, use `0`, to sort before alpha
        base_version, *rest = chart['version'].split('-', 1)
        prerelease = 0
        if rest:
            prerelease = rest[0].split('.')[0]
            if not prerelease:
                prerelease = '0'

        describe = check_output(['git', 'describe', '--tags', '--long', commit]).decode('utf8').strip()
        _tag, n_commits, sha = describe.rsplit('-', 2)
        version = "{base_version}-{prerelease}.{n_commits}.{sha}".format(**locals())

    chart['version'] = version

    with open(chart_file, 'w') as f:
        yaml.dump(chart, f)

    return version


def publish_pages(name, paths, git_repo, published_repo, extra_message=''):
    """Publish helm chart index to github pages"""
    version = last_modified_commit(*paths)
    checkout_dir = '{}-{}'.format(name, version)
    check_call([
        'git', 'clone', '--no-checkout',
        git_remote(git_repo), checkout_dir],
        echo=False,
    )
    check_call(['git', 'checkout', 'gh-pages'], cwd=checkout_dir)

    # package the latest version into a temporary directory
    # and run helm repo index with --merge to update index.yaml
    # without refreshing all of the timestamps
    with TemporaryDirectory() as td:
        check_call([
            'helm', 'package', name,
            '--destination', td + '/',
        ])

        check_call([
            'helm', 'repo', 'index', td,
            '--url', published_repo,
            '--merge', os.path.join(checkout_dir, 'index.yaml'),
        ])

        # equivalent to `cp td/* checkout/`
        # copies new helm chart and updated index.yaml
        for f in os.listdir(td):
            shutil.copy2(
                os.path.join(td, f),
                os.path.join(checkout_dir, f)
            )
    check_call(['git', 'add', '.'], cwd=checkout_dir)
    if extra_message:
        extra_message = '\n\n%s' % extra_message
    else:
        extra_message = ''
    check_call([
        'git',
        'commit',
        '-m', '[{}] Automatic update for commit {}{}'.format(name, version, extra_message)
    ], cwd=checkout_dir)
    check_call(
        ['git', 'push', 'origin', 'gh-pages'],
        cwd=checkout_dir,
    )


def main():
    """Run chartpress"""
    argparser = argparse.ArgumentParser(description=__doc__)

    argparser.add_argument('--commit-range',
        help='Range of commits to consider when building images')
    argparser.add_argument('--push', action='store_true',
        help='push built images to docker hub')
    argparser.add_argument('--publish-chart', action='store_true',
        help='publish updated chart to gh-pages')
    argparser.add_argument('--tag', default=None,
        help='Use this tag for images & charts')
    argparser.add_argument('--extra-message', default='',
        help='extra message to add to the commit message when publishing charts')
    argparser.add_argument('--image-prefix', default=None,
        help='override image prefix with this value')

    args = argparser.parse_args()

    with open('chartpress.yaml') as f:
        config = yaml.load(f)

    for chart in config['charts']:
        chart_paths = ['.'] + list(chart.get('paths', []))

        version = args.tag
        if version:
            # version of the chart shouldn't have leading 'v' prefix
            # if tag is of the form 'v1.2.3'
            version = version.lstrip('v')
        chart_version = build_chart(chart['name'], paths=chart_paths, version=version)

        if 'images' in chart:
            image_prefix = args.image_prefix if args.image_prefix is not None else chart['imagePrefix']
            value_mods = build_images(
                prefix=image_prefix,
                images=chart['images'],
                tag=args.tag,
                commit_range=args.commit_range,
                push=args.push,
                # exclude `-<hash>` from chart_version prefix for images
                chart_version=chart_version.split('-', 1)[0],
            )
            build_values(chart['name'], value_mods)

        if args.publish_chart:
            publish_pages(chart['name'],
                paths=chart_paths,
                git_repo=chart['repo']['git'],
                published_repo=chart['repo']['published'],
                extra_message=args.extra_message,
            )


if __name__ == '__main__':
    main()
