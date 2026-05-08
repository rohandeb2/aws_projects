# Project 2 — Custom VPC with Public + Private Subnets
# Bastion Host + Private App Server + NAT Gateway
# Written for: Comfortable with networking, new to AWS VPC

=======================================================
WHAT YOU WILL BUILD
=======================================================

A production-grade VPC from scratch — zero default VPC used.

Architecture:
  - 1 Custom VPC (10.0.0.0/16)
  - 2 Public Subnets  (10.0.1.0/24 and 10.0.2.0/24) — AZ-a and AZ-b
  - 2 Private Subnets (10.0.3.0/24 and 10.0.4.0/24) — AZ-a and AZ-b
  - 1 Internet Gateway  — gives public subnets internet access
  - 1 NAT Gateway       — gives private subnets outbound internet access
  - 2 Route Tables      — one for public, one for private
  - 1 Bastion Host EC2  — in public subnet, your SSH entry point
  - 1 App Server EC2    — in private subnet, NOT reachable from internet
  - Security Groups     — strict inbound rules

Goal: Prove that:
  ✅ Public EC2 (bastion) is reachable via SSH from your laptop
  ✅ Private EC2 (app server) is ONLY reachable via bastion (SSH jump)
  ✅ Private EC2 CAN reach internet outbound (via NAT Gateway)
  ✅ Private EC2 CANNOT be reached directly from internet


  Built a production VPC architecture from scratch —
   public/private subnets, NAT Gateway, bastion host.
   Zero default VPC used. Private server can reach internet
   but internet cannot reach it

=======================================================
IMPORTANT — READ BEFORE STARTING
=======================================================

Cost warning:
  NAT Gateway costs ~$0.045/hour = ~$1.08/day = ~$32/month
  DELETE the NAT Gateway when you finish practicing.
  Everything else costs near zero.

Region: use ap-south-1 (Mumbai) for this project
  — closer to you, lower latency when SSH testing
  — us-east-1 was needed for ACM/CloudFront only

Key pair: you need an SSH key pair to access EC2 instances
  — you will create one in Phase 1

=======================================================
PHASE 1 — CREATE SSH KEY PAIR
=======================================================

STEP 1.1 — Go to EC2
  → Search bar → "EC2" → Click EC2
  → Confirm region: ap-south-1 (Mumbai) top right

STEP 1.2 — Create key pair
  → Left sidebar → "Key Pairs" (under Network & Security)
  → Click "Create key pair"
  → Name: devops-project2
  → Key pair type: RSA
  → Private key file format: .pem (for Linux/Mac) or .ppk (for PuTTY on Windows)
    ↳ Choose .pem — we will use it with SSH command
  → Click "Create key pair"
  → A file downloads automatically: devops-project2.pem
  → SAVE THIS FILE — you cannot download it again

STEP 1.3 — Set permissions on the key (Windows PowerShell or Git Bash)
  → Open terminal where the .pem file is saved
  → Run:
      chmod 400 devops-project2.pem
  → This prevents "permissions too open" SSH error

  ✅ Checkpoint: devops-project2.pem saved on your laptop

=======================================================
PHASE 2 — CREATE THE VPC
=======================================================

STEP 2.1 — Go to VPC
  → Search bar → "VPC" → Click VPC

STEP 2.2 — Create VPC (VPC only — not "VPC and more")
  → Click "Create VPC"
  → Select "VPC only" (not the wizard — we build manually)
  → Name tag: devops-project2-vpc
  → IPv4 CIDR block: 10.0.0.0/16
    ↳ This gives you 65,536 IP addresses to work with
    ↳ /16 = the first two octets (10.0) are fixed, last two are flexible
  → IPv6 CIDR block: No IPv6 CIDR block
  → Tenancy: Default
  → Click "Create VPC"

STEP 2.3 — Enable DNS hostnames
  → Click on your new VPC in the list
  → Click "Actions" → "Edit VPC settings"
  → Check "Enable DNS hostnames" → Save
    ↳ This allows EC2 instances to get public DNS names
    ↳ Required for SSH to work properly

  ✅ Checkpoint: VPC created with CIDR 10.0.0.0/16

=======================================================
PHASE 3 — CREATE SUBNETS (4 total)
=======================================================

You will create 4 subnets — 2 public, 2 private, across 2 AZs.

→ In VPC console → left sidebar → "Subnets"
→ Click "Create subnet"

---- SUBNET 1: Public Subnet AZ-a ----

