# Deployment Guide — DevOps Project 3

> **Region:** ap-south-1 (Mumbai) — confirm this in the top-right corner of AWS Console before every step.

---

## Phase 1 — Create RDS Subnet Group

> RDS must always be in private subnets. It should never have a public IP.

### Step 1.1 — Go to RDS
- Search bar at top of AWS Console → type **RDS** → click RDS
- Confirm region: **ap-south-1 (Mumbai)** — top right corner

### Step 1.2 — Create Subnet Group
- Left sidebar → **Subnet groups** → **Create DB subnet group**
- **Name:** `devops-project3-rds-subnet-group`
- **Description:** `Private subnets for RDS`
- **VPC:** `devops-project2-vpc`
- **Availability Zones:** select `ap-south-1a` and `ap-south-1b`
- **Subnets:** select `private-subnet-1a (10.0.3.0/24)` and `private-subnet-1b (10.0.4.0/24)`
- Click **Create**

✅ **Checkpoint:** RDS subnet group created with both private subnets

---

## Phase 2 — Create RDS MySQL Database

### Step 2.1 — Create Security Group for RDS

> First, create a security group that only allows MySQL traffic from your EC2 instances.

- Go to **VPC → Security Groups → Create security group**
- **Name:** `rds-sg`
- **Description:** `Allow MySQL from app EC2 only`
- **VPC:** `devops-project2-vpc`
- **Inbound rules → Add rule:**
  - Type: `MySQL/Aurora`
  - Protocol: `TCP` (auto-filled)
  - Port: `3306` (auto-filled)
  - Source: `Custom` — **leave empty for now** (we will add `app-server-sg` after Phase 3)

> ⚠️ Leave source empty for now. We will come back and edit this after Phase 3.

- **Outbound:** leave default (allow all)
- Click **Create security group**

### Step 2.2 — Create RDS Database

- Go to **RDS → Databases → Create database**
- **Creation method:** Standard create
- **Engine:** MySQL
- **Engine version:** MySQL 8.0.x (latest minor version)
- **Templates:** Free tier

**Settings:**
- **DB instance identifier:** `devops-project3-db`
- **Master username:** `admin`
- **Master password:** use the SAME password you stored in Secrets Manager
- **Confirm password:** same again

**Instance configuration:**
- **DB instance class:** `db.t3.micro`

**Storage:**
- **Allocated storage:** 20 GB (minimum)
- **Enable storage autoscaling:** uncheck (not needed for practice)

**Connectivity:**
- **VPC:** `devops-project2-vpc`
- **DB subnet group:** `devops-project3-rds-subnet-group`
- **Public access:** **NO** — this is critical
- **VPC security group:** choose existing → select `rds-sg`
- **Availability Zone:** `ap-south-1a`

**Additional configuration:**
- **Initial database name:** `appdb`
- **Automated backups:** disabled (for practice — enable in real production)
- Click **Create database**

> ℹ️ RDS takes 5–10 minutes to become Available. Continue to Phase 3 while it creates.

### Step 2.3 — Copy RDS Endpoint
- After status shows **Available**, click your DB → copy the **Endpoint**
- It looks like: `devops-project3-db.xxxxxxxx.ap-south-1.rds.amazonaws.com`
- **Save this** — your app uses this to connect to the database

✅ **Checkpoint:** RDS created in private subnet. Endpoint copied. No public IP.

---

## Phase 3 — Store DB Password in Secrets Manager

> In production, you NEVER hardcode database passwords in code or config files. Secrets Manager stores them securely and your app fetches them at runtime.

> 🔴 This is a non-negotiable production practice. Any hardcoded password in code = immediate security incident.

### Step 3.1 — Go to Secrets Manager
- Search bar → **Secrets Manager** → click it

