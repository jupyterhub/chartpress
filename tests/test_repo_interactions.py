import os
import subprocess
import sys

import pytest
from conftest import cache_clear

import chartpress
from chartpress import PRERELEASE_PREFIX, yaml


def check_version(tag):
    chartpress._fix_chart_version(tag, strict=True)


def test_git_repo_fixture(git_repo):
    # assert we use the git repo as our current working directory
    assert os.path.realpath(git_repo.working_dir) == os.path.realpath(os.getcwd())

    # assert we have copied files
    assert os.path.isfile("chartpress.yaml")
    assert os.path.isfile("testchart/Chart.yaml")
    assert os.path.isfile("testchart/values.yaml")
    assert os.path.isfile("testchart/templates/configmap.yaml")
    assert os.path.isfile("image/Dockerfile")

    # assert there is another branch to contain published content as well
    git_repo.git.checkout("gh-pages")
    assert os.path.isfile("index.yaml")


@pytest.mark.parametrize("base_version", [None, "0.0.1-0.dev"])
def test_chartpress_run(git_repo, capfd, base_version):
    """Run chartpress and inspect the output."""

    with open("chartpress.yaml") as f:
        chartpress_config = yaml.load(f)

    chart = chartpress_config["charts"][0]
    if base_version:
        chart["baseVersion"] = base_version
        with open("chartpress.yaml", "w") as f:
            yaml.dump(chartpress_config, f)

    # summarize information from git_repo
    sha = git_repo.commit("HEAD").hexsha[:7]
    tag = f"0.0.1-{PRERELEASE_PREFIX}.1.h{sha}"
    branch = "main"
    check_version(tag)

    # run chartpress
    out = _capture_output([], capfd)
    print(out)
    # verify image was built
    # verify the fallback tag of "0.0.1" when a tag is missing
    assert (
        f"Successfully tagged testchart/testimage:{tag}" in out
        or f"naming to docker.io/testchart/testimage:{tag} in out"
    )

    # verify the passing of static and dynamic --build-args
    assert "--build-arg TEST_STATIC_BUILD_ARG=test" in out
    assert f"--build-arg TEST_DYNAMIC_BUILD_ARG={tag}-{sha}-{branch}" in out

    # verify updates of Chart.yaml and values.yaml
    assert f"Updating testchart/Chart.yaml: version: {tag}" in out
    assert f"Updating testchart/values.yaml: image: testchart/testimage:{tag}" in out
    assert f"Updating testchart/values.yaml: list.0: testchart/testimage:{tag}" in out
    assert (
        f"Updating testchart/values.yaml: list.1.image: testchart/testimage:{tag}"
        in out
    )

    # verify usage of chartpress.yaml's resetVersion and resetTag
    reset_version = chart["resetVersion"]
    reset_tag = chart["resetTag"]
    out = _capture_output(["--reset"], capfd)
    assert f"Updating testchart/Chart.yaml: version: {reset_version}" in out
    assert (
        f"Updating testchart/values.yaml: image: testchart/testimage:{reset_tag}" in out
    )

    # verify that we don't need to rebuild the image
    out = _capture_output([], capfd)
    assert "Skipping build" in out

    # verify usage of --force-build
    out = _capture_output(["--force-build"], capfd)
    assert "Successfully tagged" in out or "naming to" in out

    # verify usage --skip-build and --tag
    tag = "1.2.3-test.tag"
    out = _capture_output(["--skip-build", "--tag", tag], capfd)
    assert "Successfully tagged" not in out or "naming to" in out
    assert f"Updating testchart/Chart.yaml: version: {tag}" in out
    assert f"Updating testchart/values.yaml: image: testchart/testimage:{tag}" in out

    # verify a real git tag is detected
    git_repo.create_tag(tag, message=tag)
    out = _capture_output(["--skip-build"], capfd)

    # This assertion verifies chartpress has considered the git tag by the fact
    # that no values required to be updated. No values should be updated as the
    # previous call with a provided --tag updated Chart.yaml and values.yaml
    # already.
    assert "Updating" not in out

    # Run again, but from a clean repo (versions in git don't match tag)
    # Should produce the same result
    git_repo.git.checkout(tag, "--", "testchart")
    out = _capture_output(["--skip-build"], capfd)
    assert f"Updating testchart/Chart.yaml: version: {tag}\n" in out
    assert f"Updating testchart/values.yaml: image: testchart/testimage:{tag}\n" in out

    # verify usage of --long
    out = _capture_output(["--skip-build", "--long"], capfd)
    assert f"Updating testchart/Chart.yaml: version: {tag}.git.1.h{sha}" in out
    assert (
        f"Updating testchart/values.yaml: image: testchart/testimage:{tag}.git.1.h{sha}"
        in out
    )

    # verify usage of --image-prefix
    out = _capture_output(["--skip-build", "--image-prefix", "test-prefix/"], capfd)
    assert f"Updating testchart/Chart.yaml: version: {tag}" in out
    assert f"Updating testchart/values.yaml: image: test-prefix/testimage:{tag}" in out

    # verify usage of --publish-chart and --extra-message
    out = _capture_output(
        [
            "--skip-build",
            "--publish-chart",
            "--extra-message",
            "test added --extra-message",
        ],
        capfd,
    )

    # verify output of --publish-chart
    assert "'gh-pages' set up to track" in out
    assert "Successfully packaged chart and saved it to:" in out
    assert f"/testchart-{tag}.tgz" in out

    # checkout gh-pages
    git_repo.git.stash()
    git_repo.git.checkout("gh-pages")

    # verify result of --publish-chart
    with open("index.yaml") as f:
        index_yaml = f.read()
    print(index_yaml)
    assert "version: 1.2.1" in index_yaml
    assert "version: 1.2.2" in index_yaml
    assert f"version: {tag}" in index_yaml

    # verify result of --extra-message
    automatic_helm_chart_repo_commit = git_repo.commit("HEAD")
    assert "test added --extra-message" in automatic_helm_chart_repo_commit.message

    # return to main
    git_repo.git.checkout("main")
    git_repo.git.stash("pop")

    # verify usage of --publish-chart when the chart version exists in the chart
    # repo already
    out = _capture_output(
        [
            "--skip-build",
            "--publish-chart",
        ],
        capfd,
    )
    # verify output of --publish-chart
    assert "Skipping chart publishing" in out

    # verify usage of --force-publish-chart when the chart version exists in the
    # chart repo already
    out = _capture_output(
        [
            "--skip-build",
            "--force-publish-chart",
        ],
        capfd,
    )
    # verify output of --force-publish-chart
    assert "already exists, overwriting it" in out

    # verify we don't overwrite the previous version when we make dev commits
    # and use --publish-chart and that we don't skip publishing
    with open("extra-chart-path.txt", "w"):
        pass
    git_repo.git.add(all=True)
    sha = git_repo.index.commit("Added extra-chart-path.txt").hexsha[:7]

    # Verify that baseVersion is validated after a tag
    if base_version:
        with pytest.raises(ValueError):
            out = _capture_output(
                [
                    "--skip-build",
                ],
                capfd,
            )
        with pytest.raises(ValueError):
            out = _capture_output(
                [
                    "--reset",
                ],
                capfd,
            )
        # update baseVersion
        chart["baseVersion"] = next_tag = "1.2.4-0.dev"
        with open("chartpress.yaml", "w") as f:
            yaml.dump(chartpress_config, f)
    else:
        next_tag = tag

    out = _capture_output(
        [
            "--skip-build",
            "--publish-chart",
        ],
        capfd,
    )

    # verify output of --publish-chart
    assert "'gh-pages' set up to track" in out
    assert "Successfully packaged chart and saved it to:" in out
    assert f"/testchart-{next_tag}.git.2.h{sha}.tgz" in out
    assert "Skipping chart publishing" not in out

    # checkout gh-pages
    git_repo.git.stash()
    git_repo.git.checkout("gh-pages")

    # verify result of --publish-chart
    with open("index.yaml") as f:
        index_yaml = f.read()
    print("index_yaml follows:")
    print(index_yaml)
    print("-------------------")
    assert "version: 1.2.1" in index_yaml
    assert "version: 1.2.2" in index_yaml
    assert f"version: {tag}" in index_yaml
    assert f"version: {next_tag}.git.2.h{sha}" in index_yaml

    # return to main
    git_repo.git.checkout("main")
    git_repo.git.stash("pop")


