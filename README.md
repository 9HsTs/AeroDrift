# AeroDrift
AeroDrift – Agentic Cloud Topology & Remediation Graph

AeroDrift is an agentic CloudOps and infrastructure automation system designed to continuously monitor AWS environments, detect configuration drift, identify unauthorized network paths, and automatically remediate security anomalies.

The project combines AWS boto3, asyncio, NetworkX, Python AST, and Rich to create a cloud topology-aware remediation engine.

---

🚀 Project Overview

Cloud infrastructure can frequently drift from its intended security baseline due to manual configuration changes.

For example, an engineer may temporarily open a Security Group rule for SSH access and forget to remove it later. Traditional Infrastructure-as-Code tools such as Terraform can identify infrastructure drift, but remediation often requires manual intervention, pull requests, approvals, or a complete CI/CD deployment.

AeroDrift automates this process.

It continuously collects the current AWS infrastructure state, constructs an in-memory topology graph, detects unexpected configuration changes, analyzes the resulting network paths, generates remediation logic dynamically, and applies the required correction through AWS APIs.

---

🎯 Problem Statement

AWS environments can become inconsistent with their approved security configuration due to:

- Manual infrastructure changes
- Incorrect Security Group rules
- Temporary access that was never revoked
- Unauthorized network exposure
- Configuration drift
- Human error

AeroDrift aims to reduce the time between drift detection and remediation.

---

💡 Example Scenario

Consider a production database that should only be accessible from an internal application server.

Expected topology

Application Server
        |
        v
Security Group
        |
        v
Production Database

An engineer accidentally adds:

0.0.0.0/0 → Database Security Group

The resulting topology becomes:

Internet
    |
    v
Security Group
    |
    v
Production Database

AeroDrift detects the unauthorized path:

Internet → Security Group → Production Database

It then generates and executes the appropriate remediation action to revoke the unauthorized ingress rule and verifies the resulting AWS state.

---

🏗️ Architecture

                    AWS CLOUD
                       |
        +--------------+--------------+
        |              |              |
       VPC            EC2       Security Groups
        |              |              |
        +--------------+--------------+
                       |
                       v
              +----------------+
              | Cloud Ingestion|
              | boto3 + asyncio|
              +-------+--------+
                      |
                      v
              +----------------+
              | Topology Engine|
              |   NetworkX     |
              +-------+--------+
                      |
                      v
              +----------------+
              | Drift Detector |
              +-------+--------+
                      |
                      v
              +----------------+
              | AST Generator  |
              | Python ast     |
              +-------+--------+
                      |
                      v
              +----------------+
              | Remediation    |
              | Engine         |
              +-------+--------+
                      |
                      v
                 AWS APIs
                      |
                      v
              +----------------+
              | Audit Dashboard |
              |     Rich       |
              +----------------+

---


⚙️ Installation

Clone the repository:

git clone https://github.com/<your-username>/AeroDrift.git
cd AeroDrift

Create a virtual environment:

python -m venv venv

Activate it on Windows:

venv\Scripts\activate

Activate it on Linux/macOS:

source venv/bin/activate

Install dependencies:

pip install -r requirements.txt

---

🔐 AWS Configuration

AeroDrift requires AWS credentials with appropriate permissions.

Configure AWS CLI:

aws configure

Provide:

AWS Access Key ID
AWS Secret Access Key
Default Region
Output Format

For production deployments, use IAM roles and least-privilege permissions instead of storing credentials directly in the project.

---

▶️ Running the Project

Start AeroDrift:

python -m aerodrift.main

Example workflow:

[1] Collecting AWS state...
[2] Building topology graph...
[3] Comparing security baseline...
[4] Analyzing network paths...
[5] Drift detected!
[6] Generating remediation...
[7] Applying remediation...
[8] Verifying AWS state...
[9] Updating audit dashboard...

---

🧪 Testing

Run the test suite using:

pytest

Tests should cover:

- AWS resource collection
- Graph construction
- Path detection
- Drift detection
- Remediation generation
- Remediation verification

---

🔄 Workflow

AWS Infrastructure
       ↓
Cloud State Collection
       ↓
Topology Construction
       ↓
Baseline Comparison
       ↓
Drift Detection
       ↓
Network Path Analysis
       ↓
Remediation Generation
       ↓
AWS Remediation
       ↓
State Verification
       ↓
Audit Logging

---

🔒 Security Considerations

AeroDrift is designed for controlled CloudOps automation.

Recommended safeguards include:

- Least-privilege IAM policies
- Dry-run mode
- Remediation allowlists
- Validation before execution
- Post-remediation verification
- Detailed audit logging
- Idempotent remediation operations
- Approval policies for high-impact changes
- No hard-coded AWS credentials

Generated remediation code should be validated before execution and should never be treated as unrestricted arbitrary code.

---

📊 Future Enhancements

Potential future improvements include:

- Support for Google Cloud Platform (GCP)
- Terraform state integration
- Event-driven monitoring using AWS EventBridge
- Real-time topology visualization
- Web-based dashboard
- Slack/Teams notifications
- Machine-learning-based anomaly detection
- Policy-as-code integration
- Multi-account AWS support
- Automated rollback
- Human approval workflows for critical changes

---

🎯 Project Objectives

AeroDrift aims to:

- Detect cloud configuration drift automatically
- Identify unauthorized network paths
- Reduce manual CloudOps intervention
- Automate security-group remediation
- Maintain an auditable record of changes
- Provide topology-aware infrastructure analysis
- Demonstrate agentic infrastructure automation

---

📌 Project Status

Status: 🚧 In Development

AeroDrift is a project focused on demonstrating automated cloud infrastructure monitoring, topology analysis, drift detection, and controlled remediation.

---

👨‍💻 Author

Nishant Tandon

Computer Science / CloudOps Project

---
