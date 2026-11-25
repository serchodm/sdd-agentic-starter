---
name: cloud-iam-security
description: Cloud IAM and infrastructure security playbook enforcing strict least privilege (blocking wildcard Action/Resource grants), keyless CI/CD OIDC federation, VPC private subnet segmentation, customer-managed KMS encryption, and runtime secret managers aligned with .agents/rules/05-security-and-secrets.md across AWS, GCP, and Azure. Use when designing, implementing, or auditing cloud identities, network boundaries, encryption, or secret pipelines under SDD Gate 2 and Gate 4.
---

# Cloud IAM & Infrastructure Security

Zero-Trust cloud security playbook enforcing fail-closed least-privilege IAM, short-lived keyless federation, defense-in-depth network isolation, customer-managed cryptographic controls, and zero-secret IaC pipelines across AWS, GCP, and Azure.

## 1. When to Activate

Activate this skill whenever a Work Item (`FEAT-XXX`, `CR-XXX`, or `BUG-XXX`) involves any of the following:

- Authoring or reviewing AWS IAM policies/roles/SCPs, GCP IAM bindings/custom roles/Org Policies, or Azure RBAC role assignments/Managed Identities.
- Configuring CI/CD deployment authentication (GitHub Actions, GitLab CI, Bitbucket Pipelines) to cloud accounts without static credentials.
- Designing VPC/VNet CIDR layouts, public/private/isolated subnet tiers, Security Groups, NACLs, Firewalls, or Private Endpoints.
- Provisioning KMS keys, Cloud KMS key rings, Azure Key Vault encryption, or TLS termination certificates.
- Integrating runtime secret stores (AWS Secrets Manager, SSM Parameter Store, GCP Secret Manager, Azure Key Vault, HashiCorp Vault) aligned with `.agents/rules/05-security-and-secrets.md`.
- Performing STRIDE threat modeling in Gate 2 or OWASP/ASVS cloud infrastructure audits with `sdd-security-audit` in Gate 4.

## 2. Production Architecture & Patterns

### 2.1. Strict Least-Privilege IAM & Guardrail Hierarchy

Every workload identity MUST receive the minimum set of actions, target resources, and contextual conditions needed for its exact runtime responsibility.

- **Hard Ban on Unjustified Wildcards:** Reject `Action: "*"`, `Action: "s3:*"` / `iam:*`, and `Resource: "*"` in AWS policies; reject `roles/owner`, `roles/editor`, and project-wide broad roles in GCP; reject `Owner` and `Contributor` at subscription or management-group scope in Azure. Where a read-only discovery action genuinely requires `Resource: "*"` (e.g., `ec2:DescribeSubnets`), document the exception and constrain it with `Condition` keys (`aws:RequestedRegion`, `aws:PrincipalOrgID`, `aws:ResourceTag/env`).
- **One Identity Per Workload:** Assign a dedicated IAM Role (IRSA / EKS Pod Identity / ECS Task Role), GCP Service Account (Workload Identity Federation), or Azure User-Assigned Managed Identity per microservice. Never share a single deployment or runtime role across services or environments.
- **Prevent Privilege Escalation:** Attach IAM Permission Boundaries to every role created by application teams, block `iam:PassRole` with wildcard resources, and enforce organization-level guardrails (AWS SCPs, GCP Organization Policies, Azure Policy) denying disabling of audit trails (`CloudTrail`, `Cloud Audit Logs`, `Activity Log`) or public storage exposure.

```hcl
data "aws_iam_policy_document" "orders_worker" {
  statement {
    sid    = "ReadOrderQueue"
    effect = "Allow"
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
    ]
    resources = [aws_sqs_queue.orders.arn]
  }

  statement {
    sid     = "DecryptOrdersKeyViaSqsOnly"
    effect  = "Allow"
    actions = ["kms:Decrypt", "kms:GenerateDataKey"]
    resources = [aws_kms_key.orders.arn]
    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["sqs.${var.aws_region}.amazonaws.com"]
    }
  }
}
```

### 2.2. Keyless CI/CD OIDC Federation

Static cloud access keys (`AWS_ACCESS_KEY_ID`, GCP service account JSON files, Azure SPN client secrets) are prohibited in CI/CD pipelines per `.agents/rules/05-security-and-secrets.md`.

