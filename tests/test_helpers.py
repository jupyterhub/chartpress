from ruamel.yaml import YAML

from chartpress import _check_call
from chartpress import _get_git_remote_url
from chartpress import _get_identifier_from_parts
from chartpress import _get_image_build_args
from chartpress import _get_latest_commit_tagged_or_modifying_paths
from chartpress import _image_needs_pushing
from chartpress import _strip_build_suffix_from_identifier
from chartpress import Builder
from chartpress import GITHUB_ACTOR_KEY
from chartpress import GITHUB_TOKEN_KEY

# use safe roundtrip yaml loader
yaml = YAML(typ="rt")
yaml.preserve_quotes = True  ## avoid mangling of quotes
yaml.indent(mapping=2, offset=2, sequence=4)


def test__strip_build_suffix_from_identifier():
    assert (
        _strip_build_suffix_from_identifier(identifier="0.1.2-n005.hasdf1234")
        == "0.1.2"
    )
    assert (
        _strip_build_suffix_from_identifier(identifier="0.1.2-alpha.1.n005.hasdf1234")
        == "0.1.2-alpha.1"
    )


def test__get_identifier_from_parts():
    assert (
        _get_identifier_from_parts(
            tag="0.1.2", n_commits="0", commit="asdf123", long=True
        )
        == "0.1.2-n000.hasdf123"
    )
    assert (
        _get_identifier_from_parts(
            tag="0.1.2", n_commits="0", commit="asdf123", long=False
        )
        == "0.1.2"
    )
    assert (
        _get_identifier_from_parts(
            tag="0.1.2", n_commits="5", commit="asdf123", long=False
        )
        == "0.1.2-n005.hasdf123"
    )
    assert (
        _get_identifier_from_parts(
            tag="0.1.2-alpha.1", n_commits="0", commit="asdf1234", long=True
        )
        == "0.1.2-alpha.1.n000.hasdf1234"
    )
    assert (
        _get_identifier_from_parts(
            tag="0.1.2-alpha.1", n_commits="0", commit="asdf1234", long=False
        )
        == "0.1.2-alpha.1"
    )
    assert (
        _get_identifier_from_parts(
            tag="0.1.2-alpha.1", n_commits="5", commit="asdf1234", long=False
        )
        == "0.1.2-alpha.1.n005.hasdf1234"
    )


def test__get_git_remote_url(monkeypatch):
    monkeypatch.setenv(GITHUB_ACTOR_KEY, "test-github-actor")
    monkeypatch.setenv(GITHUB_TOKEN_KEY, "test-github-token")
    assert (
        _get_git_remote_url("jupyterhub/helm-chart")
        == "https://test-github-actor:test-github-token@github.com/jupyterhub/helm-chart"
    )

    monkeypatch.delenv(GITHUB_ACTOR_KEY)
    assert (
        _get_git_remote_url("jupyterhub/helm-chart")
        == "https://test-github-token@github.com/jupyterhub/helm-chart"
    )

    monkeypatch.delenv(GITHUB_TOKEN_KEY)
    assert (
        _get_git_remote_url("jupyterhub/helm-chart")
        == "git@github.com:jupyterhub/helm-chart"
    )


def test_git_token_censoring(monkeypatch, capfd):
    monkeypatch.setenv(GITHUB_TOKEN_KEY, "secret-token-not-to-be-exposed-in-logs")
    _check_call(
        [
            "echo",
            "Non failing dummy command with secret-token-not-to-be-exposed-in-logs",
        ]
    )
    _, err = capfd.readouterr()
    assert "CENSORED_GITHUB_TOKEN" in err


def test__image_needs_pushing():
    assert _image_needs_pushing(
        "jupyterhub/image-not-to-be-found:latest", Builder.DOCKER_BUILD
    )
    assert not _image_needs_pushing("jupyterhub/k8s-hub:0.8.2", Builder.DOCKER_BUILD)
    assert _image_needs_pushing("jupyterhub/k8s-hub:0.8.2", Builder.DOCKER_BUILDX)


def test__get_latest_commit_tagged_or_modifying_paths(git_repo):
    open("tag-mod.txt", "w").close()
    git_repo.index.add("tag-mod.txt")
    tag_commit = git_repo.index.commit("tag commit")
    git_repo.create_tag("1.0.0", message="1.0.0")

    open("post-tag-mod.txt", "w").close()
    git_repo.index.add("post-tag-mod.txt")
    post_tag_commit = git_repo.index.commit("post tag commit")

    assert (
        _get_latest_commit_tagged_or_modifying_paths("chartpress.yaml")
        == tag_commit.hexsha[:7]
    )
    assert (
        _get_latest_commit_tagged_or_modifying_paths("tag-mod.txt")
        == tag_commit.hexsha[:7]
    )
    assert (
        _get_latest_commit_tagged_or_modifying_paths("post-tag-mod.txt")
        == post_tag_commit.hexsha[:7]
    )


def test__get_image_build_args(git_repo):
    with open("chartpress.yaml") as f:
        config = yaml.load(f)
    for chart in config["charts"]:
        for name, options in chart["images"].items():
            build_args = _get_image_build_args(
                options,
                {
                    "LAST_COMMIT": "sha",
                    "TAG": "tag",
                },
            )
            assert name in ("testimage", "amd64only")
            if name == "testimage":
                assert build_args == {
                    "TEST_STATIC_BUILD_ARG": "test",
                    "TEST_DYNAMIC_BUILD_ARG": "tag-sha",
                }
            else:
                assert build_args == {}
