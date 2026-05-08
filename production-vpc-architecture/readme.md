# Project 2 — Custom VPC with Public + Private Subnets
## Bastion Host + Private App Server + NAT Gateway + IGW

**Live proof:** SSH into private EC2 via bastion, curl google.com from private subnet  
**Stack:** AWS VPC, Subnets, IGW, NAT Gateway, Route Tables, Security Groups, EC2  
**Region:** ap-south-1 (Mumbai)  
**Cost:** ~$0 (excluding NAT Gateway — delete after practice)

---

## Architecture

<div align="center">
  <img src="Screenshot 2026-05-07 184653.png" >
</div>
---

## Service Deep Dives

### VPC (Virtual Private Cloud)
Your own isolated network inside AWS. Every resource you create in AWS lives inside a VPC. The default VPC that AWS gives every account is convenient but bad practice for real infrastructure — it's pre-configured in a way that makes security mistakes easy. A custom VPC forces you to make every network decision intentionally.

The CIDR block `10.0.0.0/16` is a private IP range. The `/16` means the first 16 bits are fixed (10.0), giving you 65,536 IP addresses to assign to subnets.

### Subnets
A subnet is a slice of your VPC's IP range, locked to one Availability Zone. You can't stretch a subnet across AZs.

Public subnets have a route to the Internet Gateway. Private subnets do not. That's the only difference — it's entirely controlled by the route table, not anything magical about the subnet itself.

We created 2 subnets in each tier (public and private) across 2 AZs. This is production practice — if one AZ has an outage, your other AZ keeps running.

### Internet Gateway (IGW)
The door between your VPC and the internet. One IGW per VPC. It's not a server — it's a logical component. Attaching it to the VPC is not enough; you also need a route table entry pointing `0.0.0.0/0` to it.

Without IGW: nothing in your VPC can reach the internet, even if an EC2 has a public IP assigned.

### NAT Gateway
Allows private subnet instances to initiate outbound connections (updates, API calls, curl) without being reachable inbound. It works by translating the private IP to its own Elastic IP when traffic leaves, and mapping the response back. The internet only sees the NAT Gateway's IP — never the private EC2's IP.

Must live in a public subnet because it needs internet access itself. This is why we placed it in public-subnet-1a.

**NAT Gateway vs NAT Instance:** AWS used to offer NAT Instances (EC2 you manage yourself). NAT Gateway is the managed replacement — no maintenance, higher bandwidth, auto-scales. Always use NAT Gateway in real projects.

### Route Tables
The routing rules for each subnet. Every subnet must be associated with exactly one route table.

Public route table has: `0.0.0.0/0 → IGW` (all internet traffic goes to IGW)
Private route table has: `0.0.0.0/0 → NAT Gateway` (outbound goes to NAT, which forwards to IGW)

The `local` route (`10.0.0.0/16 → local`) is auto-created in every route table and allows all instances within the VPC to talk to each other.

### Security Groups
Stateful firewalls at the instance level. Stateful means if you allow inbound SSH, the response traffic is automatically allowed outbound — you don't need a separate outbound rule for it.

Key design decision: app-sg allows SSH only from bastion-sg as the source — not from an IP address, but from another security group. This means any EC2 wearing bastion-sg can SSH into the app server. It's dynamic — if the bastion's IP changes, the rule still works.

### Bastion Host
A jump server — its only job is to be a secure SSH entry point into the private network. It has a public IP so you can reach it from your laptop. From there, you SSH again into private instances. In real companies, bastions are often replaced by AWS Systems Manager Session Manager (no SSH at all), but bastion is the foundational concept to understand first.

### SSH Jump Host Pattern
```
Your Laptop → (SSH) → Bastion (public IP) → (SSH) → App Server (private IP)
```
The app server never accepts traffic from the internet. The bastion is the only publicly accessible gateway, and it's locked down to your IP only.

---

## What I Proved

| Test | Command | Result | Proves |
|---|---|---|---|
| Bastion SSH | `ssh -i key.pem ec2-user@<public-ip>` | ✅ Connected | Bastion is reachable from internet |
| App server SSH jump | `ssh ec2-user@<private-ip>` from bastion | ✅ Connected | Jump host pattern works |
| Private server outbound | `curl https://checkip.amazonaws.com` from app server | ✅ NAT Gateway IP | NAT routes outbound traffic |
| Private server unreachable | `ssh ec2-user@<private-ip>` from laptop | ✅ Timeout | No public IP = unreachable |

---

## Key Things I Learned

- Public vs private subnet is controlled entirely by the route table, not the subnet itself
- NAT Gateway must live in a public subnet — it needs internet access to forward traffic
- Security group source can be another security group, not just an IP — this is the right way to control service-to-service access
- `0.0.0.0/0` in a route table means "all traffic not matched by a more specific route"
- The `local` route in every route table is implicit — all VPC-internal traffic routes automatically
- Deleting NAT Gateway before releasing Elastic IP causes an error — resource deletion order matters
- Private EC2 with no public IP is unreachable even if you set security group to `0.0.0.0/0` — security is layered

---

## IP Reference

| Resource | CIDR / IP |
|---|---|
| VPC | 10.0.0.0/16 |
| public-subnet-1a | 10.0.1.0/24 |
| public-subnet-1b | 10.0.2.0/24 |
| private-subnet-1a | 10.0.3.0/24 |
| private-subnet-1b | 10.0.4.0/24 |
| Bastion host | 10.0.1.x + public IP |
| App server | 10.0.3.x (private only) |

---

## Proof of Work

<div align="center">
  <img src="Screenshot 2026-05-08 134731.png" >
</div>
<div align="center">
  <img src="Screenshot 2026-05-08 134949.png" >
</div>
<div align="center">
  <img src="Screenshot 2026-05-08 135147.png" >
</div>
---

## Connect

- LinkedIn: [linkedin.com/in/ruhon-deb](https://www.linkedin.com/in/ruhon-deb)
- Email: ruhondeb28@email.com