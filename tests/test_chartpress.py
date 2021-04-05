import json
import sys
from subprocess import PIPE
from subprocess import run
from urllib.request import urlopen


def test_list_images(git_repo):
    p = run(
        [sys.executable, "-m", "chartpress", "--list-images"],
        check=True,
        stdout=PIPE,
        stderr=PIPE,
    )
    stdout = p.stdout.decode("utf8").strip()
    # echo stdout/stderr for debugging
    sys.stderr.write(p.stderr.decode("utf8", "replace"))
    sys.stdout.write(stdout)

    images = stdout.strip().splitlines()
    assert len(images) == 1
    # split hash_suffix which will be different every run
    pre_hash, hash_suffix = images[0].rsplit(".", 1)
    assert pre_hash == "testchart/testimage:0.0.1-n001"

    p = run(
        ["git", "status", "--porcelain"],
        check=True,
        stdout=PIPE,
        stderr=PIPE,
    )
    assert not p.stdout, "--list-images should not make changes!"


def test_buildx(git_repo):
    p = run(
        [
            sys.executable,
            "-m",
            "chartpress",
            "--builder",
            "docker-buildx",
            "--platform",
            "linux/amd64",
            "--platform",
            "linux/arm64",
            "--platform",
            "linux/ppc64le",
            "--push",
            "--image-prefix",
            "localhost:5000/test-buildx/",
            "--tag",
            "1.2.3-abc",
        ],
        check=True,
        stdout=PIPE,
        stderr=PIPE,
    )
    stdout = p.stdout.decode("utf8").strip()
    stderr = p.stderr.decode("utf8").strip()
    # echo stdout/stderr for debugging
    sys.stderr.write(stderr)
    sys.stdout.write(stdout)

    assert "[linux/amd64 1/1] FROM docker.io/library/alpine@" in stderr
    assert "[linux/arm64 1/1] FROM docker.io/library/alpine@" in stderr
    assert "[linux/ppc64le 1/1] FROM docker.io/library/alpine@" in stderr
    assert (
        "pushing manifest for localhost:5000/test-buildx/testimage:1.2.3-abc" in stderr
    )

    with urlopen("http://localhost:5000/v2/test-buildx/testimage/tags/list") as h:
        d = json.load(h)
    assert d == {"name": "test-buildx/testimage", "tags": ["1.2.3-abc"]}
