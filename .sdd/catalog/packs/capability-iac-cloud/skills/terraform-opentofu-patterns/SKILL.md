---
name: terraform-opentofu-patterns
description: Production Terraform and OpenTofu Infrastructure as Code playbook covering composable HCL modules, encrypted remote state with locking, non-destructive moved/import/removed refactoring, native testing (terraform validate, tofu test, TFLint), Checkov/Trivy IaC scanning, and AWS/GCP/Azure multi-cloud parity. Use when designing, implementing, refactoring, or auditing IaC modules and cloud environments under SDD Gate 2 and Gate 4.
---

# Terraform & OpenTofu Patterns

Production-grade Infrastructure as Code (IaC) engineering playbook for composable HCL modules, encrypted remote state management, zero-downtime state refactoring, automated validation, and Terraform/OpenTofu parity across AWS, GCP, and Azure.

## 1. When to Activate

Activate this skill whenever a Work Item (`FEAT-XXX`, `CR-XXX`, or `BUG-XXX`) involves any of the following:

- Bootstrapping or modifying cloud infrastructure roots (`infra/envs/<env>/<stack>`) or reusable HCL modules (`infra/modules/<component>`).
- Configuring encrypted remote state backends and distributed state locking on AWS, GCP, or Azure.
- Refactoring module hierarchy, renaming resource addresses, adopting unmanaged brownfield resources (`import`), or detaching resources (`removed`) without downtime.
- Authoring native HCL unit/integration tests (`*.tftest.hcl`), TFLint provider rulesets, or Checkov/Trivy policy gates in CI/CD.
- Ensuring multi-cloud and engine parity between Terraform (`>= 1.9`) and OpenTofu (`>= 1.8`) across teams or regulated environments.
- Investigating state lock contention, configuration drift, provider upgrade regressions, or destructive plan diffs.

## 2. Production Architecture & Patterns

### 2.1. Composable HCL Module Architecture

Keep root stacks thin and reusable child modules focused on a single bounded infrastructure capability (e.g., `vpc-network`, `rds-postgres`, `gke-cluster`, `aks-workload`).

- **Directory & Blast-Radius Layout:** Isolate state by environment and lifecycle cadence (`00-foundation/network`, `10-data/database`, `20-platform/compute`, `30-app/<service>`). Avoid using `terraform workspace` to separate `dev`, `staging`, and `prod` in the same backend; use separate directories and separate state keys/accounts instead.
- **Strict Version Pinning:** Pin `required_version` and every provider in `versions.tf` using pessimistic constraints (`~> 5.80`), commit `.terraform.lock.hcl` to version control, and pin external module sources to immutable Git commit SHAs or exact registry versions (`version = "5.16.0"`).
- **Typed Interfaces & Fail-Closed Validation:** Declare explicit `type`, `description`, and `validation` blocks on every input variable; mark credentials or tokens `sensitive = true`; expose only contract outputs required by downstream stacks.
- **Flat Composition Over Deep Nesting:** Limit module depth to at most 2 levels (root -> composite/leaf module). Pass dependency identifiers (VPC ID, subnet IDs, KMS ARN) via explicit input variables rather than hidden `data` lookups inside leaf modules.

```hcl
variable "environment" {
  type        = string
  description = "Target deployment environment controlling sizing and retention guardrails."
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "kms_key_arn" {
  type        = string
  description = "Customer-managed KMS key ARN used to encrypt storage and logs."
  validation {
    condition     = can(regex("^arn:aws[a-z-]*:kms:[a-z0-9-]+:[0-9]{12}:key/[a-f0-9-]+$", var.kms_key_arn))
    error_message = "kms_key_arn must be a valid AWS KMS key ARN."
  }
}
```

### 2.2. Encrypted Remote State & Locking Across Clouds

Never store `terraform.tfstate` locally or in Git. Remote state MUST enforce encryption at rest, TLS in transit, versioning for rollback, and atomic locking.

| Cloud Provider | Backend Type | Encryption & Locking Baseline |
| :--- | :--- | :--- |
| **AWS** | `s3` | `encrypt = true`, `kms_key_id`, `use_lockfile = true` (Terraform `>= 1.10` / OpenTofu `>= 1.10`) or DynamoDB lock table, bucket versioning + public access block. |
| **GCP** | `gcs` | Customer-managed encryption key (`encryption_key` / bucket CMEK), uniform bucket-level access, object versioning, native GCS lock object. |
| **Azure** | `azurerm` | `use_azuread_auth = true` (no storage account keys), Storage Service Encryption with CMK, blob soft-delete + versioning, native blob lease locking. |

