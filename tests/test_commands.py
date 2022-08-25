# Unit tests for some chartpress methods
from os import mkdir

import pytest
from ruamel.yaml import YAML

import chartpress
from chartpress import PRERELEASE_PREFIX


@pytest.mark.parametrize("with_args", [False, True])
def test_build_image(mock_check_call, with_args):
    image_spec = "index.docker.io/library/ubuntu:latest"
    context_path = "dir"
    dockerfile_path = None
    build_args = None

    if with_args:
        dockerfile_path = "Dockerfile.custom"
        # Ensure dict is ordered
        build_args = {"arg": "value"}
        build_args["b"] = 2

    chartpress.build_image(image_spec, context_path, dockerfile_path, build_args)

    assert len(mock_check_call.commands) == 1
    if with_args:
        assert mock_check_call.commands[0] == (
            [
                "docker",
                "build",
                "-t",
                image_spec,
                context_path,
                "-f",
                "Dockerfile.custom",
                "--build-arg",
                "arg=value",
                "--build-arg",
                "b=2",
            ],
            {},
        )
    else:
        assert mock_check_call.commands[0] == (
            [
                "docker",
                "build",
                "-t",
                image_spec,
                context_path,
            ],
            {},
        )


@pytest.mark.parametrize("with_opts", [False, True])
def test_build_image_with_options(git_repo, mock_check_call, with_opts):
    image_spec = "index.docker.io/library/ubuntu:latest"
    context_path = "dir"
    dockerfile_path = None
    build_args = None
    extra_build_command_options = None

    if with_opts:
        dockerfile_path = "Dockerfile.custom"
        extra_build_command_options = [
            "--label=maintainer=octocat",
            "--label",
            "ref=tag-sha",
            "--rm",
        ]

    chartpress.build_image(
        image_spec,
        context_path,
        dockerfile_path,
        build_args,
        extra_build_command_options,
    )

    assert len(mock_check_call.commands) == 1
    if with_opts:
        sha = git_repo.commit(git_repo.head).hexsha
        assert mock_check_call.commands[0] == (
            [
                "docker",
                "build",
                "-t",
                image_spec,
                context_path,
                "-f",
                "Dockerfile.custom",
                "--label=maintainer=octocat",
                "--label",
                "ref=tag-sha",
                "--rm",
            ],
            {},
        )
    else:
        assert mock_check_call.commands[0] == (
            [
                "docker",
                "build",
                "-t",
                image_spec,
                context_path,
            ],
            {},
        )


@pytest.mark.parametrize("push", [False, True])
@pytest.mark.parametrize("tag", [None, "1.2.3"])
def test_build_images(git_repo, mock_check_call, push, tag):
    prefix = "pre/"
    images = {
        "testimage": {
            "buildArgs": {
                "arg": "test",
            },
            "contextPath": "image",
            "dockerfilePath": "image/Dockerfile",
        },
    }
    images["imageName"] = {
        "imageName": "custom-name",
    }

    chartpress.build_images(
        prefix, images, tag=tag, force_build=True, push=push, force_push=push
    )
    sha = git_repo.commit(git_repo.head).hexsha

    if tag:
        expected_tag = tag
    else:
        expected_tag = f"0.0.1-{PRERELEASE_PREFIX}.1.h{sha[:7]}"

    expected_build1 = [
        "docker",
        "build",
        "-t",
        f"pre/testimage:{expected_tag}",
        "image",
        "-f",
        "image/Dockerfile",
        "--build-arg",
        "arg=test",
    ]
    expected_build2 = [
        "docker",
        "build",
        "-t",
        f"custom-name:{expected_tag}",
        "images/imageName",
        "-f",
        "images/imageName/Dockerfile",
    ]

    expected_push1 = ["docker", "push", f"pre/testimage:{expected_tag}"]
    expected_push2 = ["docker", "push", f"custom-name:{expected_tag}"]

    if push:
        assert len(mock_check_call.commands) == 4
        assert mock_check_call.commands[0] == (expected_build1, {})
        assert mock_check_call.commands[1] == (expected_push1, {})
        assert mock_check_call.commands[2] == (expected_build2, {})
        assert mock_check_call.commands[3] == (expected_push2, {})
    else:
        assert len(mock_check_call.commands) == 2
        assert mock_check_call.commands[0] == (expected_build1, {})
        assert mock_check_call.commands[1] == (expected_build2, {})


