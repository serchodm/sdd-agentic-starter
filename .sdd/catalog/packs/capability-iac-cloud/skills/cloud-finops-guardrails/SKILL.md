---
name: cloud-finops-guardrails
description: Cloud FinOps cost governance and engineering guardrails covering mandatory resource tagging (env, service, owner, cost-center), pre-provisioning budget and Infracost PR gates, workload rightsizing, log/snapshot/bucket lifecycle retention policies, and hidden cost controls (NAT Gateways, cross-AZ egress, serverless recursion/retry loops) across AWS, GCP, and Azure. Use when designing, provisioning, or optimizing cloud infrastructure under SDD Gate 2 and Gate 4.
---

# Cloud FinOps Guardrails

Engineering-first Cloud FinOps playbook that shifts cost accountability left into Gate 2 architecture and Gate 4 IaC automation, preventing unattributed spend, storage sprawl, and runaway cloud bills across AWS, GCP, and Azure.

## 1. When to Activate

Activate this skill whenever a Work Item (`FEAT-XXX`, `CR-XXX`, or `BUG-XXX`) involves any of the following:

- Provisioning new cloud accounts, VPCs, compute clusters, databases, storage buckets, queues, or serverless workloads.
- Defining or enforcing mandatory FinOps tag/label schemas for cost allocation and chargeback/showback.
- Estimating monthly infrastructure cost deltas in Pull Requests (`Infracost`) or configuring cloud billing budgets and anomaly alerts.
- Designing autoscaling bounds, non-prod shutdown schedules, compute rightsizing, or storage/log retention lifecycles.
- Reviewing architectures susceptible to hidden cloud multipliers: NAT Gateway data processing, cross-AZ/internet egress, infinite log retention, orphaned snapshots, or serverless retry/recursion loops.

## 2. Production Architecture & Patterns

### 2.1. Mandatory Resource Tagging & Allocation Taxonomy

Untagged infrastructure creates dark spend that cannot be traced to a team or product. Every billable cloud resource MUST carry the 4 mandatory FinOps tags/labels:

| Tag / Label Key | Required Format | Example | Purpose |
| :--- | :--- | :--- | :--- |
| `env` | `dev \| staging \| prod \| sandbox` | `prod` | Separates production COGS from non-prod R&D spend. |
| `service` | Kebab-case bounded context / app | `orders-api` | Maps cloud cost directly to a catalog service and SLO. |
| `owner` | Team slug or distribution email | `team-checkout` | Identifies the accountable team for alerts and cleanup. |
| `cost-center` | Finance ledger code | `cc-4200-core` | Enables automated showback/chargeback and budget scoping. |

- **Provider-Level Default Enforcement:** Apply mandatory tags automatically via AWS provider `default_tags`, GCP provider `default_labels`, or a centralized `local.common_tags` map merged into every Azure resource.
- **Fail-Closed Tag Enforcement:** Validate presence and regex compliance of all 4 keys in CI (Checkov/OPA/Conftest + `tofu test`) and at cloud organization level (AWS Tag Policies, GCP Org Policy / Label validator, Azure Policy `Require a tag on resources`).

```hcl
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      env         = var.environment
      service     = var.service_name
      owner       = var.owner_team
      cost-center = var.cost_center
      managed-by  = "opentofu"
    }
  }
}
```

### 2.2. Pre-Provisioning Budget Gates & Cost Anomaly Alerts

Never deploy net-new infrastructure without an explicit cost ceiling and automated alerting before spend occurs.

- **Shift-Left PR Cost Estimation (`Infracost`):** Run `infracost diff` on every IaC Pull Request to surface exact monthly cost delta (`+$X/mo`). Configure a fail-closed CI guard requiring `@architect` / FinOps owner approval whenever a single PR increases projected monthly spend above the project threshold (e.g., `> $200/mo` or `> 15%`).
- **Cloud Budgets & Anomaly Monitors:** Provision budgets via IaC (`aws_budgets_budget`, `google_billing_budget`, `azurerm_consumption_budget_subscription`) scoped per account/project or `cost-center` tag with multi-tier notifications:
  - **50% actual:** informational notice to team channel.
  - **80% actual & 100% forecasted:** high-priority alert to `owner` + `@devops`.
  - **100% actual:** incident escalation + optional automated freeze on non-prod scale-out.
- **Anomaly Detection:** Enable `aws_ce_anomaly_monitor` / GCP Billing anomaly alerts / Azure Cost Management anomaly alerts with daily cadence so sudden spikes (e.g., misconfigured polling loop) are caught within 24 hours rather than at month-end invoice.

