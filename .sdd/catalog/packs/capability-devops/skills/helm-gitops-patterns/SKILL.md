---
name: helm-gitops-patterns
description: Production Helm chart authoring with values.schema.json and deterministic templates, Kustomize base and overlay composition, GitOps continuous reconciliation with ArgoCD and Flux, drift detection and fail-closed sync policies, secret management with External Secrets Operator and SOPS, and Gate 6 release alignment. Use when packaging Kubernetes workloads, structuring GitOps repositories, or auditing cluster sync and secret safety under SDD Gate 2, Gate 4, and Gate 6.
---

# Helm & GitOps Patterns

Declarative Kubernetes delivery playbook for deterministic Helm charts, Kustomize environment overlays, pull-based GitOps reconciliation (ArgoCD / Flux), fail-closed drift guards, zero-plaintext secret management, and auditable Gate 6 releases.

## 1. When to Activate

Activate this skill whenever a Work Item (`FEAT-XXX`, `CR-XXX`, `BUG-XXX`) or Release (`REL-vX.Y.Z`) involves:

- Authoring, refactoring, or linting Helm charts (`Chart.yaml`, `values.yaml`, `values.schema.json`, `templates/`).
- Structuring Kustomize `base/` and `overlays/{dev,staging,prod}/` directories or composing Helm charts with Kustomize patches.
- Configuring ArgoCD `Application` / `ApplicationSet` or Flux `GitRepository` / `Kustomization` / `HelmRelease` reconciliation pipelines.
- Enforcing drift detection, automated self-healing, sync waves, or fail-closed promotion policies across environments.
- Designing Kubernetes secret delivery via External Secrets Operator (ESO) or SOPS without ever committing plaintext credentials to Git.
- Preparing or verifying Kubernetes and GitOps release promotion aligned with `.agents/workflows/gate6-release.md`.

## 2. Production Architecture & Patterns

### 2.1. Helm Charts: Schema Validation & Deterministic Templates

Treat every Helm chart as a versioned, strictly typed release artifact (`apiVersion: v2`).

- **Strict `values.schema.json`:** Define JSON Schema Draft 7 validation alongside `values.yaml` with `"additionalProperties": false` on critical objects so misspelled keys in environment value files fail immediately during `helm lint` and `helm template`.
- **Deterministic Rendering:** Templates MUST produce byte-identical manifests across repeated renders. Never use nondeterministic template functions (`randAlphaNum`, `now`, `uuidv4`, or live-cluster `lookup`) inside GitOps-reconciled resources, because they trigger perpetual drift loops.
- **Immutable Image Digests & Config Rollouts:** Pin images by immutable SHA-256 digest (`image.digest`) rather than mutable tags (`latest`). Include a deterministic config hash annotation (`checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}`) on Pod templates so ConfigMap updates trigger controlled rolling restarts.

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "type": "object",
  "additionalProperties": false,
  "required": ["replicaCount", "image", "resources"],
  "properties": {
    "replicaCount": { "type": "integer", "minimum": 1, "maximum": 100 },
    "image": {
      "type": "object",
      "additionalProperties": false,
      "required": ["repository", "tag", "digest"],
      "properties": {
        "repository": { "type": "string", "minLength": 1 },
        "tag": { "type": "string", "pattern": "^v[0-9]+\\.[0-9]+\\.[0-9]+$" },
        "digest": { "type": "string", "pattern": "^sha256:[a-f0-9]{64}$" }
      }
    },
    "resources": {
      "type": "object",
      "required": ["requests", "limits"]
    }
  }
}
```

### 2.2. Kustomize Bases, Overlays & Packaging Choice

Use Kustomize for environment-specific composition without duplicating base YAML across environments:

```text
deploy/
  base/
    kustomization.yaml
    deployment.yaml
    service.yaml
    pdb.yaml
  components/
    network-policy/
      kustomization.yaml
      netpol.yaml
  overlays/
    dev/
      kustomization.yaml
      patch-replicas.yaml
    staging/
      kustomization.yaml
    prod/
      kustomization.yaml
      patch-hpa.yaml
      external-secret.yaml
```

| Tooling Pattern | Best Fit | Guardrail |
| :--- | :--- | :--- |
| **Helm Chart** | Reusable multi-tenant or shared internal services, third-party vendor charts, strict parameter validation via `values.schema.json`. | Lock chart dependencies in `Chart.lock`; validate every `values-<env>.yaml` with `helm lint --strict`. |
| **Kustomize Base + Overlays** | First-party workloads owned by one squad with small per-environment deltas (replicas, ingress hosts, HPA bounds). | Keep `configMapGenerator` hash suffix enabled (default) so Pods roll cleanly on config changes. |
| **Helm + Kustomize Overlay** | Wrapping upstream third-party Helm charts with organization security patches (PodSecurity, NetworkPolicy, annotations). | Pin exact upstream chart version and digest; never hand-edit unpacked vendor templates. |

### 2.3. GitOps Continuous Reconciliation (ArgoCD & Flux)

Git is the single declarative source of truth for desired cluster state. Controllers pull and reconcile state continuously inside the cluster; CI builds, signs, tests, and opens a promotion PR rather than running `kubectl apply` against production clusters.

**ArgoCD Fail-Closed `Application` Baseline:**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: orders-api-prod
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: production
  source:
    repoURL: https://github.com/org/platform-gitops.git
    targetRevision: v1.4.2
    path: charts/orders-api
    helm:
      valueFiles:
        - values.yaml
        - values-prod.yaml
      ignoreMissingValueFiles: false
  destination:
    server: https://kubernetes.default.svc
    namespace: orders-prod
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
      - Validate=true
      - CreateNamespace=false
      - ServerSideApply=true
      - PrunePropagationPolicy=foreground
      - PruneLast=true
      - FailOnSharedResource=true
    retry:
      limit: 3
      backoff:
        duration: 10s
        factor: 2
        maxDuration: 2m
```