### Step 3.2 — Create Secret
- Click **Store a new secret**
- **Secret type:** Credentials for Amazon RDS database
- **Username:** `admin`
- **Password:** choose a strong password (e.g. `MySecurePass123!`) — note it down
- **Database:** skip for now (we create RDS next) — click **Next**
- **Secret name:** `devops/project3/rds-password`
- **Description:** `RDS password for project 3 app server`
- Click **Next → Next → Store**

### Step 3.3 — Copy the Secret ARN
- Click on your new secret → copy the **Secret ARN** at the top
- It looks like: `arn:aws:secretsmanager:ap-south-1:123456789:secret:devops/project3/rds-password-AbCdEf`
- **Save this** — you'll need it in the Launch Template

✅ **Checkpoint:** Secret stored. ARN copied. No password in any code file.

---

## Phase 4 — Create Security Groups

> You need 2 new security groups: one for the Load Balancer (accepts internet traffic) and one for the EC2 app servers (only accepts traffic from the Load Balancer).

### Step 4.1 — Security Group for Load Balancer

- **VPC → Security Groups → Create security group**
- **Name:** `alb-sg`
- **Description:** `Allow HTTP from internet`
- **VPC:** `devops-project2-vpc`
- **Inbound rules → Add rule:**
  - Type: `HTTP` | Port: `80` | Source: `Anywhere (0.0.0.0/0)`
- **Outbound:** leave default
- Click **Create security group**

### Step 4.2 — Security Group for App Servers (EC2)

- Create security group
- **Name:** `app-server-sg`
- **Description:** `Allow HTTP from ALB only`
- **VPC:** `devops-project2-vpc`
- **Inbound rules → Add rule:**
  - Type: `HTTP` | Port: `80` | Source: `Custom` → paste **Security Group ID of alb-sg**

> ℹ️ This means only the Load Balancer can send traffic to your EC2s. The internet cannot reach them directly.

- **Add another rule:**
  - Type: `SSH` | Port: `22` | Source: `Custom` → paste **Security Group ID of bastion-sg** (from Project 2)
- **Outbound:** leave default (EC2s need outbound to reach RDS and internet for updates)
- Click **Create security group**

### Step 4.3 — Update RDS Security Group

- Go back to `rds-sg` → click it → **Inbound rules → Edit inbound rules**
- For the MySQL rule (port 3306), set Source: `Custom` → paste **Security Group ID of app-server-sg**
- **Save rules**

✅ **Checkpoint:** 3 security groups configured. Traffic flows: Internet → ALB → EC2 → RDS. Nothing bypasses this chain.

---

## Phase 5 — Create Launch Template

### Step 5.1 — Go to EC2 → Launch Templates
- EC2 → left sidebar → **Launch Templates → Create launch template**

### Step 5.2 — Basic Settings
- **Launch template name:** `devops-project3-lt`
- **Description:** `App server template for ASG`
- Check: **Provide guidance to help me set up a template that I can use with EC2 Auto Scaling**

### Step 5.3 — AMI
- Click **Browse more AMIs**
- Search: `Ubuntu`
- Select: **Ubuntu Server 22.04 LTS (HVM), SSD Volume Type**
- **Architecture:** 64-bit (x86)

### Step 5.4 — Instance Type
- **Instance type:** `t2.micro`

### Step 5.5 — Key Pair
- **Key pair name:** `devops-project2` (reuse from Project 2)

### Step 5.6 — Network Settings
- **Subnet:** Do NOT specify here — ASG will choose subnets
- **Security groups:** select `app-server-sg`

### Step 5.7 — IAM Instance Profile

> Your EC2 needs permission to read from Secrets Manager. Create an IAM role first.

- Open a new browser tab: **IAM → Roles → Create role**
  - **Trusted entity type:** AWS service
  - **Use case:** EC2
  - Click **Next**
  - Search and attach policy: `SecretsManagerReadWrite`
  - **Role name:** `ec2-secrets-manager-role`
  - Click **Create role**
- Back in Launch Template tab → **Advanced details → IAM instance profile** → select `ec2-secrets-manager-role`

