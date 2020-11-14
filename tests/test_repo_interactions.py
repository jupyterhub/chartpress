import os
import sys

import chartpress


def test_git_repo_fixture(git_repo):
    # assert we use the git repo as our current working directory
    assert git_repo.working_dir == os.getcwd()

    # assert we have copied files
    assert os.path.isfile("chartpress.yaml")
    assert os.path.isfile("testchart/Chart.yaml")
    assert os.path.isfile("testchart/values.yaml")
    assert os.path.isfile("testchart/templates/configmap.yaml")
    assert os.path.isfile("image/Dockerfile")

    # assert there is another branch to contain published content as well
    git_repo.git.checkout("gh-pages")
    assert os.path.isfile("index.yaml")


def test_chartpress_run(git_repo, capfd):
    """Run chartpress and inspect the output."""

    # summarize information from git_repo
    sha = git_repo.commit("HEAD").hexsha[:7]
    tag = f"0.0.1-n001.h{sha}"

    # run chartpress
    out = _capture_output([], capfd)

    # verify image was built
    # verify the fallback tag of "0.0.1" when a tag is missing
    assert f"Successfully tagged testchart/testimage:{tag}" in out

    # verify the passing of static and dynamic --build-args
    assert f"--build-arg TEST_STATIC_BUILD_ARG=test" in out
    assert f"--build-arg TEST_DYNAMIC_BUILD_ARG={tag}-{sha}" in out

    # verify updates of Chart.yaml and values.yaml
    assert f"Updating testchart/Chart.yaml: version: {tag}" in out
    assert f"Updating testchart/values.yaml: image: testchart/testimage:{tag}" in out
    assert f"Updating testchart/values.yaml: list.0: testchart/testimage:{tag}" in out
    assert f"Updating testchart/values.yaml: list.1.image: testchart/testimage:{tag}" in out


    # verify usage of chartpress.yaml's resetVersion and resetTag
    out = _capture_output(["--reset"], capfd)
    assert f"Updating testchart/Chart.yaml: version: 0.0.1-test.reset.version" in out
    assert f"Updating testchart/values.yaml: image: testchart/testimage:test-reset-tag" in out


    # verify that we don't need to rebuild the image
    out = _capture_output([], capfd)
    assert f"Skipping build" in out


    # verify usage of --force-build
    out = _capture_output(["--force-build"], capfd)
    assert f"Successfully tagged" in out


    # verify usage --skip-build and --tag
    tag = "1.2.3-test.tag"
    out = _capture_output(["--skip-build", "--tag", tag], capfd)
    assert f"Successfully tagged" not in out
    assert f"Updating testchart/Chart.yaml: version: {tag}" in out
    assert f"Updating testchart/values.yaml: image: testchart/testimage:{tag}" in out


    # verify a real git tag is detected
    git_repo.create_tag(tag, message=tag)
    out = _capture_output(["--skip-build"], capfd)
    # This assertion verifies chartpress has considered the git tag by the fact
    # that no values required to be updated. No values should be updated as the
    # previous call with a provided --tag updated Chart.yaml and values.yaml
    # already.
    assert f"Updating" not in out


    # verify usage of --long
    out = _capture_output(["--skip-build", "--long"], capfd)
    assert f"Updating testchart/Chart.yaml: version: {tag}.n000.h{sha}" in out
    assert f"Updating testchart/values.yaml: image: testchart/testimage:{tag}.n000.h{sha}" in out


    # verify usage of --image-prefix
    out = _capture_output(["--skip-build", "--image-prefix", "test-prefix/"], capfd)
    assert f"Updating testchart/Chart.yaml: version: {tag}" in out
    assert f"Updating testchart/values.yaml: image: test-prefix/testimage:{tag}" in out


    # verify usage of --publish-chart and --extra-message
    out = _capture_output(
        [
            "--skip-build",
            "--publish-chart",
            "--extra-message", "test added --extra-message",
        ],
        capfd,
    )

    # verify output of --publish-chart
    assert "Branch 'gh-pages' set up to track remote branch 'gh-pages' from 'origin'." in out
    assert "Successfully packaged chart and saved it to:" in out
    assert f"/testchart-{tag}.tgz" in out

    # checkout gh-pages
    git_repo.git.stash()
    git_repo.git.checkout("gh-pages")

    # verify result of --publish-chart
    with open("index.yaml", "r") as f:
        index_yaml = f.read()
    print(index_yaml)
    assert f"version: 1.2.1" in index_yaml
    assert f"version: 1.2.2" in index_yaml
    assert f"version: {tag}" in index_yaml

    # verify result of --extra-message
    automatic_helm_chart_repo_commit = git_repo.commit("HEAD")
    assert "test added --extra-message" in automatic_helm_chart_repo_commit.message

    # return to master
    git_repo.git.checkout("master")
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
    assert f"Skipping chart publishing" in out



    # verify we don't overwrite the previous version when we make dev commits
    # and use --publish-chart and that we don't skip publishing
    open("extra-chart-path.txt", "w").close()
    git_repo.git.add(all=True)
    sha = git_repo.index.commit("Added extra-chart-path.txt").hexsha[:7]
    out = _capture_output(
        [
            "--skip-build",
            "--publish-chart",
        ],
        capfd,
    )

    # verify output of --publish-chart
    assert "Branch 'gh-pages' set up to track remote branch 'gh-pages' from 'origin'." in out
    assert "Successfully packaged chart and saved it to:" in out
    assert f"/testchart-{tag}.n001.h{sha}.tgz" in out
    assert f"Skipping chart publishing" not in out

    # checkout gh-pages
    git_repo.git.stash()
    git_repo.git.checkout("gh-pages")

    # verify result of --publish-chart
    with open("index.yaml", "r") as f:
        index_yaml = f.read()
    print("index_yaml follows:")
    print(index_yaml)
    print("-------------------")
    assert f"version: 1.2.1" in index_yaml
    assert f"version: 1.2.2" in index_yaml
    assert f"version: {tag}" in index_yaml
    assert f"version: {tag}.n001.h{sha}" in index_yaml

    # return to master
    git_repo.git.checkout("master")
    git_repo.git.stash("pop")


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
    tag = f"0.0.1-n002.h{sha}"
    out = _capture_output(["--skip-build"], capfd)
    assert f"Updating testchart/Chart.yaml: version: {tag}" not in out
    assert f"Updating testchart/values.yaml: image: testchart/testimage:{tag}" not in out


    # Add a file specified in the chart's paths configuration and verify
    # chartpress updated the Chart.yaml version, but not the image tags in
    # values.yaml.
    open("extra-chart-path.txt", "w").close()
    git_repo.git.add(all=True)
    sha = git_repo.index.commit("Added extra-chart-path.txt").hexsha[:7]
    tag = f"0.0.1-n003.h{sha}"
    out = _capture_output(["--skip-build"], capfd)
    assert f"Updating testchart/Chart.yaml: version: {tag}" in out
    assert f"Updating testchart/values.yaml: image: testchart/testimage:{tag}" not in out

    # Add a file specified in a chart image's paths configuration and verify
    # updates to Chart.yaml version as well as the image tags in values.yaml.
    open("extra-image-path.txt", "w").close()
    git_repo.git.add(all=True)
    sha = git_repo.index.commit("Added extra-image-path.txt").hexsha[:7]
    tag = f"0.0.1-n004.h{sha}"
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
    sha = r.heads.master.commit.hexsha[:7]
    tag = f"0.0.1-n002.h{sha}"

    out = _capture_output([], capfd)
    assert f"Updating testchart/Chart.yaml: version: {tag}" in out


