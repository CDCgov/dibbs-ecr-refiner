# Vulnerability Scanning and Management

To protect our software supply chain and infrastructure, we employ a multi-layered vulnerability management strategy. We use **Dependabot** for proactive dependency updates, a custom script running **Trivy** during CI/CD builds, and **AWS Inspector** for production image compliance.

| Tool                              | Phase / Layer Scanned                   | Primary Action                                                     |
| :-------------------------------- | :-------------------------------------- | :----------------------------------------------------------------- |
| **Dependabot**                    | Source Code & Package Registries        | Proactive weekly PRs for out-of-date application dependencies      |
| **Trivy (`security-summary.js`)** | CI/CD Pipeline & OCI Container Layers   | PR feedback, Slack alerts, and automated Risk Exception generation |
| **AWS Inspector**                 | Pre-Release Audit & Production Registry | Enforcement threshold for releases (APHL board sign-off)           |

---

## Dependabot (Dependency Management)

Dependabot is configured via `.github/dependabot.yml` in our GitHub repository. It monitors packages across our frontend, backend, and Docker registries, automatically opening PRs every Monday to update out-of-date dependencies.

Developers regularly review, triage, and implement any necessary code changes to merge these updates as part of ongoing maintenance.

- For more details, see the [GitHub Dependabot Documentation](https://docs.github.com/en/code-security/tutorials/secure-your-dependencies/dependabot-quickstart).

---

## Trivy Pipeline Scanning (`security-summary.js`)

In addition to application dependency maintenance, our pipeline runs [Trivy](https://trivy.dev/) on bundled container images. This ensures visibility into security vulnerabilities within underlying base Docker images and system libraries. Results are reported directly in GitHub Pull Requests and dispatched to Slack for developer action.

### 🚀 Features

- **JSON Parsing**: Aggregates output files matching the pattern `trivy-{image-name}-results.json`.
- **PR Feedback**: Dynamically creates or updates a summary comment on GitHub Pull Requests.
- **Slack Alerts**: Sends rich Block Kit messages with color-coded severity indicators for scheduled runs.
- **Risk Exception Generator**: Automatically generates a pre-filled `risk-exception.md` template for `CRITICAL` and `HIGH` vulnerabilities requiring formal justification.
- **Targeted Container Images**: Configured by default for `refiner-app`, `refiner-lambda`, and `refiner-ops`.

---

### 📋 Prerequisites

To execute `security-summary.js` within GitHub Actions:

- **Node.js**: `v18+` (utilizes native `fetch`).
- **GitHub Actions Context**: Access to `@actions/core` and `@actions/github` via `actions/github-script`.
- **Input Artifacts**: Pre-generated Trivy JSON scan output matching `trivy-{image}-results.json`.

---

### 🛠️ Entry Points

The script exports three main functions for use in GitHub Workflow steps:

| Function                        | Workflow Trigger                 | Primary Action                                                                                             |
| :------------------------------ | :------------------------------- | :--------------------------------------------------------------------------------------------------------- |
| `generatePRSummary`             | `pull_request`                   | Parses Trivy JSON results, updates PR comments with metric tables, and flags High/Critical warnings.       |
| `generateScheduledSummary`      | `schedule` / `workflow_dispatch` | Sends color-coded scan metrics to Slack via webhook.                                                       |
| `generateRiskExceptionTemplate` | Any                              | Filters `CRITICAL` and `HIGH` CVEs and outputs a Markdown risk acceptance template to `risk-exception.md`. |

---

### ⚙️ Environment Variables

| Variable             | Required By                | Description                                                                 |
| :------------------- | :------------------------- | :-------------------------------------------------------------------------- |
| `SLACK_WEBHOOK_URL`  | `generateScheduledSummary` | Slack incoming webhook URL.                                                 |
| `RISK_EXCEPTION_URL` | `generateScheduledSummary` | Optional URL linking to downloadable scan artifacts in Slack notifications. |

---

## AWS Inspector & Release Governance

Prior to cutting a production release, **AWS Inspector** scans all bundled release images. Release gate policy dictates:

1. **Critical Vulnerabilities**: Must be resolved before release; zero-tolerance threshold.
2. **High Vulnerabilities**: Must be resolved or formally approved via a Security Risk Exception through the **APHL Security Review Board**.

Inspector scans also run periodically against the latest `main` branch. To streamline the exception approval process, the custom Trivy script (`generateRiskExceptionTemplate`) pre-fills boilerplate CVE metadata into `risk-exception.md`. The engineering team then adds specific mitigation strategies and submits the completed document to the APHL board for review prior to deployment.