- **Short-Lived OIDC Tokens:** Configure cloud OIDC trust relationships with GitHub Actions (`token.actions.githubusercontent.com`), GitLab CI, or Workload Identity Pools so runners exchange signed OIDC JWTs for short-lived STS credentials (`max_session_duration <= 3600s`).
- **Strict Subject (`sub`) Scoping:** Bind trust policies to an exact repository AND branch or protected deployment environment (`repo:org/repo:environment:prod`). Never allow wildcard subjects such as `repo:org/*:*` or untrusted pull-request branches to assume deployment roles.
- **Plan vs Apply Role Separation:** Grant PR validation workflows a read-only `plan` role and restrict the mutating `apply` role strictly to protected branches/environments requiring human approval.

```hcl
data "aws_iam_policy_document" "github_oidc_trust" {
  statement {
    sid     = "AllowGitHubProdDeploy"
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_org}/${var.github_repo}:environment:production"]
    }
  }
}
```

### 2.3. VPC & Private Subnet Segmentation

Design cloud networks using 3-tier isolation so application and data layers are unreachable from the public internet:

| Tier | Exposure | Allowed Resources | Mandatory Guardrails |
| :--- | :--- | :--- | :--- |
| **Public Tier** | Internet-facing ingress only | ALB/NLB, Cloud Load Balancing, Azure Front Door/App Gateway, NAT Gateways | WAF attached, TLS 1.2+/1.3 only, zero compute SSH/RDP (`22`/`3389`) from `0.0.0.0/0`. |
| **Private App Tier** | No public IPs; outbound via NAT/Proxy | Containers, Kubernetes nodes, serverless VPC connectors, internal APIs | Default-deny Security Groups referencing peer SG IDs (not wide CIDRs); IMDSv2 (`http_tokens = "required"`). |
| **Isolated Data Tier** | No internet route (`0.0.0.0/0` absent) | RDS/Aurora, Cloud SQL, Azure PostgreSQL, Redis, Kafka, OpenSearch | Inbound strictly from App Tier SG on exact DB port; private DNS + TLS enforced (`rds.force_ssl = 1`). |

- **Private Service Connectivity:** Route cloud API traffic (S3, DynamoDB, Secrets Manager, KMS, ECR, GCS, Key Vault) over VPC Gateway/Interface Endpoints, GCP Private Service Connect, or Azure Private Endpoints instead of traversing the public internet.
- **Zero Bastion SSH:** Replace public bastion hosts with audited, session-logged identity-aware access (AWS Systems Manager Session Manager, GCP IAP TCP forwarding, Azure Bastion with Entra ID).

### 2.4. KMS Encryption & Cryptographic Hygiene

- **Customer-Managed Keys (CMK/CMEK):** Encrypt stateful storage (databases, object buckets, block volumes, queues, backups, container registries, remote IaC state) with dedicated per-domain KMS keys rather than default cloud-managed keys when compliance, cross-account isolation, or cryptographic revocation is required.
- **Rotation & Deletion Protection:** Enable automatic annual key rotation (`enable_key_rotation = true` in AWS, `rotation_period = "7776000s"` in GCP), set deletion windows to at least 30 days (`deletion_window_in_days = 30`), and restrict `kms:Decrypt` via explicit key policies + `kms:ViaService` conditions.
- **Encryption in Transit:** Enforce TLS `1.2` minimum (prefer `1.3`) on all load balancers, service meshes, database connections, and bucket policies (`aws:SecureTransport = false` explicit `Deny`).

### 2.5. Secret Managers Aligned with `.agents/rules/05-security-and-secrets.md`

IaC provisions secret **containers**, access policies, and rotation schedules — NEVER plaintext secret **values**.

- **Zero Secrets in IaC or State:** Never pass real passwords, API keys, or private keys through `.tfvars`, `locals`, default variable values, or `aws_secretsmanager_secret_version` with literal strings (which persist in plaintext inside `terraform.tfstate`).
- **Out-of-Band or Managed Generation:** Use cloud-managed secret generation (`manage_master_user_password = true` on AWS RDS) or seed secret payloads out-of-band / via CI secret sync, and consume secrets at runtime through Workload Identity / CSI Secrets Store Driver.
- **Automated Rotation & Audit:** Configure automatic rotation intervals (`<= 90 days` for DB/service credentials), enable secret access audit logging, and block secret read permissions from CI deployment roles that do not need runtime secret values.

## 3. SDD Gate 2 & Gate 4 Contract Alignment