def test_tbump_release(git_repo, git_repo_base_version, capfd):
    """Run through tagging"""

    def get_base_version():
        """Get baseVersion config from chartpress.yaml"""
        with open("chartpress.yaml") as f:
            chartpress_config = yaml.load(f)

        chart = chartpress_config["charts"][0]
        return chart["baseVersion"]

    def get_chart_version():
        """Get the current version in Chart.yaml"""
        with open("testchart/Chart.yaml") as f:
            chart = yaml.load(f)
        return chart["version"]

    # run chartpress with --no-build and any additional arguments
    def run_chartpress(args=None):
        """run chartpress with --no-build and any additional arguments"""
        if args is None:
            args = []
        if args != ["--reset"]:
            args = ["--no-build"] + args
        out = _capture_output(args, capfd)
        print(out)
        return out

    def tbump(args):
        """Run tbump with args"""
        subprocess.run(["git", "status"])
        proc = subprocess.run(
            ["tbump", "--non-interactive", "--no-push"] + args,
            capture_output=True,
            text=True,
        )
        # echo output before checking return code
        # so we see it on errors
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        assert proc.returncode == 0
        # increment commit count because tbump makes a commit
        nonlocal n
        n += 1
        return proc.stdout, proc.stderr

    base_version = get_base_version()
    assert base_version == "1.0.0-0.dev"

    # summarize information from git_repo
    sha = git_repo.commit("HEAD").hexsha[:7]
    n = chartpress._count_commits(sha)
    tag = f"{base_version}.git.{n}.h{sha}"
    run_chartpress()
    assert get_chart_version() == tag

    # tag a prerelease
    run_chartpress(["--reset"])
    version = "1.0.0-beta.1"
    with open("chartpress.yaml") as f:
        print(f.read())
    tbump([version])
    base_version = get_base_version()
    assert base_version == version

    # reset passes
    run_chartpress(["--reset"])
    # after chartpress, version is correct (no suffix)
    run_chartpress()
    assert get_chart_version() == version

    extra_chart_path = "extra-chart-path.txt"
    # add a commit
    with open(extra_chart_path, "w") as f:
        f.write("first")

    git_repo.git.add(extra_chart_path)
    sha = git_repo.index.commit("Added commit").hexsha[:7]
    n += 1  # added a commit
    tag = f"{base_version}.git.{n}.h{sha}"

    # reset passes
    run_chartpress(["--reset"])
    # after chartpress, version is correct (with suffix)
    run_chartpress()
    assert get_chart_version() == tag

    # tag a final release
    run_chartpress(["--reset"])
    version = "1.0.0"
    tbump([version])
    base_version = get_base_version()

    # reset passes
    run_chartpress(["--reset"])

    # chartpress gets tag version
    run_chartpress()
    assert get_chart_version() == version

    # reset before making a commit
    run_chartpress(["--reset"])

    # Add a commit (without bumping baseVersion)
    with open(extra_chart_path, "w") as f:
        f.write("second")

    git_repo.git.add(extra_chart_path)
    sha = git_repo.index.commit("Added commit").hexsha[:7]
    n += 1  # added a commit

    # reset balks because baseVersion hasn't been updated
    with pytest.raises(ValueError, match="not greater than latest tag"):
        run_chartpress(["--reset"])

    # tbump next dev release (the last step of making a stable release)
    base_version = "1.1.0-0.dev"
    tbump(["--no-tag", base_version])

    assert get_base_version() == base_version
    # reset is happy now
    run_chartpress(["--reset"])

    # final chartpress render
    run_chartpress()
    sha = git_repo.heads.main.commit.hexsha[:7]
    tag = f"{base_version}.git.{n}.h{sha}"
    assert get_chart_version() == tag