**Flux `Kustomization` & `HelmRelease` Baseline:**

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: orders-api-prod
  namespace: flux-system
spec:
  interval: 5m
  retryInterval: 1m
  timeout: 3m
  path: ./deploy/overlays/prod
  prune: true
  wait: true
  force: false
  sourceRef:
    kind: GitRepository
    name: platform-gitops
  decryption:
    provider: sops
    secretRef:
      name: sops-age-key
```

For Flux `HelmRelease`, explicitly configure `spec.upgrade.remediation.retries: 3` and `spec.upgrade.remediation.strategy: rollback` so failed upgrades automatically revert to the last healthy Helm release revision instead of leaving partial resources behind.

### 2.4. Drift Detection & Fail-Closed Sync Policies

- **Continuous Drift Detection:** Enable `selfHeal: true` (ArgoCD) or bounded `spec.interval` (Flux) and alert whenever `OutOfSync` or `Degraded` persists longer than the deployment window (e.g., `> 5m`). Manual out-of-band `kubectl edit` changes in production MUST be reverted automatically and flagged as security/compliance drift.
- **Fail-Closed Sync Gates:** Block reconciliation on invalid manifests (`Validate=true`, `FailOnSharedResource=true`, `allowEmpty: false`, `ignoreMissingValueFiles: false`, `force: false`). Reject sync if pre-sync validation (`kubeconform -strict`, policy engine admission, or schema checks) fails.
- **Ordered Dependencies & Stateful Protection:** Order database migrations and CRDs ahead of application Deployments using ArgoCD `argocd.argoproj.io/sync-wave` (`-1` for CRDs/ExternalSecrets, `0` for migrations/PreSync Jobs, `1` for Deployments) or Flux `spec.dependsOn`. Protect stateful PersistentVolumeClaims from accidental pruning with `argocd.argoproj.io/sync-options: Prune=false` or `helm.sh/resource-policy: keep` only where explicitly approved in Gate 2.
- **Declarative Rollback Only:** Roll back unhealthy releases by reverting the Git commit or switching `targetRevision` to the previous immutable SemVer tag (`vX.Y.Z`) — never by running imperative `helm rollback` that diverges from Git.

### 2.5. Secret Management: External Secrets Operator & SOPS

Zero plaintext secrets are permitted in Git repositories, Helm `values*.yaml`, or Kustomize patches (strict enforcement of `.agents/rules/05-security-and-secrets.md`).

- **External Secrets Operator (Preferred for Cloud/Vault Backends):** Store secret values in AWS Secrets Manager, GCP Secret Manager, Azure Key Vault, or HashiCorp Vault; authenticate the cluster via short-lived workload identity (IRSA, GKE Workload Identity, Azure Workload Identity, or Vault Kubernetes Auth). Commit only the `ExternalSecret` reference:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: orders-api-secrets
  namespace: orders-prod
spec:
  refreshInterval: 15m
  secretStoreRef:
    name: prod-cloud-secrets
    kind: ClusterSecretStore
  target:
    name: orders-api-runtime-env
    creationPolicy: Owner
    deletionPolicy: Retain
  dataFrom:
    - extract:
        key: prod/orders-api/runtime
```

- **SOPS + `age` / Cloud KMS (For Git-Resident Encrypted Manifests):** Configure `.sops.yaml` with `encrypted_regex: '^(data|stringData)$'` so metadata stays diffable while values remain authenticated-encrypted (AES-256-GCM). Decrypt exclusively inside the cluster via Flux `spec.decryption.provider: sops` or ArgoCD KSOPS; never commit unencrypted keys or `.agekey` files.

## 3. SDD Gate 2 & Gate 4 Contract Alignment

- **Gate 2 (`02-tech-spec.md` — `@architect`, `@devops`, `@security-reviewer`):**
  1. Specify packaging model (Helm chart, Kustomize overlays, or hybrid), `values.schema.json` constraints, and target namespace isolation.
  2. Document GitOps sync policy per environment (`dev`/`staging` automated vs. `prod` immutable SemVer tag promotion), `prune`/`selfHeal` rules, sync wave order, and rollback SLA.
  3. Specify secret backend (`ExternalSecret` + `ClusterSecretStore` or SOPS + KMS/`age`), rotation cadence, and least-privilege controller RBAC.
