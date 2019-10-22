import os
import tempfile
from distutils.dir_util import copy_tree

import git
import pytest

@pytest.fixture(scope="function")
def git_repo():
    """A temporary git repo with """
    with tempfile.TemporaryDirectory() as temp_dir:
        copy_tree("tests/data", os.path.join(temp_dir))

        stashed_cwd = os.getcwd()
        os.chdir(temp_dir)
        yield git.Repo.init(temp_dir)
        os.chdir(stashed_cwd)
