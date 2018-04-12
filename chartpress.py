#!/usr/bin/env python3
"""
Automate building and publishing helm charts and associated images.

This is used as part of the JupyterHub and Binder projects.
"""

import argparse
import os
import subprocess
import shutil
from tempfile import TemporaryDirectory

from ruamel.yaml import YAML

__version__ = '0.2.0.dev'

# use safe roundtrip yaml loader
yaml = YAML(typ='rt')
yaml.indent(mapping=2, offset=2, sequence=4)


def last_modified_commit(*paths, **kwargs):
    """Get the last commit to modify the given paths"""
    return subprocess.check_output([
        'git',
        'log',
        '-n', '1',
        '--pretty=format:%h',
        *paths
    ], **kwargs).decode('utf-8')


def last_modified_date(*paths, **kwargs):
    """Return the last modified date (as a string) for the given paths"""
    return subprocess.check_output([
        'git',
        'log',
        '-n', '1',
        '--pretty=format:%cd',
        '--date=iso',
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
    return subprocess.check_output([
        'git', 'diff', '--name-only', commit_range, *paths
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

def build_image(image_path, image_spec, build_args, dockerfile_path=None):

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

    for k, v in build_args.items():
        cmd += ['--build-arg', '{}={}'.format(k, v)]
    subprocess.check_call(cmd)


def build_images(prefix, images, tag=None, commit_range=None, push=False):
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
    """
    value_modifications = {}
    for name, options in images.items():
        image_path = options.get('contextPath', os.path.join('images', name))
        image_tag = tag
        paths = options.get('paths', []) + [image_path]
        last_commit = last_modified_commit(*paths)
        if tag is None:
            image_tag = last_commit
        image_name = prefix + name
        image_spec = '{}:{}'.format(image_name, image_tag)
        value_modifications[options['valuesPath']] = {
            'name': image_name,
            'tag': image_tag,
        }

        if tag is None and commit_range and not path_touched(*paths, commit_range=commit_range):
            print(f"Skipping {name}, not touched in {commit_range}")
            continue

        template_namespace = {
            'LAST_COMMIT': last_commit,
            'TAG': image_tag,
        }

        build_args = render_build_args(options, template_namespace)
        build_image(image_path, image_spec, build_args, options.get('dockerfilePath'))

        if push:
            subprocess.check_call([
                'docker', 'push', image_spec
            ])
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
        mod_obj.update(value)


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
        version = chart['version'].split('-')[0] + '-' + commit

    chart['version'] = version

    with open(chart_file, 'w') as f:
        yaml.dump(chart, f)


def publish_pages(name, paths, git_repo, published_repo, extra_message=''):
    """Publish helm chart index to github pages"""
    version = last_modified_commit(*paths)
    checkout_dir = '{}-{}'.format(name, version)
    subprocess.check_call([
        'git', 'clone', '--no-checkout',
        'git@github.com:{}'.format(git_repo), checkout_dir],
    )
    subprocess.check_call(['git', 'checkout', 'gh-pages'], cwd=checkout_dir)

    # package the latest version into a temporary directory
    # and run helm repo index with --merge to update index.yaml
    # without refreshing all of the timestamps
    with TemporaryDirectory() as td:
        subprocess.check_call([
            'helm', 'package', name,
            '--destination', td + '/',
        ])

        subprocess.check_call([
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
    subprocess.check_call(['git', 'add', '.'], cwd=checkout_dir)
    if extra_message:
        extra_message = '\n\n%s' % extra_message
    else:
        extra_message = ''
    subprocess.check_call([
        'git',
        'commit',
        '-m', '[{}] Automatic update for commit {}{}'.format(name, version, extra_message)
    ], cwd=checkout_dir)
    subprocess.check_call(
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

    args = argparser.parse_args()

    with open('chartpress.yaml') as f:
        config = yaml.load(f)

    for chart in config['charts']:
        if 'images' in chart:
            value_mods = build_images(
                prefix=chart['imagePrefix'],
                images=chart['images'],
                tag=args.tag,
                commit_range=args.commit_range,
                push=args.push,
            )
            build_values(chart['name'], value_mods)
        chart_paths = ['.'] + chart.get('paths', [])
        build_chart(chart['name'], paths=chart_paths, version=args.tag)
        if args.publish_chart:
            publish_pages(chart['name'],
                paths=chart_paths,
                git_repo=chart['repo']['git'],
                published_repo=chart['repo']['published'],
                extra_message=args.extra_message,
            )


if __name__ == '__main__':
    main()
