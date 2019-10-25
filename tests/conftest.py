import os
import tempfile
from distutils.dir_util import copy_tree

import git
import pytest

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
        test_helm_chart_repo_dir = os.path.join(chartpress_dir, "tests/test_helm_chart_repo")

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
