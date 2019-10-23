from chartpress import GITHUB_TOKEN_KEY

from chartpress import git_remote
from chartpress import latest_tag_or_mod_commit
from chartpress import _strip_identifiers_build_suffix
from chartpress import _get_identifier

def test__strip_identifiers_build_suffix():
    assert _strip_identifiers_build_suffix(identifier="0.1.2-005.asdf1234") == "0.1.2"
    assert _strip_identifiers_build_suffix(identifier="0.1.2-alpha.1.005.asdf1234") == "0.1.2-alpha.1"

def test__get_identifier():
    assert _get_identifier(tag="0.1.2",         n_commits="0", commit="asdf123",  long=True)  == "0.1.2-000.asdf123"
    assert _get_identifier(tag="0.1.2",         n_commits="0", commit="asdf123",  long=False) == "0.1.2"
    assert _get_identifier(tag="0.1.2",         n_commits="5", commit="asdf123",  long=False) == "0.1.2-005.asdf123"
    assert _get_identifier(tag="0.1.2-alpha.1", n_commits="0", commit="asdf1234", long=True)  == "0.1.2-alpha.1.000.asdf1234"
    assert _get_identifier(tag="0.1.2-alpha.1", n_commits="0", commit="asdf1234", long=False) == "0.1.2-alpha.1"
    assert _get_identifier(tag="0.1.2-alpha.1", n_commits="5", commit="asdf1234", long=False) == "0.1.2-alpha.1.005.asdf1234"

def test_git_remote(monkeypatch):
    monkeypatch.setenv(GITHUB_TOKEN_KEY, "test-github-token")
    assert git_remote("jupyterhub/helm-chart") == "https://test-github-token@github.com/jupyterhub/helm-chart"

    monkeypatch.delenv(GITHUB_TOKEN_KEY)
    assert git_remote("jupyterhub/helm-chart") == "git@github.com:jupyterhub/helm-chart"

def test_latest_tag_or_mod_commit(git_repo):
    open('tag-mod.txt', "w").close()
    git_repo.index.add("tag-mod.txt")
    tag_commit = git_repo.index.commit("tag commit")
    git_repo.create_tag("1.0.0", message="1.0.0")

    open('post-tag-mod.txt', "w").close()
    git_repo.index.add("post-tag-mod.txt")
    post_tag_commit = git_repo.index.commit("post tag commit")

    assert tag_commit.hexsha.startswith(latest_tag_or_mod_commit("chartpress.yaml"))
    assert tag_commit.hexsha.startswith(latest_tag_or_mod_commit("tag-mod.txt"))
    assert post_tag_commit.hexsha.startswith(latest_tag_or_mod_commit("post-tag-mod.txt"))
