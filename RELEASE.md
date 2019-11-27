# How to make a release

`chartpress` is a package [available on
PyPI](https://pypi.org/project/chartpress/). These are instructions on how to
make a release on PyPI.

For you to follow along according to these instructions, you need:
- To be a maintainer of the [PyPI chartpress
  project](https://pypi.org/project/chartpress/).
- To have push rights to the [chartpress GitHub repository](https://github.com/jupyterhub/chartpress).

## Steps to make a release

1. Update [CHANGELOG.md](CHANGELOG.md) if it is not up to date,
   and verify [README.md](README.md) has an updated output of running `--help`.
   Make a PR to review the CHANGELOG notes.

1. Once the changelog is up to date, checkout master and make sure it is up to date and clean.

   ```bash
   ORIGIN=${ORIGIN:-origin} # set to the canonical remote, e.g. 'upstream' if 'origin' is not the official repo
   git checkout master
   git fetch $ORIGIN master
   git reset --hard $ORIGIN/master
   # WARNING! This next command deletes any untracked files in the repo
   git clean -xfd
   ```

1. Update the version with `bump2version` (can be installed with `pip install -r dev-requirements.txt`)

   ```bash
   VERSION=...  # e.g. 1.2.3
   bump2version --tag --new-version $VERSION -
   ```

1. Package the release

   ```bash
   python3 setup.py sdist bdist_wheel
   ```

1. Upload it to PyPI

   ```bash
   twine upload dist/*
   ```

1. Reset the version to the next development version with `bump2version`

   ```bash
   bump2version --no-tag patch
   ```

1. Push your two commits to master along with the annotated tags referencing
   commits on master.

   ```
   git push --follow-tags $ORIGIN master
   ```
