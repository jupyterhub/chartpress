# Chartpress

Chartpress automate basic Helm chart development work. It is tightly used in development of the [JupyterHub](https://github.com/jupyterhub/zero-to-jupyterhub-k8s) and [BinderHub](https://github.com/jupyterhub/binderhub) Helm charts.

## Features

Chartpress can do the following with the help of some configuration.

- Update Chart.yaml's version appropriately
- Build docker images and tag them appropriately
- Push built images to a docker image repository
- Update values.yaml to reference the built images
- Publish a chart to a Helm chart registry based on GitHub pages
- Reset changes to Chart.yaml and values.yaml

```{toctree}
:maxdepth: 2

chart-version.md
installation.md
usage.md
configuration.md
example.md
development.md
```
