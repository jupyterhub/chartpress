# Notes about the tests

These tests are [pytest](https://docs.pytest.org) tests.

useful flags:


```bash
pytest -vx --flakes

# -v / --verbose:
#   allows you to see the names etc of individual tests etc.
# -x / --exitfirst:
#   to stop running tests of first error
# --flakes:
#   use pyflakes to add some static code analysis tests
# -k:
#   only run tests which match the given substring
```

## Developing tests
Keep your eye out for test issues caused by caching! The
[`@lru_cache()`](https://docs.python.org/3/library/functools.html#functools.lru_cache)
decorator will do in memory cache that affects us when we run multiple commands
to chartpress in the same process. This decorator also adds the `cache_clear()`
function to the function object.

It is very possible to run into issues with caching on `image_needs_building`,
`image_needs_pushing` and `latest_tag_or_mod_commit`.

```python
# clearing the cache of these functions is important if you run chartpress
# without --skip-build
chartpress.image_needs_building.cache_clear()
chartpress.image_needs_pushing.cache_clear()

# clearing the cache of this function is important very often
chartpress.latest_tag_or_mod_commit.cache_clear()
```

## Not yet tested
- `--push`

## References
- [pytest](https://docs.pytest.org)
  - Fixture: [capfd](https://docs.pytest.org/en/latest/reference.html#_pytest.capture.capfd)
  - Fixture: [monkeypatching](https://docs.pytest.org/en/latest/capfd.html)
- [pytest-flakes](https://github.com/fschulze/pytest-flakes) and
  [pyflakes](https://github.com/PyCQA/pyflakes) for passive code check tests
  added to the other pytest tests when using the `--flakes` flag with `pytest`.
- [GitPython](https://gitpython.readthedocs.io/en/stable/)
