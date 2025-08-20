# [chartpress](https://github.com/jupyterhub/chartpress)

[![Latest PyPI version](https://img.shields.io/pypi/v/chartpress?logo=pypi)](https://pypi.python.org/pypi/chartpress)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/jupyterhub/chartpress/test.yaml?logo=github)](https://github.com/jupyterhub/chartpress/actions)
[![GitHub](https://img.shields.io/badge/issue_tracking-github-blue?logo=github)](https://github.com/jupyterhub/chartpress/issues)
[![Discourse](https://img.shields.io/badge/help_forum-discourse-blue?logo=discourse)](https://discourse.jupyter.org/c/jupyterhub)
[![Gitter](https://img.shields.io/badge/social_chat-gitter-blue?logo=gitter)](https://gitter.im/jupyterhub/jupyterhub)

Chartpress automate basic Helm chart development work. It is tightly used in development of the [JupyterHub](https://github.com/jupyterhub/zero-to-jupyterhub-k8s) and [BinderHub](https://github.com/jupyterhub/binderhub) Helm charts.

## Features

Chartpress can do the following with the help of some configuration.

- Update Chart.yaml's version appropriately
- Build docker images and tag them appropriately
- Push built images to a docker image repository
- Update values.yaml to reference the built images
- Publish a chart to a Helm chart registry based on GitHub pages
- Reset changes to Chart.yaml and values.yaml