STEP 3.1
  → VPC ID: select devops-project2-vpc
  → Subnet name: public-subnet-1a
  → Availability Zone: ap-south-1a
  → IPv4 CIDR block: 10.0.1.0/24
    ↳ /24 = first three octets fixed (10.0.1), 256 IPs available
  → Click "Add new subnet" (do not save yet, add all 4 at once)

---- SUBNET 2: Public Subnet AZ-b ----

STEP 3.2
  → Subnet name: public-subnet-1b
  → Availability Zone: ap-south-1b
  → IPv4 CIDR block: 10.0.2.0/24

---- SUBNET 3: Private Subnet AZ-a ----

STEP 3.3
  → Subnet name: private-subnet-1a
  → Availability Zone: ap-south-1a
  → IPv4 CIDR block: 10.0.3.0/24

---- SUBNET 4: Private Subnet AZ-b ----

STEP 3.4
  → Subnet name: private-subnet-1b
  → Availability Zone: ap-south-1b
  → IPv4 CIDR block: 10.0.4.0/24

→ Click "Create subnet" (creates all 4 at once)

STEP 3.5 — Enable auto-assign public IP on PUBLIC subnets only
  → Click on "public-subnet-1a"
  → Actions → "Edit subnet settings"
  → Check "Enable auto-assign public IPv4 address"
  → Save
  → Repeat for "public-subnet-1b"
  → Do NOT do this for private subnets

  ✅ Checkpoint: 4 subnets created. Public subnets auto-assign IPs.

=======================================================
PHASE 4 — CREATE INTERNET GATEWAY
=======================================================

An Internet Gateway (IGW) is what connects your VPC to the internet.
Without it, nothing in your VPC can reach the internet, even public subnets.

STEP 4.1 — Create IGW
  → Left sidebar → "Internet gateways"
  → Click "Create internet gateway"
  → Name tag: devops-project2-igw
  → Click "Create internet gateway"

STEP 4.2 — Attach IGW to your VPC
  → After creation, click "Actions" → "Attach to VPC"
  → Select devops-project2-vpc
  → Click "Attach internet gateway"

  ⚠️ An IGW created but NOT attached does nothing.
     State must say "Attached" not "Detached".

  ✅ Checkpoint: IGW created and attached to VPC.

=======================================================
PHASE 5 — CREATE NAT GATEWAY
=======================================================

A NAT Gateway allows private subnet instances to initiate
outbound internet connections (e.g. curl google.com, yum update)
WITHOUT being reachable from the internet inbound.

It must live in a PUBLIC subnet (it needs internet access itself).

STEP 5.1 — Allocate an Elastic IP first
  → Left sidebar → "Elastic IPs"
  → Click "Allocate Elastic IP address"
  → Network border group: ap-south-1 (default)
  → Click "Allocate"
  → Copy the Elastic IP address — you'll need it
    ↳ Note: Elastic IPs are free when attached to a running resource
      but cost ~$0.005/hour when unattached. Delete when done.

STEP 5.2 — Create NAT Gateway
  → Left sidebar → "NAT gateways"
  → Click "Create NAT gateway"
  → Name: devops-project2-nat
    choose availability mode= zonal
  → Subnet: public-subnet-1a (MUST be a public subnet)
  → Connectivity type: Public
  → Elastic IP allocation ID: select the EIP you just created
  → Click "Create NAT gateway"
  → Status will show "Pending" → wait for "Available" (~1-2 minutes)

  ⚠️ COST REMINDER: NAT Gateway = ~$1/day. Delete after practice.

  ✅ Checkpoint: NAT Gateway status = Available

=======================================================
PHASE 6 — CREATE ROUTE TABLES
=======================================================

Route tables control where traffic goes from each subnet.
You need 2 route tables:
  1. Public Route Table  — routes 0.0.0.0/0 to Internet Gateway
  2. Private Route Table — routes 0.0.0.0/0 to NAT Gateway

---- PUBLIC ROUTE TABLE ----

STEP 6.1 — Create public route table
  → Left sidebar → "Route tables"
  → Click "Create route table"
  → Name: public-rt
  → VPC: devops-project2-vpc
  → Click "Create route table"

STEP 6.2 — Add route to Internet Gateway
  → Click on public-rt
  → Click "Routes" tab → "Edit routes"
  → Click "Add route"
  → Destination: 0.0.0.0/0
    ↳ This means "all traffic going anywhere on the internet"
  → Target: Internet Gateway → select devops-project2-igw
  → Click "Save changes"

STEP 6.3 — Associate public subnets
  → Click "Subnet associations" tab → "Edit subnet associations"
  → Check both: public-subnet-1a and public-subnet-1b
  → Click "Save associations"

---- PRIVATE ROUTE TABLE ----