```hcl
resource "aws_budgets_budget" "service_monthly" {
  name         = "${var.service_name}-${var.environment}-monthly"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  cost_filter {
    name   = "TagKeyValue"
    values = ["user:service$${var.service_name}", "user:env$${var.environment}"]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "ACTUAL"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.owner_alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "FORECASTED"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.owner_alert_email]
  }
}
```

### 2.3. Workload Rightsizing & Bounded Elasticity

- **Right-Size Before Committing:** Start new services on measured baseline instances (prefer ARM64/Graviton/Tau T2A for ~20% better price-performance where runtime supports it) and review p95 CPU/memory utilization over 14–30 days before purchasing Savings Plans or Committed Use Discounts (CUDs).
- **Mandatory Autoscaling Ceilings:** Every Auto Scaling Group, Kubernetes HPA/KEDA scaler, Cloud Run service, or DynamoDB/Aurora autoscaler MUST define an explicit `max_capacity` / `max_instances` ceiling calculated from Gate 2 traffic projections. Unbounded autoscaling converts a DDoS or retry storm into an unbounded cloud bill.
- **Non-Prod Hibernation:** Schedule `dev` and `staging` compute clusters, preview environments, and non-prod databases to stop or scale to zero outside working hours (typically cutting non-prod compute spend by 60–70%).
- **Spot / Preemptible for Fault-Tolerant Compute:** Run stateless batch jobs, CI build agents, and interruptible worker pools on Spot/Preemptible capacity with graceful termination handling and on-demand fallback.

### 2.4. Log, Snapshot & Object Storage Lifecycle Policies

Storage and observability costs compound silently when retention defaults to "Never Expire".

- **Explicit Log Retention:** Every CloudWatch Log Group, GCP Cloud Logging bucket, and Azure Log Analytics Workspace MUST declare explicit `retention_in_days` (e.g., `7–14` days in `dev`, `30–90` days hot in `prod`, archived to compressed object storage only when regulatory retention is required). Drop high-volume debug/healthcheck logs at ingestion.
- **Object Storage Lifecycle Rules:** Attach lifecycle rules to every S3/GCS/Azure Blob container:
  1. Abort incomplete multipart uploads after `7` days (`abort_incomplete_multipart_upload`).
  2. Transition infrequently accessed objects to Infrequent Access / Nearline / Cool after `30` days and Archive/Glacier/Coldline after `90–180` days (only for objects `>= 128 KB` to avoid minimum-size surcharges).
  3. Expire noncurrent object versions (`noncurrent_days = 30–90`) and ephemeral staging buckets automatically.
- **Orphan & Artifact Hygiene:** Enforce lifecycle policies on container registries (keep last `N` tagged release images, expire untagged digests after `7` days), prune snapshots older than the RPO/compliance window, and alert on unattached block volumes (EBS/PD/Managed Disks) and idle Elastic/Static IPs.

### 2.5. Hidden Cloud Cost Controls (The Silent Bill Multipliers)

Explicitly audit and mitigate the 3 most common hidden cloud cost traps in every Gate 2 review:

1. **NAT Gateway & Managed Proxy Data Processing:**
   - AWS NAT Gateways charge both per-hour AND per-GB processed. Deploy free **Gateway VPC Endpoints** for S3 and DynamoDB in every VPC immediately.
   - Evaluate Interface VPC Endpoints vs NAT throughput breakeven for high-volume ECR, CloudWatch, or Secrets Manager traffic.
   - Use 1 shared NAT Gateway in `dev`/`staging` (accepting single-AZ resilience) and multi-AZ NAT Gateways only in `prod`.
2. **Cross-AZ & Internet Egress:**
   - Cross-AZ traffic between chatty microservices, Kafka brokers, or Redis clusters incurs per-GB transfer charges (`~$0.01/GB` each direction). Enable topology-aware routing (Kubernetes Topology Aware Hints, ALB cross-zone trade-offs, local AZ read replicas where applicable).
   - Serve static assets and downloads through a CDN (CloudFront, Cloud CDN, Azure Front Door) with high cache-hit ratios rather than direct bucket internet egress.
   - Restrict cross-region replication strictly to disaster-recovery datasets documented in Gate 2.
3. **Serverless Retry Loops, Recursion & Unbounded Scans:**
   - Set `reserved_concurrent_executions` / `max_instances` caps and tight function `timeout` values on every Lambda, Cloud Function, or Azure Function.
   - Bound async retries (`maximum_retry_attempts = 2`, SQS `maxReceiveCount <= 3`) with a Dead Letter Queue, and enable **Lambda Recursive Loop Detection** (`RecursiveLoop = "Terminate"`) so an S3/SQS/SNS feedback loop cannot execute millions of invocations in minutes.
   - Enforce query byte caps on serverless analytics (`maximum_bytes_billed` in BigQuery, `bytes_scanned_cutoff_per_query` in Athena workgroups) to block accidental full-table scans.

