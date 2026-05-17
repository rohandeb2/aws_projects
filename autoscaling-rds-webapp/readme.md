# DevOps Project 3 — Auto Scaling Web App with RDS, ALB & Secrets Manager

## Overview

This project deploys a **highly available, auto-scaling web application** on AWS using:

- **RDS MySQL** (private subnet, no public IP)
- **AWS Secrets Manager** (secure password storage — no hardcoded credentials)
- **Application Load Balancer (ALB)** (internet-facing, distributes traffic)
- **Auto Scaling Group (ASG)** (automatically launches/terminates EC2 instances)
- **EC2 Launch Template** (with User Data script for automated app setup)

Traffic flow: `Internet → ALB (public subnets) → EC2 app servers (private subnets) → RDS (private subnets)`

---

## Architecture

<div align="center">
  <img src="img/Screenshot 2026-05-17 095714.png" >
</div>

### AWS Resources Created

| Resource | Name |
|---|---|
| VPC | devops-project2-vpc (reused from Project 2) |
| RDS Subnet Group | devops-project3-rds-subnet-group |
| Secret | devops/project3/rds-password |
| RDS Instance | devops-project3-db |
| Security Group (ALB) | alb-sg |
| Security Group (EC2) | app-server-sg |
| Security Group (RDS) | rds-sg |
| IAM Role | ec2-secrets-manager-role |
| Launch Template | devops-project3-lt |
| Target Group | devops-project3-tg |
| Load Balancer | devops-project3-alb |
| Auto Scaling Group | devops-project3-asg |
| Bastion Server | (Project 2 VPC, public subnet, bastion-sg + app-server-sg) |

---

## Prerequisites

- AWS account with access to **ap-south-1 (Mumbai)** region
- Existing VPC from Project 2: `devops-project2-vpc`
  - private-subnet-1a (10.0.3.0/24)
  - private-subnet-1b (10.0.4.0/24)
  - public-subnet-1a, public-subnet-1b
- Key pair from Project 2: `devops-project2`
- Bastion server security group: `bastion-sg`

---

## Security Design

- RDS has **no public IP** — accessible only from app EC2s
- EC2 instances are in **private subnets** — only reachable via ALB
- Passwords are stored in **Secrets Manager** — never hardcoded in code or config
- ALB is the only internet-facing resource

## Proof of work:

<div align="center">
  <img src="img/Screenshot 2026-05-11 175217.png" >
</div>

<div align="center">
  <img src="img/Screenshot 2026-05-11 175222.png" >
</div>

<div align="center">
  <img src="img/Screenshot 2026-05-11 175250.png" >
</div>

<div align="center">
  <img src="img/Screenshot 2026-05-11 175254.png" >
</div>

<div align="center">
  <img src="img/Screenshot 2026-05-11 175258.png" >
</div>

<div align="center">
  <img src="img/Screenshot 2026-05-11 175303.png" >
</div>