- **OpenTofu Native Client-Side State Encryption:** When using OpenTofu (`>= 1.7`), configure an `encryption {}` block inside `terraform {}` with a KMS key provider (`aws_kms`, `gcp_kms`, or `azure_vault`) so state and plan files are encrypted before leaving the runner.

```hcl
terraform {
  required_version = ">= 1.9.0, < 2.0.0"

  backend "s3" {
    bucket       = "org-prod-tfstate-eu-west-1"
    key          = "10-data/orders-db/terraform.tfstate"
    region       = "eu-west-1"
    kms_key_id   = "alias/org-prod-tfstate"
    encrypt      = true
    use_lockfile = true
  }
}
```

### 2.3. Non-Destructive Refactoring: `moved`, `import`, and `removed`

Eliminate manual imperative `terraform state mv` / `terraform state rm` commands on shared environments. Express every state transition declaratively in HCL so it is peer-reviewed in Pull Requests and verified during `plan`.

- **Renaming or Extracting Modules (`moved`):** Preserves existing cloud resources without destroy/recreate. Keep `moved` blocks until all environments have applied them, then prune in a follow-up cleanup PR.
- **Adopting Existing Resources (`import`):** Brings brownfield resources under IaC control idempotently; run `-generate-config-out` only as a starting scaffold and immediately clean/parameterize the generated HCL.
- **Detaching Without Destroying (`removed`):** Removes a resource from state (`lifecycle { destroy = false }`) when handing ownership to another stack.

```hcl
moved {
  from = aws_s3_bucket.audit_logs
  to   = module.audit_logs.aws_s3_bucket.this[0]
}

import {
  to = google_storage_bucket.artifacts
  id = "org-prod-artifacts-eu"
}

removed {
  from = azurerm_storage_account.legacy_archive
  lifecycle {
    destroy = false
  }
}
```

### 2.4. Testing, Linting & Static Security Scanning

Enforce a deterministic 4-layer IaC quality pyramid before any `apply`:

1. **Format & Syntax (`fmt` + `validate`):** Enforce canonical HCL formatting (`-check -recursive`) and schema validation (`validate -no-color`).
2. **Provider-Aware Linting (`tflint`):** Enable cloud rulesets (`tflint-ruleset-aws`, `tflint-ruleset-google`, `tflint-ruleset-azurerm`) to catch invalid instance types, deprecated arguments, unused declarations, and missing version constraints.
3. **Native HCL Testing (`tofu test` / `terraform test`):** Write `tests/*.tftest.hcl` suites using `command = plan` and `mock_provider` for fast sub-second unit assertions on tags, encryption flags, and validation failures; reserve `command = apply` tests for ephemeral sandbox accounts with guaranteed teardown.
4. **IaC Security & Compliance Scanning (`trivy` / `checkov`):** Scan both raw HCL (`trivy config`) and rendered plan JSON (`terraform show -json tfplan.binary`) to fail-closed on unencrypted volumes, public buckets, wildcard IAM policies, or missing logging. Inline suppressions (`# checkov:skip=...` or `# trivy:ignore:...`) require a documented justification and expiry/ticket ID.

```hcl
# tests/storage_unit.tftest.hcl
mock_provider "aws" {}

run "enforces_kms_encryption_and_blocks_public_access" {
  command = plan

  variables {
    environment = "prod"
    bucket_name = "org-prod-audit-logs"
    kms_key_arn = "arn:aws:kms:eu-west-1:123456789012:key/11111111-2222-3333-4444-555555555555"
  }

  assert {
    condition     = aws_s3_bucket_public_access_block.this.block_public_acls == true
    error_message = "Public ACLs must be blocked on all managed S3 buckets."
  }
}
```

### 2.5. Multi-Cloud & Terraform/OpenTofu Engine Parity

Maintain portability across AWS, GCP, and Azure while keeping HCL cleanly compatible with the chosen engine declared in `specs/STACK.md`:

- **Shared Baseline HCL:** Stick to standard HCL2 constructs (`for_each`, `try`, `coalesce`, `moved`, `import`, `removed`, `check`, `*.tftest.hcl`) supported identically by both Terraform (`>= 1.9`) and OpenTofu (`>= 1.8`).
- **Explicit Engine Divergences:** Document any engine-specific feature in a Gate 2 ADR before adopting it: OpenTofu supports native state/plan `encryption {}` blocks and early evaluation in backend/module blocks, whereas Terraform supports `ephemeral` resources and provider write-only arguments (`*_wo`) on recent versions. Never mix both binaries against the same state file.
- **Stable Resource Indexing:** Prefer `for_each` over `count` for collections of subnets, IAM roles, or service accounts so removing an element from the middle of a list does not trigger cascading destroy/recreate operations.