- **Gate 4 (`@devops` & `@qa-tester`):**
  - Validate chart linting (`helm lint --strict`), offline template rendering (`helm template`), Kustomize overlay builds, Kubernetes OpenAPI schema conformance (`kubeconform -strict`), and zero plaintext secrets across all rendered manifests.
  - Pair this skill with `kubernetes-patterns` (probes, PDB, RBAC, securityContext), `docker-patterns` (digest-pinned non-root images), `deployment-patterns`, `canary-watch`, `sdd-security-audit`, and `santa-method` dual review when modifying production delivery paths.
- **Gate 6 Release Alignment (`.agents/workflows/gate6-release.md`):**
  - Start every production chart/manifest release through `./sdd git release-start --version X.Y.Z` and `./sdd release prepare --version X.Y.Z`, updating Helm `Chart.yaml` (`version`/`appVersion`) and pinned image digests on `release/vX.Y.Z`.
  - Record sync waves, schema/secret prerequisites, drift verification checks, and declarative `git revert` rollback steps inside `specs/releases/REL-vX.Y.Z.md`.
  - Respect human Gate 6 sign-off (`RN-SDD-HUMAN-GATE-OWNERSHIP`) before executing `./sdd release verify --version X.Y.Z --stage finish` and `./sdd git release-finish --version X.Y.Z` (PR to `main`, never direct push). Pin production ArgoCD `targetRevision` or Flux `spec.ref.tag` to the resulting immutable `vX.Y.Z` tag so every cluster state maps 1:1 to an approved `REL-vX.Y.Z.md` dossier.

## 4. Anti-Patterns & Fail-Closed Guards

| Anti-Pattern | Failure Mode | Fail-Closed Guard |
| :--- | :--- | :--- |
| Plaintext or base64 Kubernetes `Secret` committed to Git | Permanent credential leak in Git history (violates `.agents/rules/05-security-and-secrets.md`). | Mandate ESO `ExternalSecret` or SOPS-encrypted files with `encrypted_regex` and CI secret scanning. |
| Floating tags (`:latest`, `:main`) or nondeterministic Helm helpers (`now`, `randAlphaNum`) | Non-reproducible rollouts and infinite ArgoCD/Flux drift reconciliation loops. | Pin immutable `sha256:...` image digests in values/overlays and enforce deterministic `helm template` diffs in CI. |
| Imperative `kubectl apply` or `helm upgrade` from CI/developer machines | Cluster diverges silently from Git; rollbacks overwrite hotfixes unpredictably. | Revoke human/CI cluster write RBAC in managed namespaces; funnel all changes through GitOps PRs. |
| Omitting `values.schema.json` or allowing unknown keys | Typo in `values-prod.yaml` silently falls back to unsafe dev defaults. | Require strict `values.schema.json` (`additionalProperties: false`) checked by `helm lint --strict`. |
| Disabling `prune` or `selfHeal` globally to avoid surprises | Orphaned workloads, leaked ingresses, and undetected manual drift accumulate in prod. | Keep `prune: true` and `selfHeal: true`; scope `Prune=false` exclusively to approved stateful PVCs. |
| Enabling `force: true` / `Replace=true` on stateful syncs | Destructive pod/PVC recreation and avoidable downtime during schema or field mismatches. | Keep `force: false`, enable `ServerSideApply=true`, and fail closed on immutable field conflicts. |
| Auto-syncing mutable `main`/`develop` branches straight into prod without Gate 6 | Unapproved changes deploy before `REL-vX.Y.Z.md` human sign-off (violates `.agents/workflows/gate6-release.md`). | Pin prod GitOps targets to immutable `vX.Y.Z` SemVer tags produced after Gate 6 PR merge. |

## 5. Deterministic Verification Commands

Run these deterministic checks during Gate 4 DoD and Gate 6 release readiness verification (adapt paths and chart names to `specs/STACK.md`):

```bash
# 1. Lint Helm chart strictly (enforces values.schema.json) and verify deterministic rendering
helm lint ./charts/orders-api -f ./charts/orders-api/values-prod.yaml --strict
helm template orders-api ./charts/orders-api -f ./charts/orders-api/values-prod.yaml \
  | kubeconform -strict -ignore-missing-schemas -summary

# 2. Build Kustomize overlay and validate rendered Kubernetes manifests against schemas
kubectl kustomize ./deploy/overlays/prod \
  | kubeconform -strict -ignore-missing-schemas -summary

# 3. Verify zero plaintext Kubernetes Secrets exist in Git-tracked manifests
git grep -nE '^kind:\s*Secret\b' -- deploy/ charts/ || true
# (Any match MUST contain SOPS metadata `sops:` or be rejected fail-closed)

# 4. Preview GitOps drift / diff before promoting or syncing (ArgoCD or Flux)
argocd app diff orders-api-prod --local ./charts/orders-api --exit-code
argocd app get orders-api-prod --refresh
flux diff kustomization orders-api-prod --path ./deploy/overlays/prod
flux get all -A

# 5. Verify External Secrets synchronization health and Gate 6 release readiness
kubectl get externalsecrets -n orders-prod
./sdd release verify --version "${RELEASE_VERSION}" --stage finish
```
