# Notes about the tests

These tests are [pytest](https://docs.pytest.org) tests.


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
