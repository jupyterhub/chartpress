# How chart version and image tags are determined

Chartpress will infer chart versions and image tags using a few key pieces of
information.

1. `tag`: If not directly set by `--tag`, it will be inferred from most recent
   commit that is tagged in the _current branch_
   (as determined by `git describe`)
   or be set to 0.0.1 if no commit is tagged.
   1. If the `tag` has a leading `v` but is otherwise a valid
      [SemVer2](https://semver.org) version, the `v` will be stripped from Chart.yaml
      before its set as Helm 3 requires Helm chart versions to be SemVer2
      compliant.
1. The latest commit modifying content in a _relevant path_ since `tag`.
   1. `n`: The number of commits since the latest tagged commit on the branch, as an integer.
   1. `hash`: The latest commit's abbreviated hash, which is often 7-8 characters,
      prefixed with `h`.
1. If `tag` (like `0.10.0` or `0.10.0-beta.1`) contains a `-`, a `tag.git.n.hash`
   format will be used, and otherwise a `tag-0.dev.git.n.hash` format will be used.
1. If `--long` is specified or not. If `--long` is specified, tagged commits
   will always be written out with the `.git.n.hash` part appended to it, looking something
   like `1.0.0-0.dev.git.0.habcd123`

When producing a development version (with `.git.n.hash` on the end),
The _base_ version can come from one of two places,
depending on your configuration.
See [Controlling development versions](#controlling-development-versions) for more info.

## Examples chart versions and image tags

This is a list of realistic chart versions and/or image tags in a chronological
order that could come from using chartpress.

```
0.8.0
0.8.0-0.dev.git.4.hasdf123
0.8.0-0.dev.git.10.hsdfg234
0.9.0-beta.1
0.9.0-beta.1.git.12.hdfgh345
0.9.0-beta.1.git.15.hfghj456
0.9.0-beta.2
0.9.0-beta.2.git.20.hghjk567
0.9.0-beta.3
0.9.0
```
