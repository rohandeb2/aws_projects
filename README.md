# AWS DevOps Projects — Real-World Infrastructure Solutions

A curated collection of **production-grade AWS infrastructure projects** — each one solving a real-world problem using AWS services, Infrastructure as Code, and DevOps best practices.

This repository is a **living portfolio** of hands-on projects. New mini-projects solving specific infrastructure challenges are added regularly.

---

## 🎯 What This Repo Contains

Each project is **self-contained** with:
- ✅ Complete step-by-step deployment guide
- ✅ Architecture diagrams and explanations  
- ✅ Production-ready configurations
- ✅ Proof of work (screenshots, test results)
- ✅ Lessons learned and gotchas documented

**No cookie-cutter tutorials.** Each project teaches an architecture pattern used by real companies.

---

## 📚 Projects by Domain

### 🌐 **Content Delivery & Static Hosting**

#### Static Website Hosting
**Directory:** `static_website_hosting/`  
**Stack:** S3 · CloudFront · ACM · Route53 · GoDaddy  
**Difficulty:** Beginner  
**Problem Solved:** How do I host a website without managing servers or worrying about SSL certificates?

Deploy a static portfolio/landing page globally with auto-renewing HTTPS, CDN caching, and zero server maintenance.

**Key Learning:** Origin Access Control (OAC) — how to keep S3 private while serving through CloudFront securely.

---

### 🔌 **Networking & VPC Architecture**

#### Custom VPC with Public/Private Subnets
**Directory:** `production_vpc_architecture/`  
**Stack:** VPC · IGW · NAT Gateway · Route Tables · Security Groups · EC2  
**Difficulty:** Intermediate  
**Problem Solved:** How do I build a production VPC from scratch with proper network isolation?

Build a multi-AZ VPC with bastion hosts, private application servers, and NAT gateways. Proves that private servers can reach the internet outbound but are unreachable inbound.

**Key Learning:** Security group source can be another security group — this enables service-to-service access patterns without exposing IPs.

---

### ⚙️ **Compute & Scalability**

#### Auto Scaling Web Application with RDS
**Directory:** `autoscaling-rds-webapp/`  
**Stack:** EC2 · RDS · ALB · Auto Scaling Group · Secrets Manager  
**Difficulty:** Intermediate → Advanced  
**Problem Solved:** How do I run a web app that auto-scales based on demand and connects securely to a database?

Deploy a Flask/Node app on an auto-scaling infrastructure. The load balancer distributes traffic across EC2s. The ASG scales from 1 → 4 instances based on CPU. Database credentials are injected at runtime via Secrets Manager — never hardcoded.

**Key Learning:** Secrets Manager integration patterns. Health checks in target groups. Launch template user data scripts for zero-touch server initialization.

---

### 🐳 **Container Orchestration**

#### Production Container Platform (ECS Fargate)
**Directory:** `production_container_platform/`  
**Stack:** Docker · ECR · ECS Fargate · ALB · Secrets Manager · CloudWatch  
**Difficulty:** Advanced  
**Problem Solved:** How do I deploy containerized microservices without managing Kubernetes or EC2s?

Package a Flask application as a Docker container. Push to ECR. Deploy to ECS Fargate with staging and production environments on a single ALB. Auto-scale tasks based on CPU. All logs stream to CloudWatch automatically.

**Key Learning:** Task definitions (the blueprint for containers). Service auto-scaling. Rolling deploys with zero downtime. Secrets injection at container start time.

---

## 🚀 Quick Start

Each project is independent. Choose one and follow its deployment guide.

**Prerequisites (for all projects):**
- AWS account (with admin access for learning)
- AWS CLI configured: `aws configure`
- Basic understanding of AWS services
- Terminal/CLI access

**To get started with any project:**

```bash
# Clone this repo
git clone https://github.com/yourusername/aws-devops-projects.git
cd aws-devops-projects

# Navigate to the project
cd static_website_hosting/
# (or autoscaling-rds-webapp/, production_container_platform/, etc.)

# Read the deployment guide
cat deployment_guide.md

# Follow the step-by-step instructions in order
```

