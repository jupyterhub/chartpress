# Development

Testing of this python package can be done using
[`pytest`](https://github.com/pytest-dev/pytest). For more details on the
testing, see [tests/README.md](https://github.com/jupyterhub/chartpress/blob/main/tests/README.md).

```bash
# install chartpress locally
pip install  -e ".[test]"

# format and lint code
pip install pre-commit
pre-commit run -a

# run tests
pytest --verbose --exitfirst
# some tests push to a local registry, you can skip these
pytest --verbose --exitfirst -m 'not registry'
```
