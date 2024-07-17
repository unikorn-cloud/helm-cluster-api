# Installing Cluster API Provider OpenStack

<details>
<summary>Helm</summary>

```shell
helm repo add unikorn-cloud-capi https://unikorn-cloud.github.io/helm-cluster-api
helm repo update
helm install cluster-api-provider-openstack --version v0.2.0
```
</details>

<details>
<summary>ArgoCD</summary>

```yaml
---

apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: cluster-api-provider-openstack
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://unikorn-cloud.github.io/helm-cluster-api
    chart: cluster-api-provider-openstack
    targetRevision: v0.2.0
  destination:
    server: ${TARGET_CLUSTER}
  ignoreDifferences:
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

