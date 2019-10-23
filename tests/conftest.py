import os
import tempfile
from distutils.dir_util import copy_tree

import git
import pytest

@pytest.fixture(scope="function")
def git_repo(monkeypatch):
    """A temporary git repo with """
    with tempfile.TemporaryDirectory() as temp_dir:
        # copy content of tests/data folder to the temp dir
        copy_tree("tests/data", os.path.join(temp_dir))

        # enter the directory
        monkeypatch.chdir(temp_dir)

        # initialize the repo and make one initial commit
        repo = git.Repo.init(temp_dir)
        repo.index.add(".")
        repo.index.commit("initial commit")

        yield repo
