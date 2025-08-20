# Example

This section tries to give a full picture example of how `chartpress` is used.

```{note}
The files used in this sections are available in [`minimal-working-example.zip`](minimal-working-example.zip).
```

## Requirements

The following binaries must be in your `PATH`:

- [`git`](https://www.git-scm.com/downloads)
- [`docker`](https://docs.docker.com/install/#supported-platforms)
- [`helm`](https://helm.sh/docs/using_helm/#installing-helm)
- `chartpress`

## Project structure

```
.
├── chartpress.yaml
├── Dockerfile
├── helm
│   └── minimal-working-example
│       ├── Chart.yaml
│       ├── templates
│       │   └── deployment.yaml
│       └── values.yaml
└── README.md
```

## Building

During building, `chartpress` will

- re-write the Helm chart version
- create a new container image
- re-write the Helm values with the new container image tag

To build, run

```bash
chartpress
```

```{note}
During development, it is recommended to configure the [Docker context](https://docs.docker.com/engine/manage-resources/contexts/) to be the same used by the Kubernetes cluster.
```

## Installing

:::{note}
Remember to verify the Kubernetes context that you are using with

```bash
kubectl config get-contexts
```

If the Kubernetes context is incorrect, select the correct context with

```bash
kubectl config use-context CONTEXT_NAME
```

where `CONTEXT_NAME` is the name of the correct context.
:::

Installing is a step that does **not** involve `chartpress`. To install, run

```bash
helm upgrade \
    minimal-working-example \
    ./helm/minimal-working-example \
    --create-namespace \
    --force \
    --install
```

If the installation goes well, you will have a pod running.

```bash
kubectl get pods
```

```
NAME                                       READY   STATUS    RESTARTS   AGE
minimal-working-example-78b6b8b87c-lhbl9   1/1     Running   0          2m52s
```

## Cleaning

First, uninstall the Helm release.

```bash
helm uninstall \
    minimal-working-example
```

Last, undo the changes in the Helm chart.

```bash
chartpress --reset
```