STEP 6.4 — Create private route table
  → Click "Create route table"
  → Name: private-rt
  → VPC: devops-project2-vpc
  → Click "Create route table"

STEP 6.5 — Add route to NAT Gateway
  → Click on private-rt
  → Click "Routes" tab → "Edit routes"
  → Click "Add route"
  → Destination: 0.0.0.0/0
  → Target: NAT Gateway → select devops-project2-nat
  → Click "Save changes"

STEP 6.6 — Associate private subnets
  → Click "Subnet associations" tab → "Edit subnet associations"
  → Check both: private-subnet-1a and private-subnet-1b
  → Click "Save associations"

  ✅ Checkpoint: 2 route tables created and associated with correct subnets.

=======================================================
PHASE 7 — CREATE SECURITY GROUPS
=======================================================

Security groups are virtual firewalls for EC2 instances.
You need 2 security groups:
  1. bastion-sg  — allows SSH from YOUR IP only
  2. app-sg      — allows SSH from bastion only (not from internet)

---- SECURITY GROUP 1: Bastion ----

STEP 7.1 — Find your public IP first
  → Open browser → go to: https://checkip.amazonaws.com
  → Note your IP address (e.g. 103.45.67.89)

STEP 7.2 — Create bastion security group
  → Left sidebar → "Security Groups"
  → Click "Create security group"
  → Security group name: bastion-sg
  → Description: Allow SSH from my IP only
  → VPC: devops-project2-vpc

  → Inbound rules → Add rule:
    - Type: SSH
    - Protocol: TCP (auto-filled)
    - Port: 22 (auto-filled)
    - Source: My IP (click the dropdown — AWS fills your IP automatically)
      ↳ This ensures ONLY your laptop can SSH to the bastion
      ↳ Never use 0.0.0.0/0 for SSH in production

  → Outbound rules: leave default (allow all outbound)
  → Click "Create security group"

---- SECURITY GROUP 2: App Server ----

STEP 7.3 — Create app security group
  → Click "Create security group"
  → Security group name: app-sg
  → Description: Allow SSH from bastion only
  → VPC: devops-project2-vpc

  → Inbound rules → Add rule:
    - Type: SSH
    - Protocol: TCP
    - Port: 22
    - Source: Custom → type the Security Group ID of bastion-sg
      ↳ Go to bastion-sg, copy its Security Group ID (sg-xxxxxxxxx)
      ↳ Paste it as the source
      ↳ This means: only traffic coming FROM the bastion EC2 is allowed
      ↳ Nothing from the internet can reach this instance directly

  → Outbound rules: leave default (allow all outbound)
  → Click "Create security group"

  ✅ Checkpoint: 2 security groups created with strict inbound rules.

=======================================================
PHASE 8 — LAUNCH EC2 INSTANCES
=======================================================

You will launch 2 EC2 instances:
  - Bastion host: public subnet, publicly accessible
  - App server: private subnet, only accessible via bastion

---- BASTION HOST ----

STEP 8.1 — Go to EC2 → Instances → Launch instances

STEP 8.2 — Configure bastion
  → Name: bastion-host
  → AMI: ubuntu
  → Instance type: t2.micro (free tier)
  → Key pair: devops-project2
  → Network settings → Edit:
    - VPC: devops-project2-vpc
    - Subnet: public-subnet-1a
    - Auto-assign public IP: Enable
    - Security group: Select existing → bastion-sg
  → Click "Launch instance"

STEP 8.3 — Copy bastion public IP
  → Go to Instances list
  → Click bastion-host
  → Copy the "Public IPv4 address" (e.g. 13.232.45.67)

---- APP SERVER ----

STEP 8.4 — Launch second instance

STEP 8.5 — Configure app server
  → Name: app-server
  → AMI: ubuntu
  → Instance type: t2.micro
  → Key pair: devops-project2
  → Network settings → Edit:
    - VPC: devops-project2-vpc
    - Subnet: private-subnet-1a
    - Auto-assign public IP: Disable
      ↳ Private servers should NEVER have a public IP
    - Security group: Select existing → app-sg
  → Click "Launch instance"

STEP 8.6 — Copy app server private IP
  → Click app-server in instances list
  → Copy the "Private IPv4 address" (e.g. 10.0.3.45)
  → Note: there is no public IP — this is correct

  ✅ Checkpoint: 2 instances running.
     Bastion has public IP. App server has private IP only.

=======================================================
PHASE 9 — SSH INTO BASTION HOST
=======================================================