**Region Preference:** Most projects are configured for `ap-south-1` (Mumbai). Adjust region names in guides if deploying elsewhere.

---

## 📖 How to Read Each Project

1. **readme.md** — Architecture overview, services used, proof of work
2. **deployment_guide.md** — Step-by-step AWS Console walkthrough (no IaC in some projects; raw Terraform coming soon)
3. **Proof of work screenshots** — Real deployments showing it works end-to-end

---

## 💰 Cost Awareness

Each project includes a cost breakdown. Most are designed to run for **learning only** (1–2 days) to keep costs minimal.

**Typical costs per project:**
- Static Website: ~$0.50/month
- VPC: ~$32/month (NAT Gateway — delete after learning)
- Auto Scaling: ~$2–5/day (delete same day)
- ECS Fargate: ~$2/day (delete same day)

**Important:** **Always delete resources immediately after learning.** Set phone reminders if needed. Forgotten resources can cost hundreds per month.

---

## 🎓 What You'll Learn

By working through these projects, you'll understand:

- ✅ How to think about architecture problems first, services second
- ✅ Security patterns (OAC, security groups, IAM roles, Secrets Manager)
- ✅ Scalability patterns (Auto Scaling, load balancing, multi-AZ)
- ✅ Networking patterns (VPC, subnets, route tables, bastion hosts)
- ✅ Container orchestration (Docker, ECR, ECS, task definitions)
- ✅ Observability (CloudWatch Logs, Container Insights, metrics)
- ✅ How to debug AWS services when things break
- ✅ AWS best practices used in real companies

---

## 🛠 Contributing

This is a personal learning portfolio, but if you find bugs in guides or want to suggest improvements:

1. Open an issue describing the problem
2. Include:
   - Which project + which step
   - What you expected vs. what happened
   - AWS Console screenshots if relevant
3. I'll review and update the guide

**Future project ideas welcome.** If you've built something interesting on AWS, you can submit it as a PR with the same structure (readme + deployment_guide + proof of work).

---

## 🔗 Connect

- **Live Portfolio:** [rohandevops.co.in](https://rohandevops.co.in)
- **LinkedIn:** [linkedin.com/in/ruhon-deb](https://www.linkedin.com/in/ruhon-deb)
- **Email:** ruhondeb28@gmail.com
- **GitHub:** [github.com/rohandeb2](https://github.com/rohandeb2)

---

## ⚡ Tips for Learning

1. **Read the architecture diagram first** before touching AWS Console
2. **Understand the "why"** before following steps — each guide explains why each resource is needed
3. **Take screenshots** at key checkpoints (some guides have 80+ steps)
4. **Test immediately** after deployment using the provided test commands
5. **Break it intentionally** — delete a security group or change a route table to see what breaks
6. **Read the error messages** — AWS errors are usually very specific about what went wrong
7. **Delete everything** at the end to avoid surprise bills

---

## 📝 License

This repository contains educational material and deployment guides. Feel free to use these patterns in your own AWS projects.

---

## 🙏 Acknowledgments

These projects are based on:
- AWS Architecture Best Practices
- Production patterns from real-world DevOps teams
- AWS Well-Architected Framework
- Hands-on troubleshooting and learning

---

## FAQ

**Q: Can I use these projects for work?**  
A: Yes. These are production-ready patterns. Adjust resource names, regions, and scaling parameters for your use case.

**Q: Why are some projects done in AWS Console instead of Terraform?**  
A: Console walkthroughs teach AWS service behavior and help you understand what Terraform generates. IaC versions are being added for each project.

**Q: Which project should I start with?**  
A: Start with **Static Website Hosting** if you're new to AWS (simplest, lowest cost). Then **Custom VPC** to understand networking. Then combine both ideas in **Auto Scaling Web App**.

**Q: How long does each project take?**  
A: 3–4 hours if you read carefully and test thoroughly. Faster if you've seen similar patterns.

**Q: Will these projects help me get a DevOps job?**  
A: Yes. These cover the core architecture patterns used in real companies. Add them to your portfolio, link them from your resume, and explain what you learned in interviews.