def test_chartpress_run_alternative(git_repo_alternative, capfd):
    """
    Ensures that chartpress will run with an alternative configuration. This
    allow us to test against more kinds of configurations than we could squeeze
    into a single chartpress.yaml file.
    """
    r = git_repo_alternative
    sha = r.heads.master.commit.hexsha[:7]
    tag = f"0.0.1-n002.h{sha}"

    out = _capture_output([], capfd)
    assert f"Successfully tagged test-image-name-configuration:{tag}" in out


def _capture_output(args, capfd, expect_output=False):
    """
    Calls chartpress given provided arguments and captures the output during the
    call.
    """
    # clear cache of in memory cached functions
    # this allows us to better mimic the chartpress CLI behavior
    chartpress.image_needs_building.cache_clear()
    chartpress.image_needs_pushing.cache_clear()
    chartpress.latest_tag_or_mod_commit.cache_clear()

    # first flush past captured output, then run chartpress, and finally read
    # and save all output that came of it
    _, _ = capfd.readouterr()
    chartpress.main(args)
    out, err = capfd.readouterr()
    if not expect_output:
        assert out == ""

    # since the output was captured, print it back out again for debugging
    # purposes if a test fails for example
    header = f'--- chartpress {" ".join(args)} ---'
    footer = "-" * len(header)
    print()
    print(header)
    print("out:")
    print(out)
    print("err:")
    print(err, file=sys.stderr)
    print(footer)
    return err