STEP 9.1 — Open terminal on your laptop
  → Navigate to where devops-project2.pem is saved
  → Run:
      ssh -i "devops-project2.pem" ubuntu@<BASTION_PUBLIC_IP>.compute-1.amazonaws.com

  Replace <BASTION_PUBLIC_IP> with your actual bastion IP.
  Example: ssh -i devops-project2.pem ec2-user@13.232.45.67

STEP 9.2 — Accept the fingerprint
  → Type "yes" when asked "Are you sure you want to continue connecting?"

STEP 9.3 — Confirm you are on the bastion
  → You should see: [ec2-user@ip-10-0-1-xxx ~]$
  → Run: hostname
    → Shows the private IP of bastion (10.0.1.x)

  ✅ Checkpoint: You are inside the bastion host.

=======================================================
PHASE 10 — SSH FROM BASTION TO APP SERVER (SSH Jump)
=======================================================

The app server has no public IP. You can ONLY reach it from
the bastion host. This is the SSH jump pattern.

STEP 10.1 — Copy your .pem key to the bastion

  → Open a NEW terminal on your laptop (keep bastion SSH open) and on the other terminal should be your local machien running
  → Run:
      scp -i devops-project2.pem devops-project2.pem ubuntu@ec2-34-201-26-27.compute-1.amazonaws.com:~

  This copies your .pem file to the bastion's home directory.

STEP 10.2 — Back in bastion terminal, set permissions
  → chmod 400 ~/devops-project2.pem

STEP 10.3 — SSH from bastion to app server
  → Run from inside the bastion:
      ssh -i ~/devops-project2.pem ec2-user@<APP_SERVER_PRIVATE_IP>

  Replace <APP_SERVER_PRIVATE_IP> with the private IP (10.0.3.x)
  Example: ssh -i ~/devops-project2.pem ec2-user@10.0.3.45

STEP 10.4 — Confirm you are on the app server
  → You should see: [ec2-user@ip-10-0-3-xxx ~]$
  → Run: hostname
    → Shows the private IP of app server (10.0.3.x)

  ✅ Checkpoint: You are inside the app server via SSH jump.

=======================================================
PHASE 11 — PROVE THE ARCHITECTURE WORKS (4 Tests)
=======================================================

Run all 4 tests and note results. These become your LinkedIn proof.

---- TEST 1: Private server can reach internet (via NAT) ----

From INSIDE the app server, run:
  curl https://checkip.amazonaws.com

Expected result: Shows an IP address (the NAT Gateway's EIP)
This proves: Private EC2 → NAT Gateway → Internet Gateway → Internet

---- TEST 2: Private server cannot be reached from internet ----

From YOUR LAPTOP (not bastion), try:
  ssh -i devops-project2.pem ec2-user@<APP_SERVER_PRIVATE_IP>

Expected result: Connection times out (hangs forever)
This proves: App server is not directly reachable — no public IP,
app-sg only allows SSH from bastion-sg source

Press Ctrl+C to cancel after 10 seconds.

---- TEST 3: Confirm private server has no public IP ----

From inside app server, run:
  curl http://169.254.169.254/latest/meta-data/public-ipv4

Expected result: 404 error or empty response
This proves: Instance has no public IP assigned

---- TEST 4: DNS resolution works from private subnet ----

From inside app server, run:
  curl https://google.com

Expected result: HTML response from Google
This proves: NAT Gateway is routing outbound traffic correctly
and DNS resolution works inside the private subnet

  ✅ All 4 tests passing = architecture is complete and correct.

=======================================================
PHASE 12 — CLEANUP (IMPORTANT — AVOID CHARGES)
=======================================================

Delete in this exact order (dependencies matter):

1. Terminate both EC2 instances
   → EC2 → Instances → select both → Instance state → Terminate

2. Delete NAT Gateway
   → VPC → NAT gateways → select → Actions → Delete
   → Wait for state: Deleted (~1 minute)

3. Release Elastic IP
   → VPC → Elastic IPs → select → Actions → Release
   ↳ Must delete NAT Gateway FIRST before releasing EIP

4. Detach and Delete Internet Gateway
   → VPC → Internet gateways → Actions → Detach from VPC
   → Then Actions → Delete internet gateway

5. Delete Subnets (all 4)
   → VPC → Subnets → select all 4 → Actions → Delete

6. Delete Route Tables (public-rt and private-rt)
   → VPC → Route tables → select both custom ones → Actions → Delete
   ↳ Do NOT delete the main/default route table — AWS won't let you

7. Delete Security Groups (bastion-sg and app-sg)
   → EC2 → Security Groups → select both → Actions → Delete

8. Delete VPC
   → VPC → Your VPCs → select devops-project2-vpc → Actions → Delete

  ✅ All resources deleted. Zero ongoing charges.

