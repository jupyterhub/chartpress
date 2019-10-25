import os

import chartpress

def test_git_repo_fixture(git_repo):
    # assert we use the git repo as our current working directory
    assert git_repo.working_dir == os.getcwd()

    # assert we have copied files
    assert os.path.isfile("chartpress.yaml")
    assert os.path.isfile("testchart/Chart.yaml")
    assert os.path.isfile("testchart/values.yaml")

    # assert there is another branch to contain published content as well
    git_repo.git.checkout("gh-pages")
    assert os.path.isfile("index.yaml")


def test_chartpress_run(git_repo, capfd):
    """Run chartpress and inspect the output."""

    # summarize information from git_repo
    sha = git_repo.commit("HEAD").hexsha[:7]
    tag = f"0.0.1-001.{sha}"

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
    assert f"Updating testchart/values.yaml: list.0: testchart/testimage:test-reset-tag" in out
    assert f"Updating testchart/values.yaml: list.1.image: testchart/testimage:test-reset-tag" in out


    # clear cache of image_needs_building
    # ref: https://docs.python.org/3/library/functools.html#functools.lru_cache
    chartpress.image_needs_building.cache_clear()


    # verify that we don't need to rebuild the image
    out = _capture_output([], capfd)
    assert f"Skipping build" in out


    # verify usage --skip-build and --tag
    tag = "1.2.3-test.tag"
    out = _capture_output(["--skip-build", "--tag", tag], capfd)
    assert f"Successfully tagged" not in out
    assert f"Updating testchart/Chart.yaml: version: {tag}" in out
    assert f"Updating testchart/values.yaml: image: testchart/testimage:{tag}" in out
    assert f"Updating testchart/values.yaml: list.0: testchart/testimage:{tag}" in out
    assert f"Updating testchart/values.yaml: list.1.image: testchart/testimage:{tag}" in out


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
    assert f"Updating testchart/Chart.yaml: version: {tag}.000.{sha}" in out
    assert f"Updating testchart/values.yaml: image: testchart/testimage:{tag}.000.{sha}" in out
    assert f"Updating testchart/values.yaml: list.0: testchart/testimage:{tag}.000.{sha}" in out
    assert f"Updating testchart/values.yaml: list.1.image: testchart/testimage:{tag}.000.{sha}" in out


    # verify usage of --image-prefix
    out = _capture_output(["--skip-build", "--image-prefix", "test-prefix/"], capfd)
    assert f"Updating testchart/Chart.yaml: version: {tag}" in out
    assert f"Updating testchart/values.yaml: image: test-prefix/testimage:{tag}" in out
    assert f"Updating testchart/values.yaml: list.0: test-prefix/testimage:{tag}" in out
    assert f"Updating testchart/values.yaml: list.1.image: test-prefix/testimage:{tag}" in out


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

    git_repo.git.checkout("master")
    git_repo.git.stash("pop")


    # verify we don't overwrite the previous version when we make dev commits
    # and use --publish-chart
    open("extra-path.txt", "w").close()
    git_repo.git.add(all=True)
    sha = git_repo.index.commit("Added extra-path.txt").hexsha[:7]
    chartpress.latest_tag_or_mod_commit.cache_clear()
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
    assert f"/testchart-{tag}.001.{sha}.tgz" in out

    git_repo.git.stash()
    git_repo.git.checkout("gh-pages")

    # verify result of --publish-chart
    with open("index.yaml", "r") as f:
        index_yaml = f.read()
    print(index_yaml)
    assert f"version: 1.2.1" in index_yaml
    assert f"version: 1.2.2" in index_yaml
    assert f"version: {tag}" in index_yaml
    assert f"version: {tag}.001.{sha}" in index_yaml

    git_repo.git.checkout("master")
    git_repo.git.stash("pop")


def _capture_output(args, capfd):
    _, _ = capfd.readouterr()
    chartpress.main(args)
    out, err = capfd.readouterr()
    header = f'--- chartpress {" ".join(args)} ---'
    footer = "-" * len(header)
    print()
    print(header)
    print(out)
    print(footer)
    return out
