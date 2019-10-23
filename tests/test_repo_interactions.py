import os

import chartpress

def test_git_repo_fixture(git_repo):
    assert git_repo.working_dir == os.getcwd()
    assert os.path.isfile("chartpress.yaml")
    assert os.path.isfile("testchart/Chart.yaml")
    assert os.path.isfile("testchart/values.yaml")


def test_chartpress_run(git_repo, capfd):
    """Run chartpress and inspect the output."""

    # run chartpress on initial commit
    _, _ = capfd.readouterr()
    chartpress.main([])
    out, err = capfd.readouterr()
    print()
    print("--- chartpress ---")
    print(out)
    print("------------------")

    sha = git_repo.commit("HEAD").hexsha[:7]
    tag = f"0.0.1-001.{sha}"
    
    # verify image was built
    # verify the fallback tag of "0.0.1" when a tag is missing
    assert f"Successfully tagged testchart/testimage:{tag}"

    # verify the passing of static and dynamic --build-args
    assert f"--build-arg TEST_STATIC_BUILD_ARG=test" in out
    assert f"--build-arg TEST_DYNAMIC_BUILD_ARG={tag}-{sha}" in out

    # verify updates of Chart.yaml and values.yaml
    assert f"Updating testchart/Chart.yaml: version: {tag}" in out
    assert f"Updating testchart/values.yaml: image: testchart/testimage:{tag}" in out
    assert f"Updating testchart/values.yaml: list.0: testchart/testimage:{tag}" in out
    assert f"Updating testchart/values.yaml: list.1.image: testchart/testimage:{tag}" in out

    _, _ = capfd.readouterr()
    chartpress.main(["--reset"])
    out, err = capfd.readouterr()
    print()
    print('--- chartpress --reset ---')
    print(out)
    print("--------------------------")

    # verify usage of chartpress.yaml's resetVersion and resetTag
    assert f"Updating testchart/Chart.yaml: version: 0.0.1-test.reset.version" in out
    assert f"Updating testchart/values.yaml: image: testchart/testimage:test-reset-tag" in out
    assert f"Updating testchart/values.yaml: list.0: testchart/testimage:test-reset-tag" in out
    assert f"Updating testchart/values.yaml: list.1.image: testchart/testimage:test-reset-tag" in out

    _, _ = capfd.readouterr()
    chartpress.main([])
    out, err = capfd.readouterr()
    print()
    print('--- chartpress ---')
    print(out)
    print("------------------")

    # verify that we don't need to rebuild the image
    assert f"Skipping build" in out

    _, _ = capfd.readouterr()
    chartpress.main(["--skip-build", "--tag", "1.2.3-test.tag"])
    out, err = capfd.readouterr()
    print()
    print('--- chartpress --skip-build --tag 1.2.3-test.tag ---')
    print(out)
    print("----------------------------------------------------")

    # verify usage --skip-build (this string from docker's output)
    assert f"Successfully tagged" not in out

    # verify usage of --tag
    assert f"Updating testchart/Chart.yaml: version: 1.2.3-test.tag" in out
    assert f"Updating testchart/values.yaml: image: testchart/testimage:1.2.3-test.tag" in out
    assert f"Updating testchart/values.yaml: list.0: testchart/testimage:1.2.3-test.tag" in out
    assert f"Updating testchart/values.yaml: list.1.image: testchart/testimage:1.2.3-test.tag" in out

    # make a git tag and verify it is detected
    git_repo.create_tag("1.2.3-test.tag", message="1.2.3-test.tag")

    _, _ = capfd.readouterr()
    chartpress.main(["--skip-build"])
    out, err = capfd.readouterr()
    print()
    print('--- chartpress --skip-build ---')
    print(out)
    print("-------------------------------")

    # verify detection of git tag by the fact that nothing required updating as
    # the previous write to --tag updated Chart.yaml and values.yaml already
    assert f"Updating" not in out

    _, _ = capfd.readouterr()
    chartpress.main(["--skip-build", "--long"])
    out, err = capfd.readouterr()
    print()
    print('--- chartpress --skip-build --long ---')
    print(out)
    print("--------------------------------------")

    # verify usage of --long
    assert f"Updating testchart/Chart.yaml: version: 1.2.3-test.tag.000.{sha}" in out
    assert f"Updating testchart/values.yaml: image: testchart/testimage:1.2.3-test.tag.000.{sha}" in out
    assert f"Updating testchart/values.yaml: list.0: testchart/testimage:1.2.3-test.tag.000.{sha}" in out
    assert f"Updating testchart/values.yaml: list.1.image: testchart/testimage:1.2.3-test.tag.000.{sha}" in out

    _, _ = capfd.readouterr()
    chartpress.main(["--skip-build", "--image-prefix", "test-prefix/"])
    out, err = capfd.readouterr()
    print()
    print('--- chartpress --skip-build --image-prefix test-prefix ---')
    print(out)
    print("----------------------------------------------------------")

    # verify usage of --image-prefix
    assert f"Updating testchart/Chart.yaml: version: 1.2.3-test.tag" in out
    assert f"Updating testchart/values.yaml: image: test-prefix/testimage:1.2.3-test.tag" in out
    assert f"Updating testchart/values.yaml: list.0: test-prefix/testimage:1.2.3-test.tag" in out
    assert f"Updating testchart/values.yaml: list.1.image: test-prefix/testimage:1.2.3-test.tag" in out