def test_chartpress_paths_configuration(git_repo, capfd):
    """
    Background:
    - A helm chart resides in a directory with the name of the chart. This kind
      of directory will contain Chart.yaml, values.yaml, and the templates
      folder for example.
    - chartpress.yaml is meant to reside in a parent directory to helm chart
      directories.

    By default, the Chart.yaml's version field should only be updated if
    anything within its folder has changed, but also if any of the chart's
    images are being updated when running chartpress.

    This default can be augmented by paths configuration in chartpress.yaml.
    These additional paths are relative to the chartpress.yaml location, which
    must be in the parent folder of the charts.

    This test verifies the statements above.
    """

    # Add a file outside the chart repo and verify chartpress didn't update the
    # Chart.yaml version or the image tags in values.yaml.
    open("not-in-paths.txt", "w").close()
    git_repo.git.add(all=True)
    sha = git_repo.index.commit("Added not-in-paths.txt").hexsha[:7]
    tag = f"0.0.1-{PRERELEASE_PREFIX}.2.h{sha}"
    check_version(tag)
    out = _capture_output(["--skip-build"], capfd)
    assert f"Updating testchart/Chart.yaml: version: {tag}" not in out
    assert (
        f"Updating testchart/values.yaml: image: testchart/testimage:{tag}" not in out
    )

    # Add a file specified in the chart's paths configuration and verify
    # chartpress updated the Chart.yaml version, but not the image tags in
    # values.yaml.
    open("extra-chart-path.txt", "w").close()
    git_repo.git.add(all=True)
    sha = git_repo.index.commit("Added extra-chart-path.txt").hexsha[:7]
    tag = f"0.0.1-{PRERELEASE_PREFIX}.3.h{sha}"
    check_version(tag)
    out = _capture_output(["--skip-build"], capfd)
    assert f"Updating testchart/Chart.yaml: version: {tag}" in out
    assert (
        f"Updating testchart/values.yaml: image: testchart/testimage:{tag}" not in out
    )

    # Add a file specified in a chart image's paths configuration and verify
    # updates to Chart.yaml version as well as the image tags in values.yaml.
    open("extra-image-path.txt", "w").close()
    git_repo.git.add(all=True)
    sha = git_repo.index.commit("Added extra-image-path.txt").hexsha[:7]
    tag = f"0.0.1-{PRERELEASE_PREFIX}.4.h{sha}"
    check_version(tag)
    out = _capture_output(["--skip-build"], capfd)
    assert f"Updating testchart/Chart.yaml: version: {tag}" in out
    assert f"Updating testchart/values.yaml: image: testchart/testimage:{tag}" in out


