# Project 2 — Custom VPC with Public + Private Subnets
### Bastion Host · Private App Server · NAT Gateway

---

## What You Will Build

A production-grade VPC from scratch — zero default VPC used.

| Component | Detail |
|---|---|
| VPC | `10.0.0.0/16` |
| Public Subnets | `10.0.1.0/24` (AZ-a), `10.0.2.0/24` (AZ-b) |
| Private Subnets | `10.0.3.0/24` (AZ-a), `10.0.4.0/24` (AZ-b) |
| Internet Gateway | Gives public subnets internet access |
| NAT Gateway | Gives private subnets outbound internet access |
| Route Tables | One for public, one for private |
| Bastion Host EC2 | In public subnet — your SSH entry point |
| App Server EC2 | In private subnet — NOT reachable from internet |
| Security Groups | Strict inbound rules |

**Goals — prove that:**
- ✅ Public EC2 (bastion) is reachable via SSH from your laptop
- ✅ Private EC2 (app server) is ONLY reachable via bastion (SSH jump)
- ✅ Private EC2 CAN reach internet outbound (via NAT Gateway)
- ✅ Private EC2 CANNOT be reached directly from internet

> **Resume line:** Built a production VPC architecture from scratch — public/private subnets, NAT Gateway, bastion host. Zero default VPC used. Private server can reach internet but internet cannot reach it.

---

## ⚠️ Read Before Starting

**Cost warning:**
NAT Gateway costs ~$0.045/hour = ~$1.08/day = ~$32/month.
**DELETE the NAT Gateway when you finish practicing.**
Everything else costs near zero.

**Region:** Use `ap-south-1` (Mumbai) for this project — closer to you, lower latency when SSH testing. (`us-east-1` was only needed for ACM/CloudFront.)

---

## Phase 1 — Create SSH Key Pair

**Step 1.1 — Go to EC2**
- Search bar → **EC2** → Click EC2
- Confirm region: `ap-south-1` (Mumbai) — top right

**Step 1.2 — Create key pair**
- Left sidebar → **Key Pairs** (under Network & Security)
- Click **Create key pair**
- Name: `devops-project2`
- Key pair type: `RSA`
- Private key file format: `.pem` (for Linux/Mac) or `.ppk` (for PuTTY on Windows) — choose `.pem`
- Click **Create key pair**
- A file downloads automatically: `devops-project2.pem`
- **SAVE THIS FILE — you cannot download it again**

**Step 1.3 — Set permissions on the key**
```bash
chmod 400 devops-project2.pem
```
> Prevents the "permissions too open" SSH error.

✅ **Checkpoint:** `devops-project2.pem` saved on your laptop

---

## Phase 2 — Create the VPC

**Step 2.1 — Go to VPC**
- Search bar → **VPC** → Click VPC

**Step 2.2 — Create VPC (VPC only — not "VPC and more")**
- Click **Create VPC**
- Select **VPC only** (not the wizard — we build manually)
- Name tag: `devops-project2-vpc`
- IPv4 CIDR block: `10.0.0.0/16`
  - `/16` = first two octets (`10.0`) are fixed, last two are flexible — 65,536 IPs
- IPv6 CIDR block: No IPv6
- Tenancy: Default
- Click **Create VPC**

**Step 2.3 — Enable DNS hostnames**
- Click on your new VPC → **Actions** → **Edit VPC settings**
- Check **Enable DNS hostnames** → Save
  - Allows EC2 instances to get public DNS names; required for SSH to work properly

✅ **Checkpoint:** VPC created with CIDR `10.0.0.0/16`

---

## Phase 3 — Create Subnets (4 total)

Go to **VPC console** → left sidebar → **Subnets** → **Create subnet**

