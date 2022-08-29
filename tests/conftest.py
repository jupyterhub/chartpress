import os
import shutil
import sys
import tempfile
from functools import partial

import git
import pytest

import chartpress

if sys.version_info >= (3, 8):
    copy_tree = partial(shutil.copytree, dirs_exist_ok=True)
else:
    # use deprecated distutils on Python < 3.8
    # when shutil.copytree added dirs_exist_ok support
    from distutils.dir_util import copy_tree


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "registry: mark a test that modifies a container registry"
    )


@pytest.fixture
def git_repo(monkeypatch):
    """
    This fixture provides a temporary git repo with two branches initialized.
    main contains a test helm chart copied from tests/test_helm_chart, and
    gh-pages that contains the content of tests/test_helm_chart_repo.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        chartpress_dir = os.getcwd()
        test_helm_chart_dir = os.path.join(chartpress_dir, "tests/test_helm_chart")
        test_helm_chart_repo_dir = os.path.join(
            chartpress_dir, "tests/test_helm_chart_repo"
        )

        # enter the directory
        monkeypatch.chdir(temp_dir)

        # initialize the repo
        r = git.Repo.init(temp_dir)

        # enter blank branch gh-pages
        # copy content of tests/test_helm_chart_repo and commit it
        r.git.checkout("--orphan", "gh-pages")
        copy_tree(test_helm_chart_repo_dir, temp_dir)
        r.git.add(all=True)
        r.index.commit("initial commit")

        # enter blank branch main
        # copy content of tests/test_helm_chart and commit it
        r.git.checkout("--orphan", "main")
        copy_tree(test_helm_chart_dir, temp_dir)
        r.git.add(all=True)
        r.index.commit("initial commit")

        yield r


@pytest.fixture
def git_repo_bare_minimum(monkeypatch, git_repo):
    """
    This fixture modifies the default git_repo fixture to use another the
    chartpress_bare_minimum.yaml as chartpress.yaml and removes the image
    directory.
    """
    r = git_repo
    shutil.move("chartpress_bare_minimum.yaml", "chartpress.yaml")
    shutil.rmtree("image")
    r.git.add(all=True)
    r.index.commit("chartpress_bare_minimum.yaml initial commit")

    yield r


@pytest.fixture
def git_repo_dev_tag(git_repo):
    """
    This fixture modifies the default git_repo fixture
    to create a repo with a dev tag on the default branch
    and a '1.x' backport branch

    Both branches have a tag only on that branch,
    and both branches have one commit since the latest tag:

    main        1.x
    |           |
    @2.0.0-dev  @1.0.1
    |          /
    @1.0.0
    """
    r = git_repo
    r.git.tag("1.0.0")
    r.git.branch("1.x")
    r.git.checkout("1.x")
    image_file = os.path.join("image", "test.txt")

    with open(image_file, "w") as f:
        f.write("1.0.1")
    r.git.add(image_file)
    r.index.commit("add file for 1.0.1")
    r.git.tag("1.0.1")

    with open(image_file, "w") as f:
        f.write("1.x")
    r.git.add(image_file)
    r.index.commit("add file for 1.x")

    r.git.checkout("main")
    with open(image_file, "w") as f:
        f.write("2.0.0-dev")
    r.git.add(image_file)
    r.index.commit("add file for 2.0.0-dev")
    r.git.tag("2.0.0-dev")

    with open(image_file, "w") as f:
        f.write("2.x")
    r.git.add(image_file)
    r.index.commit("add file for 2.x")

    yield r


@pytest.fixture
def git_repo_backport_branch(git_repo_dev_tag):
    """Git repo with a backport branch currently checked out"""
    r = git_repo_dev_tag
    r.git.checkout("1.x")
    yield r


@pytest.fixture
def git_repo_alternative(monkeypatch, git_repo):
    """
    This fixture modifies the default git_repo fixture to use another the
    chartpress_alternative.yaml as chartpress.yaml.
    """
    r = git_repo
    shutil.move("chartpress_alternative.yaml", "chartpress.yaml")
    r.git.add(all=True)
    r.index.commit("chartpress_alternative.yaml initial commit")

    yield r


class MockCheckCall:
    def __init__(self):
        self.commands = []

    def __call__(self, cmd, **kwargs):
        self.commands.append((cmd, kwargs))


def cache_clear():
    """Clear lru cache to better mimic CLI behavior"""
    # Need to clear @lru_cache since we test multiple temporary repositories
    for name in dir(chartpress):
        obj = getattr(chartpress, name)
        if hasattr(obj, "cache_clear"):
            obj.cache_clear()


@pytest.fixture(autouse=True)
def _cache_clear():
    cache_clear()
    # return it so it can be re-used mid-test
    return cache_clear


@pytest.fixture(scope="function")
def mock_check_call(monkeypatch, _cache_clear):
    """
    Replace chartpress._check_call with a no-op version that records all commands
    Also disable lru_cache to prevent cached information being kept across test calls
    """
    mock_call = MockCheckCall()
    monkeypatch.setattr(chartpress, "_check_call", mock_call)

    yield mock_call
