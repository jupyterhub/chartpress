import os
import shutil
import tempfile
from distutils.dir_util import copy_tree

import git
import pytest

import chartpress


@pytest.fixture(scope="function")
def git_repo(monkeypatch):
    """
    This fixture provides a temporary git repo with two branches initialized.
    master contains a test helm chart copied from tests/test_helm_chart, and
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

        # enter blank branch master
        # copy content of tests/test_helm_chart and commit it
        r.git.checkout("--orphan", "master")
        copy_tree(test_helm_chart_dir, temp_dir)
        r.git.add(all=True)
        r.index.commit("initial commit")

        yield r


@pytest.fixture(scope="function")
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


@pytest.fixture(scope="function")
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


@pytest.fixture(scope="function")
def mock_check_call(monkeypatch):
    """
    Replace chartpress._check_call with a no-op version that records all commands
    Also disable lcu_cache to prevent cached information being kept across test calls
    """
    mock_call = MockCheckCall()
    monkeypatch.setattr(chartpress, "_check_call", mock_call)
    monkeypatch.setattr(chartpress, "lru_cache", lambda func: func)

    yield mock_call