def test_chartpress_run_bare_minimum(git_repo_bare_minimum, capfd):
    """
    Ensures that chartpress will run with a minimal configuration of only
    providing a single chart name. This can catch errors that assumes we need to
    have a images key in the chartpress.yaml configuration for example.
    """
    r = git_repo_bare_minimum
    sha = r.heads.main.commit.hexsha[:7]
    tag = f"0.0.1-{PRERELEASE_PREFIX}.2.h{sha}"
    check_version(tag)
    out = _capture_output([], capfd)
    assert f"Updating testchart/Chart.yaml: version: {tag}" in out


@pytest.mark.skipif(os.environ.get("HELM2") == "helm2", reason="Skipping helm 2")
def test_chartpress_run_alternative(git_repo_alternative, capfd):
    """
    Ensures that chartpress will run with an alternative configuration. This
    allow us to test against more kinds of configurations than we could squeeze
    into a single chartpress.yaml file, including:
    - chart name != chart directory name
    """
    r = git_repo_alternative
    sha = r.heads.main.commit.hexsha[:7]

    # verify usage of --tag with a prefix v
    tag = "v1.0.0"
    check_version(tag)

    out = _capture_output(["--skip-build", "--tag", tag, "--publish-chart"], capfd)
    assert f"Updating subdir/chart/Chart.yaml: version: {tag[1:]}" in out
    assert f"Updating subdir/chart/values.yaml: image: alternativeimage:{tag}" in out

    gh_pages = r.heads["gh-pages"].commit.tree
    expected_files = sorted(b.name for b in gh_pages.blobs)
    assert expected_files == ["alternative-1.0.0.tgz", "index.yaml"]


def _capture_output(args, capfd, expect_output=False):
    """
    Calls chartpress given provided arguments and captures the output during the
    call.
    """
    # clear cache of in memory cached functions
    # this allows us to better mimic the chartpress CLI behavior
    cache_clear()

    # first flush past captured output, then run chartpress, and finally read
    # and save all output that came of it
    _, _ = capfd.readouterr()
    chartpress.main(args)
    out, err = capfd.readouterr()
    if not expect_output:
        assert out == ""

    return err


def test_dev_tag(git_repo_dev_tag, capfd):
    r = git_repo_dev_tag
    out = _capture_output(["--skip-build"], capfd)
    sha = r.heads.main.commit.hexsha[:7]
    with open("testchart/Chart.yaml") as f:
        chart = yaml.load(f)

    tag = f"2.0.0-dev.git.3.h{sha}"
    assert chart["version"] == tag
    check_version(tag)


def test_backport_branch(git_repo_backport_branch, capfd):
    r = git_repo_backport_branch
    out = _capture_output(["--skip-build"], capfd)
    sha = r.heads["1.x"].commit.hexsha[:7]
    with open("testchart/Chart.yaml") as f:
        chart = yaml.load(f)

    tag = f"1.0.1-{PRERELEASE_PREFIX}.3.h{sha}"
    assert chart["version"] == tag
    check_version(tag)


def test_reset(git_repo, capfd):
    chartpress_yaml = "chartpress.yaml"
    chart_yaml = "testchart/Chart.yaml"
    values_yaml = "testchart/values.yaml"

    with open(chartpress_yaml) as f:
        cfg = yaml.load(f)
    chart_cfg = cfg["charts"][0]

    out = _capture_output(["--reset"], capfd)
    sys.stdout.write(out)

    with open(chart_yaml) as f:
        chart = yaml.load(f)
    assert chart["version"] == chart_cfg["resetVersion"]

    with open(values_yaml) as f:
        values = yaml.load(f)

    expected_tag = chart_cfg["resetTag"]

    assert values["image"] == f"testchart/testimage:{expected_tag}"


def test_reset_exclusive(git_repo, capfd):
    with pytest.raises(SystemExit):
        chartpress.main(["--reset", "--tag", "1.2.3"])
    out, err = capfd.readouterr()
    assert "no additional arguments" in err
