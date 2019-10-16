# How to make a release

`chartpress` is a package [available on
PyPI](https://pypi.org/project/chartpress/). These are instructions on how to
make a release on PyPI.

For you to follow along according to these instructions, you need:
- To be a maintainer of the [PyPI chartpress
  project](https://pypi.org/project/chartpress/).
- To have push rights to the [chartpress GitHub repository](https://github.com/jupyterhub/chartpress).

## Technical steps to make a release

1. Checkout master and make sure it is up to date.

   ```
   git checkout master
   git fetch <upstream> master
   git reset --hard <upstream>/master
   ```

1. Update [CHANGELOG.md](CHANGELOG.md) and verify [README.md](README.md) has an
   updated output of running `--help`.

1. Set the `__version__` variable in [chartpress.py](chartpress.py)
   appropriately and make a commit with message `release <tag>`.

1. Create a git tag for the commit.

   ```
   git tag -a <tag> -m <tag> HEAD
   ```

1. Package the release
   ```
   python3 setup.py bdist_wheel
   ```

1. Upload it to PyPI
   ```
   twine upload dist/chartpress-<tag>-py3-none-any.whl
   ```

1. Reset the `__version__` variable in [chartpress.py](chartpress.py)
   appropriately with a `.dev` appendix and make a commit with the message `back
   to dev`.

1. Push your two commits to master along with the annotated tags referencing
   commits on master.

   ```
   git push --follow-tags <upstream> master
   ```