- **Gate 2 (`02-tech-spec.md`):** `@architect` and `@security-reviewer` (with `@devops`) must define:
  1. Identity Matrix: every workload role/service account, exact allowed actions, target resource ARNs/IDs, condition keys, and OIDC trust subjects.
  2. Network Topology: CIDR allocation, subnet tiers, allowed SG/firewall ingress/egress flows, and Private Endpoints.
  3. Data Protection & Secrets Table: KMS key ownership, rotation policy, TLS policy, and secret manager paths (zero plaintext values).
  4. STRIDE threat model cross-referenced with `.agents/rules/05-security-and-secrets.md` and `sdd-security-audit`.
- **Gate 4 (`@devops` & `@security-reviewer`):**
  - Implement IAM, network, KMS, and secret manager modules matching the Gate 2 Identity Matrix verbatim (verified via `sdd-spec-compliance-audit`).
  - Run automated IAM policy analyzers, IaC security scanners (`trivy`, `checkov`), and secret scanners (`gitleaks`) with fail-closed exit codes; escalate critical security findings to `santa-method` dual verification before Gate 5.

## 4. Anti-Patterns & Fail-Closed Guards

| Anti-Pattern | Failure Mode | Fail-Closed Guard |
| :--- | :--- | :--- |
| Wildcard IAM (`Action: "*"` or `Resource: "*"` / `roles/editor`) | Single compromised workload achieves full account takeover or data exfiltration. | Scope every statement to explicit actions + resource ARNs + condition keys; block wildcards in Checkov/Trivy/IAM Access Analyzer. |
| Static cloud access keys stored in CI secrets | Leaked long-lived credentials grant persistent unauthorized access without automatic expiry. | Enforce keyless OIDC federation scoped to exact `repo` + `environment` with `<= 1h` session duration. |
| `0.0.0.0/0` ingress on SSH (`22`), RDP (`3389`), or DB ports | Automated internet scanners exploit exposed management or database interfaces within minutes. | Place compute/DB in private/isolated subnets; enforce SSM/IAP/Bastion and deny `0.0.0.0/0` on non-HTTP(S) ports in CI policy checks. |
| Hardcoding secret values in `.tfvars` or IaC resources | Secrets leak into Git history and `terraform.tfstate` in plaintext (violates `.agents/rules/05-security-and-secrets.md`). | Provision only secret containers and IAM policies in IaC; use managed passwords or out-of-band rotation and block commits with `gitleaks`. |
| Missing `aws:SecureTransport` deny or disabled KMS key rotation | Downgrade attacks expose data in transit; long-lived static key material increases cryptographic blast radius. | Attach explicit HTTPS-only bucket policies and require `enable_key_rotation = true` on all CMKs. |
| Shared IAM role across `dev` and `prod` or across services | Lateral movement from low-trust non-prod environment compromises production data. | Enforce strict per-environment accounts/projects and one dedicated identity per service. |

## 5. Deterministic Verification Commands

Use these deterministic commands during Gate 4 DoD verification (adapt cloud CLI profile/project to `specs/STACK.md`):

```bash
# 1. Fail-closed secret scanning across repository history and working tree
gitleaks detect --source=. --no-banner --redact --exit-code 1

# 2. Scan IaC HCL and plan JSON for IAM wildcards, public exposure, and missing KMS encryption
trivy config --severity HIGH,CRITICAL --exit-code 1 infra/
checkov -d infra/ --framework terraform --check CKV_AWS_107,CKV_AWS_108,CKV_AWS_109,CKV_AWS_111,CKV_AWS_145,CKV_GCP_62,CKV_AZURE_35 --compact

# 3. Validate AWS IAM policy documents for syntax and security warnings via IAM Access Analyzer
aws accessanalyzer validate-policy \
  --policy-type IDENTITY_POLICY \
  --policy-document file://infra/policies/orders-worker.json \
  --query 'findings[?findingType==`ERROR` || findingType==`SECURITY_WARNING`]'

# 4. Verify zero public access blocks disabled on AWS S3 and check IMDSv2 enforcement
aws s3api get-public-access-block --bucket "${TARGET_BUCKET}" --output json
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running" \
  --query 'Reservations[].Instances[?MetadataOptions.HttpTokens!=`required`].InstanceId' --output text

# 5. Verify GCP IAM policy has zero broad Owner/Editor bindings assigned to workload service accounts
gcloud projects get-iam-policy "${GCP_PROJECT_ID}" \
  --flatten="bindings[].members" \
  --filter="bindings.role:(roles/owner OR roles/editor) AND bindings.members:serviceAccount:*" \
  --format="table(bindings.role,bindings.members)"
```