@pytest.mark.parametrize("tag", [None, "1.2.3"])
@pytest.mark.parametrize(
    ("push", "platforms", "expected_suffix"),
    [
        (False, None, ["--load"]),
        (True, None, ["--push"]),
        (False, ["linux/amd64"], ["--platform", "linux/amd64", "--load"]),
        (True, ["linux/amd64"], ["--platform", "linux/amd64", "--push"]),
        (
            False,
            ["linux/amd64", "linux/arm64"],
            ["--platform", "linux/amd64,linux/arm64"],
        ),
        (
            True,
            ["linux/amd64", "linux/arm64"],
            ["--platform", "linux/amd64,linux/arm64", "--push"],
        ),
    ],
)
def test_buildx_images(
    git_repo, mock_check_call, tag, push, platforms, expected_suffix
):
    prefix = "pre/"
    images = {
        "testimage": {
            "buildArgs": {
                "arg": "test",
            },
            "contextPath": "image",
            "dockerfilePath": "image/Dockerfile",
        },
    }
    images["imageName"] = {
        "imageName": "custom-name",
    }

    chartpress.build_images(
        prefix,
        images,
        tag=tag,
        force_build=True,
        push=push,
        force_push=push,
        builder=chartpress.Builder.DOCKER_BUILDX,
        platforms=platforms,
    )
    sha = git_repo.commit(git_repo.head).hexsha

    if tag:
        expected_tag = tag
    else:
        expected_tag = f"0.0.1-{PRERELEASE_PREFIX}.1.h{sha[:7]}"

    expected_build1 = [
        "docker",
        "buildx",
        "build",
        "--progress",
        "plain",
        "-t",
        f"pre/testimage:{expected_tag}",
        "image",
        "-f",
        "image/Dockerfile",
        "--build-arg",
        "arg=test",
    ] + expected_suffix
    expected_build2 = [
        "docker",
        "buildx",
        "build",
        "--progress",
        "plain",
        "-t",
        f"custom-name:{expected_tag}",
        "images/imageName",
        "-f",
        "images/imageName/Dockerfile",
    ] + expected_suffix

    assert len(mock_check_call.commands) == 2
    assert mock_check_call.commands[0] == (expected_build1, {})
    assert mock_check_call.commands[1] == (expected_build2, {})


@pytest.mark.parametrize(
    ("platforms", "expected_suffix"),
    [
        (None, ["--load"]),
        (["linux/amd64"], ["--platform", "linux/amd64", "--load"]),
        (
            ["linux/amd64", "linux/arm64"],
            ["--platform", "linux/amd64", "--load"],
        ),
        (
            ["linux/arm64"],
            None,
        ),
    ],
)
def test_buildx_images_skipplatforms(
    git_repo, mock_check_call, platforms, expected_suffix
):
    tag = "1.2.3"
    prefix = "pre/"
    images = {
        "testimage": {
            "contextPath": "image",
            "skipPlatforms": ["linux/arm64"],
        },
    }

    chartpress.build_images(
        prefix,
        images,
        tag=tag,
        force_build=True,
        builder=chartpress.Builder.DOCKER_BUILDX,
        platforms=platforms,
    )

    if expected_suffix:
        expected_build = [
            "docker",
            "buildx",
            "build",
            "--progress",
            "plain",
            "-t",
            f"pre/testimage:{tag}",
            "image",
            "-f",
            "image/Dockerfile",
        ] + expected_suffix

        assert len(mock_check_call.commands) == 1
        assert mock_check_call.commands[0] == (expected_build, {})
    else:
        assert len(mock_check_call.commands) == 0


@pytest.mark.parametrize("version", [None, "1.2.3"])
def test_build_chart(git_repo, mock_check_call, version):
    yaml = YAML()

    sha = git_repo.commit(git_repo.head).hexsha
    mkdir("chart")
    with open("chart/Chart.yaml", "w") as f:
        yaml.dump({"version": "0", "name": "test-chart"}, f)

    rv = chartpress.build_chart("chart", version=version, paths=[])

    if version:
        expected_version = version
    else:
        expected_version = f"0.0.1-{PRERELEASE_PREFIX}.1.h{sha[:7]}"

    assert rv == expected_version

    with open("chart/Chart.yaml") as f:
        chart = yaml.load(f)
    assert chart == {"name": "test-chart", "version": expected_version}
    assert len(mock_check_call.commands) == 0


def test_publish_pages(git_repo, mock_check_call):
    chartpress.publish_pages(
        "test-chart",
        "1.2.3",
        "jupyterhub/chartpress",
        "https://example.org/chartpress",
        "<foo>",
    )

    assert mock_check_call.commands[0] == (
        [
            "git",
            "clone",
            "--no-checkout",
            "git@github.com:jupyterhub/chartpress",
            "test-chart-1.2.3",
        ],
        {"echo": True},
    )
    assert mock_check_call.commands[1] == (
        ["git", "checkout", "gh-pages"],
        {"cwd": "test-chart-1.2.3", "echo": True},
    )

    helm_package_cmd = mock_check_call.commands[2][0]
    assert mock_check_call.commands[2][1] == {}
    # Skip the temporary directory
    assert (helm_package_cmd[:5] + helm_package_cmd[6:]) == [
        "helm",
        "package",
        "test-chart",
        "--dependency-update",
        "--destination",
    ]

    helm_index_cmd = mock_check_call.commands[3][0]
    assert mock_check_call.commands[3][1] == {}
    # Skip the temporary directory
    assert (helm_index_cmd[:3] + helm_index_cmd[4:]) == [
        "helm",
        "repo",
        "index",
        "--url",
        "https://example.org/chartpress",
        "--merge",
        "test-chart-1.2.3/index.yaml",
    ]

    assert mock_check_call.commands[4] == (
        ["git", "add", "."],
        {"cwd": "test-chart-1.2.3"},
    )
    assert mock_check_call.commands[5] == (
        [
            "git",
            "commit",
            "-m",
            "[test-chart] Automatic update for commit 1.2.3\n\n<foo>",
        ],
        {"cwd": "test-chart-1.2.3"},
    )
    assert mock_check_call.commands[6] == (
        ["git", "push", "origin", "gh-pages"],
        {"cwd": "test-chart-1.2.3"},
    )