### Step 5.8 — User Data (Startup Script)

- Scroll to bottom of Launch Template → **Advanced details → User data**
- Paste the following script **exactly:**

```bash
#!/bin/bash
apt-get update -y
apt-get install -y apache2 mysql-client awscli

systemctl start apache2
systemctl enable apache2

# Get IMDSv2 token
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" -s)

# Get instance metadata
INSTANCE_ID=$(curl -s \
  -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/instance-id)

AZ=$(curl -s \
  -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/placement/availability-zone)

# Fetch DB secret from Secrets Manager
SECRET=$(aws secretsmanager get-secret-value \
  --secret-id devops/project3/rds-password \
  --region ap-south-1 \
  --query SecretString \
  --output text)

DB_USER=$(echo $SECRET | python3 -c "import sys,json; print(json.load(sys.stdin)['username'])")

# Create webpage
cat > /var/www/html/index.html << EOF
<html>
<head><title>DevOps Project 3</title></head>

<body style='font-family:Arial; padding:40px; background:#f0f4f8'>

<h1 style='color:#1E3A5F'>Project 3 - Auto Scaling App</h1>

<p><b>Instance ID:</b> $INSTANCE_ID</p>

<p><b>Availability Zone:</b> $AZ</p>

<p><b>DB User from Secrets Manager:</b> $DB_USER</p>

<p style='color:green'><b>Status:</b> Running via Auto Scaling Group</p>

</body>
</html>
EOF
```

- Click **Create launch template**

✅ **Checkpoint:** Launch template created with User Data script and IAM role.

---

## Phase 6 — Create Target Group

> A Target Group is a pool of EC2 instances the Load Balancer sends traffic to. It also runs health checks — if an EC2 stops responding, the ALB automatically stops sending it traffic.

### Step 6.1 — Go to Target Groups
- EC2 → left sidebar → **Target Groups → Create target group**

### Step 6.2 — Configuration
- **Target type:** Instances
- **Target group name:** `devops-project3-tg`
- **Protocol:** HTTP
- **Port:** 80
- **VPC:** `devops-project2-vpc`
- **Protocol version:** HTTP1

**Health check settings:**
- **Health check protocol:** HTTP
- **Health check path:** `/`
- **Healthy threshold:** 2 (EC2 must pass 2 checks in a row to be considered healthy)
- **Unhealthy threshold:** 3 (EC2 must fail 3 checks in a row to be removed)
- **Timeout:** 5 seconds
- **Interval:** 30 seconds
- **Success codes:** 200
- Click **Next** → do NOT register any targets now (ASG will do this automatically)
- Click **Create target group**

✅ **Checkpoint:** Target group created. ALB will auto-register EC2s as ASG launches them.

---

## Phase 7 — Create Application Load Balancer

### Step 7.1 — Go to Load Balancers
- EC2 → left sidebar → **Load Balancers → Create load balancer**

### Step 7.2 — Choose ALB
- Click **Create** under **Application Load Balancer**

### Step 7.3 — Basic Configuration
- **Load balancer name:** `devops-project3-alb`
- **Scheme:** Internet-facing (it needs to accept traffic from the internet)
- **IP address type:** IPv4

### Step 7.4 — Network Mapping
- **VPC:** `devops-project2-vpc`
- **Mappings** — select BOTH availability zones:
  - `ap-south-1a` → `public-subnet-1a`
  - `ap-south-1b` → `public-subnet-1b`

> ℹ️ The ALB must span public subnets in at least 2 AZs. This is what makes it highly available.

### Step 7.5 — Security Groups
- Remove the default security group
- Add: `alb-sg`

### Step 7.6 — Listeners and Routing
- **Listener:** HTTP : 80
- **Default action:** Forward to → `devops-project3-tg`
- Click **Create load balancer**

### Step 7.7 — Copy ALB DNS Name
- After creation, click your ALB → copy the **DNS name**
- It looks like: `devops-project3-alb-1234567890.ap-south-1.elb.amazonaws.com`
- **Save this** — you will use this to test your app