## 3. SDD Gate 2 & Gate 4 Contract Alignment

- **Gate 2 (`02-tech-spec.md`):** `@architect` and `@devops` must document a **FinOps Cost Profile** section containing:
  1. Expected monthly baseline cost and peak-load ceiling (`USD/month`) plus budget alert recipients.
  2. Mandatory tag values (`env`, `service`, `owner`, `cost-center`) and autoscaling `min`/`max` caps.
  3. Retention table for logs, backups/snapshots, object storage buckets, and container registries.
  4. Explicit review of hidden cost multipliers (VPC endpoints, cross-AZ traffic, serverless concurrency/recursion guards).
- **Gate 4 (`@devops` & `@qa-tester`):**
  - Implement provider default tags, budget alerts, lifecycle policies, and concurrency/scaling caps matching Gate 2 (`sdd-spec-compliance-audit`).
  - Attach `infracost diff` output to the Gate 4 verification evidence and verify all tag/retention assertions in `*.tftest.hcl` (see `terraform-opentofu-patterns`).

## 4. Anti-Patterns & Fail-Closed Guards

| Anti-Pattern | Failure Mode | Fail-Closed Guard |
| :--- | :--- | :--- |
| Missing FinOps tags (`env`, `service`, `owner`, `cost-center`) | Unallocated dark spend; impossible to assign cost spikes to an owner. | Enforce provider `default_tags`/`default_labels` and fail CI policy checks on any resource missing the 4 keys. |
| CloudWatch / Log groups without `retention_in_days` | Logs default to infinite retention and grow monotonically forever. | Require explicit `retention_in_days` on every log group via Checkov/OPA and unit tests. |
| S3 / DynamoDB traffic routed through AWS NAT Gateways | Unnecessary `$0.045/GB` NAT processing charges on internal AWS traffic. | Provision free S3 and DynamoDB Gateway VPC Endpoints in every VPC module by default. |
| Unbounded serverless concurrency or missing DLQ/recursion limits | A single malformed event or S3 write-back trigger causes a $10k+ overnight bill. | Mandate `reserved_concurrent_executions` / `max_instances`, bounded retries + DLQ, and recursive loop termination. |
| No `infracost diff` or cloud budget alerts | Expensive instance typos (`db.r6g.16xlarge`) go unnoticed until month-end invoice. | Run `infracost diff` in PR CI with fail-closed delta gate and provision `50%/80%/100%` billing budgets in IaC. |
| Leaving `dev`/`staging` clusters running 24/7 and orphaned disks unpruned | 60%+ wasted non-prod compute and zombie storage charges accumulate monthly. | Automate off-hours hibernation schedules and enforce snapshot/EBS/ECR cleanup lifecycle rules. |

## 5. Deterministic Verification Commands

Use these deterministic commands during Gate 4 DoD verification (adapt paths and cloud profiles to `specs/STACK.md`):

```bash
# 1. Estimate monthly IaC cost breakdown and fail on unexpected PR cost delta via Infracost
infracost breakdown --path infra/envs/prod --format table --out-file infracost-base.json
infracost diff --path infra/envs/prod --compare-to infracost-base.json --format table

# 2. Audit mandatory FinOps tags and log/storage lifecycle policies in IaC
checkov -d infra/ --framework terraform --check CKV_AWS_158,CKV_AWS_338,CKV2_AWS_61,CKV_GCP_78 --compact

# 3. Verify zero AWS CloudWatch log groups exist with infinite (unset) retention
aws logs describe-log-groups \
  --query 'logGroups[?retentionInDays==null].logGroupName' --output text

# 4. Detect orphaned unattached EBS volumes and idle unassociated Elastic IPs
aws ec2 describe-volumes --filters "Name=status,Values=available" \
  --query 'Volumes[].{ID:VolumeId,SizeGiB:Size,Created:CreateTime}' --output table
aws ec2 describe-addresses --query 'Addresses[?AssociationId==null].PublicIp' --output text

# 5. Verify active AWS Budgets and Anomaly Monitors are provisioned
aws budgets describe-budgets --account-id "${AWS_ACCOUNT_ID}" \
  --query 'Budgets[].{Name:BudgetName,Limit:BudgetLimit.Amount,Unit:BudgetLimit.Unit}' --output table
```