## 3. SDD Gate 2 & Gate 4 Contract Alignment

- **Gate 2 (`02-tech-spec.md`):** Before writing HCL, `@architect` and `@devops` must specify:
  1. Target IaC engine (`terraform` or `tofu`), pinned CLI version range, and target cloud provider(s) (`aws`, `gcp`, `azure`).
  2. State blast-radius topology (stack boundaries, backend bucket/container, KMS key, locking mechanism) and drift-detection cadence.
  3. Module input/output contracts, non-destructive migration plan (`moved`/`import`/`removed`), and required `*.tftest.hcl` assertions.
  4. Security baseline aligned with `.agents/rules/05-security-and-secrets.md`, `sdd-security-audit`, and `cloud-iam-security`, plus FinOps tagging contracts from `cloud-finops-guardrails`.
- **Gate 4 (`@devops` & `@qa-tester`):**
  - Implement modules and environment roots strictly matching the Gate 2 specification and `sdd-spec-compliance-audit`.
  - Generate an exact saved plan (`-out=tfplan.binary`), export JSON for Checkov/Trivy scanning, and verify zero unexpected `destroy` or `replace` actions before promoting any change.
  - Record provisioned topology, remote state keys, and exported stack outputs in `docs/knowledge/SYSTEM_TOPOLOGY.md` during Gate 5 (`@documentator`).

## 4. Anti-Patterns & Fail-Closed Guards

| Anti-Pattern | Failure Mode | Fail-Closed Guard |
| :--- | :--- | :--- |
| Local `terraform.tfstate` or state committed to Git | Plaintext secrets leaked in VCS and concurrent applies corrupt cloud state. | Enforce remote encrypted backend with locking; add `*.tfstate*` and `.terraform/` to `.gitignore` and block via CI pre-check. |
| Using `count` on named resource lists (`count = length(var.users)`) | Removing index `0` shifts every subsequent index and destroys live resources. | Use `for_each = toset(...)` or `tomap(...)` keyed by stable immutable identifiers. |
| Running `terraform apply -auto-approve` without a saved plan | Race condition applies resources that differ from the reviewed PR plan. | Always generate `tfplan.binary` in CI, scan its JSON representation, and apply that exact artifact only after approval. |
| Manual `state mv` / `state rm` in production | Unaudited state surgery causes accidental resource deletion or orphaned billing. | Use declarative `moved {}`, `import {}`, and `removed {}` blocks validated in PR plans. |
| Unpinned providers/modules (`source = "...?ref=main"`) | Upstream breaking release silently mutates or destroys production infra. | Pin providers (`~> X.Y`), commit `.terraform.lock.hcl`, and pin modules to exact tags or commit SHAs. |
| Suppressing Checkov/Trivy findings without rationale | High-severity misconfigurations bypass security gates silently. | Fail CI on `HIGH`/`CRITICAL` IaC findings; require peer-reviewed justification and ticket reference for any temporary exception. |

## 5. Deterministic Verification Commands

Use these deterministic commands during Gate 4 DoD verification (replace `tofu` with `terraform` per `specs/STACK.md`):

```bash
# 1. Verify canonical formatting and HCL schema validity (offline, no backend mutations)
tofu fmt -check -recursive infra/
tofu -chdir=infra/envs/prod/network init -backend=false -input=false
tofu -chdir=infra/envs/prod/network validate -no-color

# 2. Run native HCL unit tests with mocked providers
tofu -chdir=infra/modules/storage test -no-color

# 3. Run provider-aware static linting via TFLint
tflint --init --config=.tflint.hcl
tflint --recursive --config=.tflint.hcl --minimum-failure-severity=warning

# 4. Run static IaC security scans (Trivy and Checkov) failing closed on HIGH/CRITICAL
trivy config --severity HIGH,CRITICAL --exit-code 1 infra/
checkov -d infra/ --framework terraform --compact --quiet

# 5. Detect live drift without mutating infrastructure (exit code 0=clean, 2=drift, 1=error)
tofu -chdir=infra/envs/prod/network plan -detailed-exitcode -lock-timeout=5m -input=false -out=tfplan.binary
tofu -chdir=infra/envs/prod/network show -json tfplan.binary > tfplan.json
```