> ⚠️ The ALB will show 502/503 errors until your Auto Scaling Group launches EC2 instances. This is expected.

✅ **Checkpoint:** ALB created. DNS name copied. No EC2s registered yet — that comes next.

---

## Phase 8 — Create Auto Scaling Group

> The ASG is the core of the architecture. It maintains a minimum number of EC2s, replaces unhealthy ones, and scales out/in based on demand.

### Step 8.1 — Go to Auto Scaling Groups
- EC2 → left sidebar → **Auto Scaling Groups → Create Auto Scaling group**

### Step 8.2 — Choose Launch Template
- **Auto Scaling group name:** `devops-project3-asg`
- **Launch template:** `devops-project3-lt`
- **Version:** Latest (1)
- Click **Next**

### Step 8.3 — Network
- **VPC:** `devops-project2-vpc`
- **Availability Zones and subnets:** select `private-subnet-1a` and `private-subnet-1b`

> ℹ️ EC2s launch in PRIVATE subnets. The ALB (in public subnets) forwards traffic to them. This is the correct production pattern.

- Click **Next**

### Step 8.4 — Load Balancing
- **Attach to an existing load balancer**
- **Choose from your load balancer target groups**
- Select: `devops-project3-tg`
- **Health checks:** turn on ELB health checks
- **Health check grace period:** 120 seconds (gives EC2 time to finish booting)
- Click **Next**

### Step 8.5 — Group Size and Scaling
- **Desired capacity:** 2
- **Minimum capacity:** 1
- **Maximum capacity:** 4

**Automatic scaling:**
- Select: **Target tracking scaling policy**
- **Scaling policy name:** `cpu-target-tracking`
- **Metric type:** Average CPU Utilization
- **Target value:** 70
- **Instance warmup:** 120 seconds

> ℹ️ This means: if average CPU across all EC2s exceeds 70%, ASG automatically adds more. If CPU drops below ~30%, it removes instances.

- Click **Next → Next → Create Auto Scaling group**

### Step 8.6 — Wait for Instances to Launch
- Go to **EC2 → Instances** — you should see 2 new instances launching
- Wait until both show status: **Running** and **2/2 checks passed** (~3–5 minutes)
- If instances launch but fail health checks, check the user-data script and IAM role

✅ **Checkpoint:** ASG running with 2 instances in private subnets. ALB health checks passing.

---

## Bastion Server Setup

> Without a Bastion server you won't be able to reach the database from your local machine for debugging.

Create a new Bastion server with the following settings:
- **VPC:** `devops-project2-vpc`
- **Subnet:** any **public subnet**
- **Key pair:** `devops-project2` (Project 2 key pair)
- **Security groups:** `bastion-sg` AND `app-server-sg`

This allows the Bastion to SSH into private EC2s and also reach RDS through the app-server security group.

---

## Testing

1. Open the ALB DNS name in your browser
2. You should see the Project 3 web page showing:
   - Instance ID
   - Availability Zone
   - DB User fetched from Secrets Manager
   - Status: Running via Auto Scaling Group
3. Refresh a few times — you may see different Instance IDs as the ALB routes to different EC2s

---

## Cleanup (to avoid AWS charges)

Delete resources in this order to avoid dependency errors:

1. Auto Scaling Group (`devops-project3-asg`)
2. Load Balancer (`devops-project3-alb`)
3. Target Group (`devops-project3-tg`)
4. Launch Template (`devops-project3-lt`)
5. RDS Database (`devops-project3-db`)
6. RDS Subnet Group (`devops-project3-rds-subnet-group`)
7. Secret (`devops/project3/rds-password`)
8. IAM Role (`ec2-secrets-manager-role`)
9. Security Groups: `rds-sg`, `app-server-sg`, `alb-sg`
10. Bastion server (EC2 instance)
