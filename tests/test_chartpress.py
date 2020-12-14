import sys
from subprocess import run, PIPE


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
