# Helm Charts to Deploy Cluster API

## Why?

`clusterctl` is very opinionated, it will pull down some kustomize generated manifests, then do some environment substitution on them.
This isn't compatible with ArgoCD for example, hence this project.

## How

In simple terms, we run `kubectl kustomize`, chop up the manifests and auto generate templates.
When we encounter one of the annoying environment variables, we replace it with Go templating, then add the replacement into `values.yaml`.

## Deploying Prerequisites

This chart requires the following to be installed on the target cluster first:

### Cert-Manager

<details>
<summary>Helm</summary>

```shell
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager --version v1.15.1 --namespace cert-manager --create-namespace --set crds.enabled=true
```
</details>

<details>
<summary>ArgoCD</summary>

```yaml
---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  generateName: cert-manager-
  namespace: argocd
spec:
  destination:
    server: ${TARGET_VCLUSTER}
    namespace: cert-manager
  project: default
  source:
    chart: cert-manager
    repoURL: https://charts.jetstack.io
    targetRevision: v1.15.1
    helm:
      releaseName: cert-manager
      parameters:
      - name: installCRDs
        value: "true"
  syncPolicy:
    automated:
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```
</details>

## Deploying One-Shot

There is a top level chart-of-charts that will just install everything as a big bang operation.

<details>
<summary>Helm</summary>

```shell
helm repo add unikorn-cloud-capi https://unikorn-cloud.github.io/helm-cluster-api
helm repo update
helm install cluster-api unikorn-cloud-capi/cluster-api --version v0.2.0
```
</details>

<details>
<summary>ArgoCD</summary>

```yaml
---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: cluster-api
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://unikorn-cloud.github.io/helm-cluster-api
    chart: cluster-api
    targetRevision: v0.2.0
  destination:
    server: ${TARGET_CLUSTER}
    namespace: foo
  ignoreDifferences:
  # Aggregated roles are mangically updated by the API.
  - group: rbac.authorization.k8s.io
    kind: ClusterRole
    name: capi-aggregated-manager-role
    jsonPointers:
    - /rules
  - group: rbac.authorization.k8s.io
    kind: ClusterRole
    name: capi-kubeadm-control-plane-aggregated-manager-role
    jsonPointers:
    - /rules
  # CA certs are injected by cert-manager mutation
  - group: apiextensions.k8s.io
    kind: CustomResourceDefinition
    jsonPointers:
    - /spec/conversion/webhook/clientConfig/caBundle
  syncPolicy:
    automated:
      selfHeal: true
    syncOptions:
    - RespectIgnoreDifferences=true
```
</details>

## Deploying Main Components

You may want to be a little less gung-ho and deploy the pieces as separate applications.

### Core

<details>
<summary>Helm</summary>

```shell
helm repo add unikorn-cloud-capi https://unikorn-cloud.github.io/helm-cluster-api
helm repo update
helm install cluster-api-core unikorn-cloud-capi/cluster-api-core --version v0.2.0
```
</details>

<details>
<summary>ArgoCD</summary>

```yaml
---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  generateName: cluster-api-core-
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://unikorn-cloud.github.io/helm-cluster-api
    chart: cluster-api-core
    targetRevision: v0.2.0
  destination:
    server: ${TARGET_CLUSTER}
    namespace: foo
  ignoreDifferences:
  # Aggregated roles are mangically updated by the API.
  - group: rbac.authorization.k8s.io
    kind: ClusterRole
    name: capi-aggregated-manager-role
    jsonPointers:
    - /rules
  # CA certs are injected by cert-manager mutation
  - group: apiextensions.k8s.io
    kind: CustomResourceDefinition
    jsonPointers:
    - /spec/conversion/webhook/clientConfig/caBundle
  syncPolicy:
    automated:
      selfHeal: true
    syncOptions:
    - RespectIgnoreDifferences=true
```
</details>

### Bootstrap

<details>
<summary>Helm</summary>

```shell
helm repo add unikorn-cloud-capi https://unikorn-cloud.github.io/helm-cluster-api
helm repo update
helm install cluster-api-bootstrap-kubeadm unikorn-cloud-capi/cluster-api-bootstrap-kubeadm --version v0.2.0
```
</details>

<details>
<summary>ArgoCD</summary>

```yaml
---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  generateName: cluster-api-bootstrap-kubeadm-
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://unikorn-cloud.github.io/helm-cluster-api
    chart: cluster-api-bootstrap-kubeadm
    targetRevision: v0.2.0
  destination:
    server: ${TARGET_CLUSTER}
    namespace: foo
  ignoreDifferences:
  - group: apiextensions.k8s.io
    jsonPointers:
    - /spec/conversion/webhook/clientConfig/caBundle
    kind: CustomResourceDefinition
  syncPolicy:
    automated:
      selfHeal: true
    syncOptions:
    - RespectIgnoreDifferences=true
```
</details>

### Control Plane

<details>
<summary>Helm</summary>

```shell
helm repo add unikorn-cloud-capi https://unikorn-cloud.github.io/helm-cluster-api
helm repo update
helm install cluster-api-control-plane-kubeadm unikorn-cloud-capi/cluster-api-control-plane-kubeadm --version v0.2.0
```
</details>

<details>
<summary>ArgoCD</summary>

```yaml
---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  generateName: cluster-api-control-plane-kubeadm-
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://unikorn-cloud.github.io/helm-cluster-api
    chart: cluster-api-control-plane-kubeadm
    targetRevision: v0.2.0
  destination:
    server: ${TARGET_CLUSTER}
    namespace: foo
  ignoreDifferences:
  - group: rbac.authorization.k8s.io
    jsonPointers:
    - /rules
    kind: ClusterRole
    name: capi-kubeadm-control-plane-aggregated-manager-role
  - group: apiextensions.k8s.io
    jsonPointers:
    - /spec/conversion/webhook/clientConfig/caBundle
    kind: CustomResourceDefinition
  syncPolicy:
    automated:
      selfHeal: true
    syncOptions:
    - RespectIgnoreDifferences=true
```
</details>

## Deploying Infrastructure Providers and Clusters

Add providers to allow CAPI to talk to various cloud providers.

### OpenStack

* [Install the provider](charts/cluster-api-provider-openstack/README.md)
* [Install a cluster](charts/cluster-api-provider-openstack/README.md)

## Developers

It's a simple as:

* Bump the versions in `Makefile` and `charts/cluster-api/Chart.yaml`
* Run `make`
* Commit and merge.
