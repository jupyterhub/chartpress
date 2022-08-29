from unittest import mock

import pytest

import chartpress
from chartpress import (
    GITHUB_ACTOR_KEY,
    GITHUB_TOKEN_KEY,
    _check_call,
    _fix_chart_version,
    _get_git_remote_url,
    _get_identifier_from_parts,
    _get_image_build_args,
    _get_image_extra_build_command_options,
    _get_latest_commit_tagged_or_modifying_paths,
    _image_needs_pushing,
    yaml,
)


@pytest.mark.parametrize(
    "tag, n_commits, commit, long, expected",
    [
        ("0.1.2", "0", "asdf123", True, "0.1.2-0.dev.git.0.hasdf123"),
        ("0.1.2", "0", "asdf123", False, "0.1.2"),
        ("0.1.2", "5", "asdf123", False, "0.1.2-0.dev.git.5.hasdf123"),
        ("0.1.2-alpha.1", "0", "asdf1234", True, "0.1.2-alpha.1.git.0.hasdf1234"),
        ("0.1.2-alpha.1", "0", "asdf1234", False, "0.1.2-alpha.1"),
        ("0.1.2-alpha.1", "5", "asdf1234", False, "0.1.2-alpha.1.git.5.hasdf1234"),
    ],
)
def test_get_identifier_from_parts(tag, n_commits, commit, long, expected):
    tag = _get_identifier_from_parts(
        tag=tag, n_commits=n_commits, commit=commit, long=long
    )
    assert tag == expected
    _fix_chart_version(tag, strict=True)


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


@pytest.mark.parametrize(
    "image, platforms, push",
    [
        ("jupyterhub/image-not-to-be-found:latest", None, True),
        ("jupyterhub/k8s-hub:0.8.2", None, False),
        ("jupyterhub/k8s-hub:0.8.2", ["linux/arm64"], True),
        ("jupyterhub/k8s-hub:0.8.2", ["linux/amd64", "linux/arm64"], True),
        ("jupyterhub/k8s-hub:0.8.2", ["linux/amd64"], False),
        ("jupyterhub/k8s-hub:1.0.0", ["linux/amd64", "linux/arm64"], False),
        (
            "jupyterhub/k8s-hub:1.0.0",
            ["linux/amd64", "linux/arm64", "linux/s390x"],
            True,
        ),
    ],
)
def test__image_needs_pushing(image, platforms, push):
    if platforms is None:
        assert _image_needs_pushing(image, platforms) == push
    else:
        assert _image_needs_pushing(image, frozenset(platforms)) == push


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


def test__get_image_extra_build_command_options(git_repo):
    with open("chartpress.yaml") as f:
        config = yaml.load(f)
    for chart in config["charts"]:
        for name, options in chart["images"].items():
            extra_build_command_options = _get_image_extra_build_command_options(
                options,
                {
                    "LAST_COMMIT": "sha",
                    "TAG": "tag",
                },
            )
            assert name in ("testimage", "amd64only")
            if name == "testimage":
                assert extra_build_command_options == [
                    "--label=maintainer=octocat",
                    "--label",
                    "ref=tag-sha",
                    "--rm",
                ]


@pytest.mark.parametrize(
    "base_version, tag, n_commits, status",
    [
        # OK, normal state
        ("1.2.4-0.dev", "1.2.3", 10, "ok"),
        # don't compare prereleases on the same tag
        ("1.2.3-0.dev", "1.2.3-alpha.1", 10, "ok"),
        # invalid baseVersion (not semver)
        ("x.y.z", "1.2.3", 10, "valid semver prerelease"),
        # not prerelease baseVersion
        ("1.2.4", "1.2.3", 10, "valid semver prerelease"),
        # check comparison with tag
        ("1.2.2-0.dev", "1.2.3-alpha.1", 10, "is not greater"),
        ("1.2.3-0.dev", "1.2.3", 10, "is not greater"),
        ("1.2.3-0.dev", "2.0.0", 10, "is not greater"),
        ("1.2.3-0.dev", "1.2.4-alpha.1", 10, "is not greater"),
        # don't check exactly on a tag
        ("1.2.3-0.dev", "2.0.0", 0, "ok"),
        # ignore invalid semver tags
        ("1.2.3-0.dev", "x.y.z", 10, "ok"),
    ],
)
def test_check_base_version(base_version, tag, n_commits, status):
    with mock.patch.object(
        chartpress, "_get_latest_tag_and_count", lambda: (tag, n_commits)
    ):
        if status == "ok":
            chartpress._check_base_version(base_version)
        else:
            with pytest.raises(ValueError) as exc:
                chartpress._check_base_version(base_version)
            assert status in str(exc)
            assert base_version in str(exc)