**Step 3.1 — Public Subnet AZ-a**
- VPC ID: `devops-project2-vpc`
- Subnet name: `public-subnet-1a`
- Availability Zone: `ap-south-1a`
- IPv4 CIDR block: `10.0.1.0/24`
- Click **Add new subnet** (don't save yet — add all 4 at once)

**Step 3.2 — Public Subnet AZ-b**
- Subnet name: `public-subnet-1b`
- Availability Zone: `ap-south-1b`
- IPv4 CIDR block: `10.0.2.0/24`

**Step 3.3 — Private Subnet AZ-a**
- Subnet name: `private-subnet-1a`
- Availability Zone: `ap-south-1a`
- IPv4 CIDR block: `10.0.3.0/24`

**Step 3.4 — Private Subnet AZ-b**
- Subnet name: `private-subnet-1b`
- Availability Zone: `ap-south-1b`
- IPv4 CIDR block: `10.0.4.0/24`

→ Click **Create subnet** (creates all 4 at once)

**Step 3.5 — Enable auto-assign public IP on PUBLIC subnets only**
- Click `public-subnet-1a` → **Actions** → **Edit subnet settings**
- Check **Enable auto-assign public IPv4 address** → Save
- Repeat for `public-subnet-1b`
- **Do NOT do this for private subnets**

✅ **Checkpoint:** 4 subnets created. Public subnets auto-assign IPs.

---

## Phase 4 — Create Internet Gateway

An Internet Gateway (IGW) connects your VPC to the internet. Without it, nothing in your VPC can reach the internet — even public subnets.

**Step 4.1 — Create IGW**
- Left sidebar → **Internet gateways** → **Create internet gateway**
- Name tag: `devops-project2-igw`
- Click **Create internet gateway**

**Step 4.2 — Attach IGW to your VPC**
- After creation → **Actions** → **Attach to VPC**
- Select `devops-project2-vpc`
- Click **Attach internet gateway**

> ⚠️ An IGW created but NOT attached does nothing. State must say **Attached**, not **Detached**.

✅ **Checkpoint:** IGW created and attached to VPC

---

## Phase 5 — Create NAT Gateway

A NAT Gateway allows private subnet instances to initiate outbound internet connections (e.g. `curl google.com`, `yum update`) without being reachable from the internet inbound. It must live in a **public subnet** — it needs internet access itself.

**Step 5.1 — Allocate an Elastic IP first**
- Left sidebar → **Elastic IPs** → **Allocate Elastic IP address**
- Network border group: `ap-south-1` (default)
- Click **Allocate**
- Copy the Elastic IP address — you'll need it
  - Elastic IPs are free when attached to a running resource, but cost ~$0.005/hour when unattached. Delete when done.

**Step 5.2 — Create NAT Gateway**
- Left sidebar → **NAT gateways** → **Create NAT gateway**
- Name: `devops-project2-nat`
- Availability mode: **Zonal**
- Subnet: `public-subnet-1a` (**MUST** be a public subnet)
- Connectivity type: Public
- Elastic IP allocation ID: select the EIP you just created
- Click **Create NAT gateway**
- Status will show **Pending** → wait for **Available** (~1–2 minutes)

> ⚠️ **COST REMINDER:** NAT Gateway = ~$1/day. Delete after practice.

✅ **Checkpoint:** NAT Gateway status = Available

---

## Phase 6 — Create Route Tables

Route tables control where traffic goes from each subnet. You need 2:
- **Public Route Table** — routes `0.0.0.0/0` to Internet Gateway
- **Private Route Table** — routes `0.0.0.0/0` to NAT Gateway

### Public Route Table

**Step 6.1 — Create public route table**
- Left sidebar → **Route tables** → **Create route table**
- Name: `public-rt`
- VPC: `devops-project2-vpc`
- Click **Create route table**

**Step 6.2 — Add route to Internet Gateway**
- Click `public-rt` → **Routes** tab → **Edit routes** → **Add route**
- Destination: `0.0.0.0/0` (all internet traffic)
- Target: Internet Gateway → select `devops-project2-igw`
- Click **Save changes**

**Step 6.3 — Associate public subnets**
- **Subnet associations** tab → **Edit subnet associations**
- Check both: `public-subnet-1a` and `public-subnet-1b`
- Click **Save associations**

### Private Route Table

**Step 6.4 — Create private route table**
- Click **Create route table**
- Name: `private-rt`
- VPC: `devops-project2-vpc`
- Click **Create route table**

**Step 6.5 — Add route to NAT Gateway**
- Click `private-rt` → **Routes** tab → **Edit routes** → **Add route**
- Destination: `0.0.0.0/0`
- Target: NAT Gateway → select `devops-project2-nat`
- Click **Save changes**

**Step 6.6 — Associate private subnets**
- **Subnet associations** tab → **Edit subnet associations**
- Check both: `private-subnet-1a` and `private-subnet-1b`
- Click **Save associations**

✅ **Checkpoint:** 2 route tables created and associated with correct subnets

---

## Phase 7 — Create Security Groups

Security groups are virtual firewalls for EC2 instances. You need 2:
- `bastion-sg` — allows SSH from YOUR IP only
- `app-sg` — allows SSH from bastion only (not from internet)

### Security Group 1: Bastion

**Step 7.1 — Find your public IP first**
- Open browser → go to: [https://checkip.amazonaws.com](https://checkip.amazonaws.com)
- Note your IP address (e.g. `103.45.67.89`)

**Step 7.2 — Create bastion security group**
- Left sidebar → **Security Groups** → **Create security group**
- Security group name: `bastion-sg`
- Description: `Allow SSH from my IP only`
- VPC: `devops-project2-vpc`
- Inbound rules → **Add rule:**
  - Type: SSH
  - Protocol: TCP (auto-filled)
  - Port: 22 (auto-filled)
  - Source: **My IP** (AWS fills your IP automatically)
    - Never use `0.0.0.0/0` for SSH in production
- Outbound rules: leave default (allow all outbound)
- Click **Create security group**

### Security Group 2: App Server

**Step 7.3 — Create app security group**
- Click **Create security group**
- Security group name: `app-sg`
- Description: `Allow SSH from bastion only`
- VPC: `devops-project2-vpc`
- Inbound rules → **Add rule:**
  - Type: SSH
  - Protocol: TCP
  - Port: 22
  - Source: Custom → paste the **Security Group ID** of `bastion-sg` (e.g. `sg-xxxxxxxxx`)
    - Only traffic coming FROM the bastion EC2 is allowed; nothing from the internet can reach this instance directly
- Outbound rules: leave default (allow all outbound)
- Click **Create security group**

✅ **Checkpoint:** 2 security groups created with strict inbound rules

---

## Phase 8 — Launch EC2 Instances

### Bastion Host

**Step 8.1 — Go to EC2 → Instances → Launch instances**

**Step 8.2 — Configure bastion**
- Name: `bastion-host`
- AMI: Ubuntu
- Instance type: `t2.micro` (free tier)
- Key pair: `devops-project2`
- Network settings → **Edit:**
  - VPC: `devops-project2-vpc`
  - Subnet: `public-subnet-1a`
  - Auto-assign public IP: **Enable**
  - Security group: Select existing → `bastion-sg`
- Click **Launch instance**

**Step 8.3 — Copy bastion public IP**
- Go to Instances list → Click `bastion-host`
- Copy the **Public IPv4 address** (e.g. `13.232.45.67`)

### App Server

**Step 8.4 — Launch second instance**

**Step 8.5 — Configure app server**
- Name: `app-server`
- AMI: Ubuntu
- Instance type: `t2.micro`
- Key pair: `devops-project2`
- Network settings → **Edit:**
  - VPC: `devops-project2-vpc`
  - Subnet: `private-subnet-1a`
  - Auto-assign public IP: **Disable** — private servers should never have a public IP
  - Security group: Select existing → `app-sg`
- Click **Launch instance**

**Step 8.6 — Copy app server private IP**
- Click `app-server` in instances list
- Copy the **Private IPv4 address** (e.g. `10.0.3.45`)
- Note: there is no public IP — this is correct

✅ **Checkpoint:** 2 instances running. Bastion has public IP. App server has private IP only.

---

## Phase 9 — SSH into Bastion Host

**Step 9.1 — Open terminal on your laptop**

Navigate to where `devops-project2.pem` is saved, then run:
```bash
ssh -i devops-project2.pem ubuntu@<BASTION_PUBLIC_IP>
# Example: ssh -i devops-project2.pem ubuntu@13.232.45.67
```

**Step 9.2 — Accept the fingerprint**
- Type `yes` when asked: *"Are you sure you want to continue connecting?"*

**Step 9.3 — Confirm you are on the bastion**
```bash
hostname
# Output: ip-10-0-1-xxx (private IP of bastion)
```

✅ **Checkpoint:** You are inside the bastion host

---

## Phase 10 — SSH from Bastion to App Server (SSH Jump)

The app server has no public IP. You can ONLY reach it from the bastion. This is the SSH jump pattern.

**Step 10.1 — Copy your .pem key to the bastion**

Open a **new terminal on your laptop** (keep bastion SSH open) and run:
```bash
scp -i devops-project2.pem devops-project2.pem ubuntu@<BASTION_PUBLIC_IP>:~
```

**Step 10.2 — Back in bastion terminal, set permissions**
```bash
chmod 400 ~/devops-project2.pem
```

**Step 10.3 — SSH from bastion to app server**
```bash
ssh -i ~/devops-project2.pem ubuntu@<APP_SERVER_PRIVATE_IP>
# Example: ssh -i ~/devops-project2.pem ubuntu@10.0.3.45
```

**Step 10.4 — Confirm you are on the app server**
```bash
hostname
# Output: ip-10-0-3-xxx (private IP of app server)
```

✅ **Checkpoint:** You are inside the app server via SSH jump

---

## Phase 11 — Prove the Architecture Works (4 Tests)

Run all 4 tests and note the results.

### Test 1 — Private server can reach internet (via NAT)

From **inside the app server**, run:
```bash
curl https://checkip.amazonaws.com
```
**Expected:** Shows an IP address (the NAT Gateway's EIP)
**Proves:** Private EC2 → NAT Gateway → Internet Gateway → Internet

### Test 2 — Private server cannot be reached from internet

From **your laptop** (not bastion), run:
```bash
ssh -i devops-project2.pem ubuntu@<APP_SERVER_PRIVATE_IP>
```
**Expected:** Connection times out (hangs forever)
**Proves:** App server is not directly reachable — no public IP, `app-sg` only allows SSH from `bastion-sg` source

Press `Ctrl+C` to cancel after 10 seconds.

### Test 3 — Confirm private server has no public IP

From **inside app server**, run:
```bash
curl http://169.254.169.254/latest/meta-data/public-ipv4
```
**Expected:** 404 error or empty response
**Proves:** Instance has no public IP assigned

### Test 4 — DNS resolution works from private subnet

From **inside app server**, run:
```bash
curl https://google.com
```
**Expected:** HTML response from Google
**Proves:** NAT Gateway is routing outbound traffic correctly and DNS resolution works inside the private subnet

✅ **All 4 tests passing = architecture is complete and correct**

---

## Phase 12 — Cleanup (Important — Avoid Charges)

Delete in this **exact order** — dependencies matter:

| Step | Action |
|---|---|
| 1 | **Terminate both EC2 instances** — EC2 → Instances → select both → Instance state → Terminate |
| 2 | **Delete NAT Gateway** — VPC → NAT gateways → Actions → Delete → wait for state: Deleted (~1 min) |
| 3 | **Release Elastic IP** — VPC → Elastic IPs → Actions → Release *(must delete NAT Gateway first)* |
| 4 | **Detach and Delete Internet Gateway** — Actions → Detach from VPC → then Delete internet gateway |
| 5 | **Delete all 4 Subnets** — VPC → Subnets → select all 4 → Actions → Delete |
| 6 | **Delete Route Tables** (`public-rt` and `private-rt`) — do NOT delete the main/default route table |
| 7 | **Delete Security Groups** (`bastion-sg` and `app-sg`) |
| 8 | **Delete VPC** — VPC → Your VPCs → select `devops-project2-vpc` → Actions → Delete |

✅ **All resources deleted. Zero ongoing charges.**
