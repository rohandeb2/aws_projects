# Project 1 — Static Website Hosting on AWS
## S3 + CloudFront + ACM + Route53 + GoDaddy

**Author:** Rohan | DevOps Engineer  
**Domain:** rohandevops.co.in  
**Stack:** AWS S3, CloudFront, ACM, Route53  
**Cost:** ~$0.50/month at low traffic  
**Difficulty:** Beginner → Intermediate

---

## Table of Contents

1. [What is this project?](#what-is-this-project)
2. [Architecture Overview](#architecture-overview)
3. [Why not just use a server?](#why-not-just-use-a-server)
4. [Service Deep Dives](#service-deep-dives)
   - [Amazon S3](#1-amazon-s3-simple-storage-service)
   - [Amazon CloudFront](#2-amazon-cloudfront)
   - [AWS ACM](#3-aws-acm-certificate-manager)
   - [Amazon Route53](#4-amazon-route53)
   - [Origin Access Control (OAC)](#5-origin-access-control-oac)
5. [How Everything Connects](#how-everything-connects)
6. [The Request Journey](#the-request-journey---what-happens-when-someone-visits-your-site)
7. [Key Decisions Made](#key-decisions-made-and-why)
8. [What Happens If You Skip Each Service](#what-happens-if-you-skip-each-service)
9. [Problems Faced and How They Were Solved](#problems-faced-and-how-they-were-solved)
10. [Cost Breakdown](#cost-breakdown)
11. [What I Learned](#what-i-learned)

---

## What is this project?

This project hosts a **static website** (HTML, CSS, JavaScript files) on AWS — completely without a traditional web server like Apache or Nginx. There is no EC2 instance, no server to maintain, no operating system to patch, and no risk of your server going down under traffic.

The website is a DevOps portfolio page served globally through AWS infrastructure, accessible at `https://rohandevops.co.in`.

**What is a static website?**  
A static website is made of fixed files — HTML, CSS, JavaScript — that are the same for every visitor. There is no backend server generating pages dynamically. The files sit in storage and get served directly to the browser. This is perfect for portfolio sites, landing pages, documentation, and blogs.

---

## Architecture Overview

```
                          ┌─────────────┐
                          │    User      │
                          │  (Browser)   │
                          └──────┬──────┘
                                 │ types rohandevops.co.in
                                 ▼
                          ┌─────────────┐
                          │   GoDaddy   │
                          │  (Domain    │
                          │ Registrar)  │
                          └──────┬──────┘
                                 │ nameservers point to Route53
                                 ▼
                          ┌─────────────┐
                          │   Route53   │
                          │    (DNS)    │
                          └──────┬──────┘
                                 │ A record → CloudFront
                                 ▼
                    ┌────────────────────────┐
                    │       CloudFront        │
                    │  (CDN + HTTPS + Cache)  │
                    │                         │
                    │  ┌───────────────────┐  │
                    │  │  ACM Certificate  │  │
                    │  │  (SSL/TLS/HTTPS)  │  │
                    │  └───────────────────┘  │
                    └────────────┬────────────┘
                                 │ OAC (private access)
                                 ▼
                    ┌────────────────────────┐
                    │        AWS S3           │
                    │  (Private File Storage) │
                    │                         │
                    │  index.html             │
                    │  error.html             │
                    │  style.css              │
                    └────────────────────────┘
```

**In plain English:**
When someone types `rohandevops.co.in` in their browser, the request travels through GoDaddy → Route53 → CloudFront → S3, and the website files come back through CloudFront → browser. The user never touches S3 directly. Everything goes through CloudFront.

---

## Why Not Just Use a Server?

Before understanding the services, it's important to understand **why** we chose this approach over a traditional setup.

**Traditional approach (what most people think of first):**
- Launch an EC2 instance (virtual server)
- Install Nginx or Apache
- Upload your HTML files
- Configure the web server
- Open port 80 and 443

**Problems with this approach for a static site:**
- You pay for the EC2 instance 24/7 even when no one is visiting (~$8-15/month minimum)
- If traffic spikes, your single server can slow down or crash
- You need to maintain the OS — security patches, updates, monitoring
- Files are served from one region only — slow for users far away
- You have to set up SSL certificates manually and renew them

**Our approach (S3 + CloudFront):**
- No server to manage — AWS handles everything
- Pay only for what you use — near zero cost at low traffic
- Files are cached at 400+ edge locations worldwide — fast for everyone
- Auto-scales to handle any amount of traffic
- SSL certificate is free and auto-renews

This pattern is called a **Serverless Static Hosting Architecture** and is used by thousands of production websites.

---

## Service Deep Dives

### 1. Amazon S3 (Simple Storage Service)

**What is S3?**  
S3 is AWS's object storage service. Think of it as a hard drive in the cloud, but instead of folders and files you have "buckets" and "objects". You can store any file — images, videos, HTML, CSS, JSON — and retrieve it via a URL.

**Key Concepts:**
- **Bucket** — a container for your files. Like a folder at the top level. Bucket names must be globally unique across all AWS accounts worldwide.
- **Object** — any file stored in a bucket. Each object has a key (its name/path) and the file data.
- **Region** — each bucket lives in one AWS region (e.g., us-east-1). Files are stored in that region's data centers.

**Why we used S3 in this project:**  
S3 is the most cost-effective and reliable way to store static files. It has 99.999999999% (11 nines) durability — meaning if you store 10 million files, you'd expect to lose one file every 10,000 years. Our HTML, CSS, and JavaScript files live in S3.

**How we configured S3:**  
We created a bucket named `rohandevops.co.in` in `us-east-1` and kept **all public access blocked**. This is a critical security decision explained in the OAC section below.

**What if we didn't use S3?**  
We would need a server (EC2) to store and serve files, which costs more, requires maintenance, and doesn't scale automatically.

**Common mistake beginners make with S3:**  
Many tutorials tell you to enable "Static website hosting" in S3 and make the bucket public. This works, but it exposes your bucket directly to the internet — anyone can download your files by guessing URLs, and you can't use a custom SSL certificate. We used the modern, secure approach instead: keep S3 private and serve everything through CloudFront.

---

### 2. Amazon CloudFront

**What is CloudFront?**  
CloudFront is AWS's Content Delivery Network (CDN). A CDN is a network of servers distributed globally that cache and serve your content from the location closest to the user.

**Why does this matter?**  
Imagine your S3 bucket is in `us-east-1` (Virginia, USA). A user in Mumbai visits your site. Without a CDN, their request travels all the way from Mumbai to Virginia and back — that's 14,000+ km round trip. With CloudFront, the files are cached at an edge location in Mumbai. The user gets the files from 50km away instead of 14,000km away. The page loads much faster.

CloudFront has **400+ edge locations** across the world. Once a user in any city visits your site, CloudFront caches the files there. The next visitor from that city gets the cached version instantly.

**What CloudFront does in this project:**
- Receives all incoming requests for `rohandevops.co.in`
- Checks if it has a cached copy of the requested file
- If yes → serves it immediately from the nearest edge location
- If no → fetches it from S3 (the "origin"), caches it, then serves it
- Handles HTTPS termination (the SSL certificate sits here)
- Redirects all HTTP traffic to HTTPS automatically
- Serves our custom error page when someone hits a bad URL

**What is Caching?**  
When CloudFront fetches a file from S3, it stores a copy at the edge location temporarily. For a certain time period (controlled by cache policies), it serves this copy to all visitors without going back to S3. This reduces load on S3 and makes the site faster.

**Cache Invalidation:**  
When you update a file in S3, CloudFront still serves the old cached version until the cache expires. To force CloudFront to fetch the new version immediately, you create an **invalidation** with path `/*`. This tells all edge locations worldwide to clear their cache. This is a real operational task DevOps engineers do after every frontend deployment.

**What if we didn't use CloudFront?**  
- No global caching — site loads slower for users far from us-east-1
- No HTTPS on a custom domain (S3 static hosting only supports HTTP for custom domains)
- No protection between users and S3 — S3 would need to be public
- No custom error pages
- Much higher S3 data transfer costs (CloudFront has cheaper egress pricing)

**The OAC + CloudFront relationship:**  
CloudFront is the only entity allowed to access our S3 bucket. It does this using Origin Access Control, explained next.

---

### 3. AWS ACM (Certificate Manager)

**What is ACM?**  
ACM is AWS's service for provisioning, managing, and auto-renewing SSL/TLS certificates. These certificates are what enable HTTPS on your website.

**What is HTTPS and why does it matter?**  
HTTP (HyperText Transfer Protocol) is the protocol browsers use to communicate with servers. The problem with plain HTTP is that all data travels in plain text — anyone between the user and the server (their ISP, someone on the same WiFi network) can read it.

HTTPS is HTTP with encryption. The "S" stands for Secure. All data is encrypted using TLS (Transport Layer Security). No one can read the traffic in transit.

**Why your browser shows a padlock:**  
When you visit a site with HTTPS, your browser verifies the SSL certificate to confirm:
1. The certificate was issued by a trusted Certificate Authority (CA)
2. The certificate belongs to the domain you're visiting
3. The certificate hasn't expired

If all three pass, you see the green padlock. If anything is wrong, the browser shows a warning like "Your connection is not private".

**Why we used ACM:**  
ACM provides free SSL certificates that auto-renew. Without ACM, you would need to buy a certificate (~$10-100/year from a provider like DigiCert), manually install it, and manually renew it every year before it expires. Forgetting to renew an SSL certificate is one of the most common causes of production outages — your site suddenly shows a security warning to all visitors.

**Critical rule about ACM + CloudFront:**  
CloudFront only accepts ACM certificates created in the `us-east-1` (N. Virginia) region. This is true even if your S3 bucket is in a different region. This is one of the most common mistakes beginners make — they create the certificate in Mumbai or another region and wonder why it doesn't show up in CloudFront's dropdown.

**DNS Validation:**  
When you request a certificate from ACM, it needs to verify that you actually own the domain. It does this by asking you to add a specific CNAME record to your DNS. Once ACM sees that record in your DNS, it knows you control the domain and issues the certificate. This is called DNS validation and it's the preferred method because it's automatic and allows auto-renewal.

**What if we didn't use ACM (or any SSL certificate)?**  
- Your site would be HTTP only — no padlock
- Chrome and Firefox would mark your site as "Not Secure"
- Users would see a warning and many would leave
- Google ranks HTTPS sites higher — no certificate hurts your SEO
- Any data submitted through forms would be readable in transit
- You would look unprofessional — no serious company runs HTTP-only in 2025

---

### 4. Amazon Route53

**What is Route53?**  
Route53 is AWS's Domain Name System (DNS) service. DNS is the internet's phone book — it translates human-readable domain names (like `rohandevops.co.in`) into IP addresses (like `13.32.45.67`) that computers use to communicate.

**Why is it called Route53?**  
DNS traditionally runs on port 53. Route53 is a play on that — "Route" as in routing traffic, "53" as in the DNS port.

**How DNS works (simplified):**  
When you type `rohandevops.co.in` in your browser:
1. Browser asks your local DNS resolver (usually your ISP or Google's 8.8.8.8): "What IP is rohandevops.co.in?"
2. The resolver checks who is authoritative for `.co.in` — this leads to the nameservers
3. Our nameservers are Route53's nameservers (ns-931.awsdns-52.net etc.)
4. Route53 looks up `rohandevops.co.in` in our hosted zone
5. Finds the A record → returns the IP address of CloudFront
6. Browser connects to that IP

**Hosted Zone:**  
A hosted zone in Route53 is a container for all DNS records for a domain. Think of it as a settings page where you define how traffic for your domain should be routed.

**Record Types we used:**
- **NS (Name Server)** — tells the world which DNS servers are authoritative for your domain. Route53 gives you 4 nameservers. You copy these to GoDaddy so GoDaddy says "for this domain, ask Route53".
- **SOA (Start of Authority)** — auto-created, contains administrative info about the zone.
- **A (Address)** — maps a domain name to an IP address. We used Alias A records that point to CloudFront instead of a raw IP.
- **CNAME** — maps one domain name to another domain name. We used this for ACM certificate validation.
- **AAAA** — same as A but for IPv6 addresses.

**Alias Records:**  
Normal A records point to a static IP address. But CloudFront doesn't have a static IP — it has a domain name (`d2u735qs6sjz7p.cloudfront.net`). AWS created Alias records specifically for this — they point to an AWS resource (like CloudFront) by its domain name, and Route53 resolves it to the right IP automatically. Alias records are also free to query, unlike CNAME records.

**Why we moved from GoDaddy DNS to Route53:**  
GoDaddy DNS works, but Route53 integrates natively with other AWS services. When you want to create an Alias record pointing to CloudFront, Route53 shows your CloudFront distributions in a dropdown. It's seamless. Route53 also has 100% uptime SLA, health checks, and latency-based routing for more advanced setups in the future.

**What if we didn't use Route53?**  
We could have used GoDaddy's DNS directly and pointed it to CloudFront using a CNAME record for `www` and an ANAME/ALIAS record for the root domain (GoDaddy supports this). It would work, but it's less integrated with AWS and slightly more manual to maintain. For learning and real-world AWS jobs, Route53 is the standard.

---

### 5. Origin Access Control (OAC)

**What is OAC?**  
Origin Access Control is a CloudFront feature that gives your CloudFront distribution a secure identity. S3 uses this identity to verify that requests are coming from your specific CloudFront distribution — and only from your CloudFront distribution.

**The problem it solves:**  
If your S3 bucket is public, anyone who knows or guesses your S3 URL can access your files directly, bypassing CloudFront entirely. They can download all your files, hot-link images, bypass any CloudFront security rules, and access things you didn't intend to expose.

**How OAC works:**  
1. You create an OAC and attach it to your CloudFront distribution
2. CloudFront uses this OAC to sign every request it sends to S3
3. You add a bucket policy to S3 that says: "Only accept requests from this specific CloudFront distribution"
4. Any other request to S3 — from a browser, from curl, from another CloudFront distribution — is rejected with a 403 Forbidden error

**The S3 bucket policy OAC generates:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontServicePrincipal",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudfront.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::rohandevops.co.in/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::ACCOUNT_ID:distribution/DISTRIBUTION_ID"
        }
      }
    }
  ]
}
```

This policy says: allow CloudFront (the service) to `GetObject` (read files) from this bucket, BUT ONLY when the request comes from this specific distribution ID. Any other request is blocked.

**OAC vs the old way (OAI):**  
The old method was called Origin Access Identity (OAI). OAC replaced it because OAC supports more S3 features (like SSE-KMS encryption), is more secure, and is the AWS-recommended approach as of 2022. If you see tutorials using OAI, they are outdated.

**What if we didn't use OAC?**  
Two scenarios:
1. **Bucket stays private without OAC** — CloudFront can't read files from S3, your site returns errors for everyone
2. **Bucket made public without OAC** — Site works, but anyone can access your S3 bucket directly using the S3 URL. Your security is bypassed. AWS will also flag this in Security Hub and Trusted Advisor as a critical finding.

OAC is what makes this architecture both **functional and secure** at the same time.

---

## How Everything Connects

Here is the exact chain of trust and configuration that makes the whole system work:

```
GoDaddy
  └── Nameservers set to Route53's 4 NS records
        └── Route53 Hosted Zone (rohandevops.co.in)
              ├── NS records (Route53 nameservers)
              ├── CNAME record (ACM validation — proves domain ownership)
              ├── A record root domain → CloudFront (Alias)
              └── A record www → CloudFront (Alias)
                    └── CloudFront Distribution
                          ├── Alternate domain: rohandevops.co.in, www.rohandevops.co.in
                          ├── SSL Certificate from ACM (us-east-1) ← MUST be us-east-1
                          ├── Viewer protocol: Redirect HTTP → HTTPS
                          ├── Default root object: index.html
                          ├── Custom error: 403 → /error.html (returns 404 to browser)
                          └── Origin: S3 bucket (private) via OAC
                                └── S3 Bucket (rohandevops.co.in)
                                      ├── Block all public access: ON
                                      ├── Bucket policy: allow only this CloudFront OAC
                                      ├── index.html
                                      ├── error.html
                                      └── style.css
```

Every arrow in this chain is a configured trust relationship. Remove any one of them and the site breaks in a specific, debuggable way.

---

## The Request Journey — What Happens When Someone Visits Your Site

Let's trace exactly what happens when someone in Bangalore types `https://rohandevops.co.in`:

**Step 1 — DNS Resolution**
The browser asks: "What IP address is rohandevops.co.in?"
GoDaddy says: "Ask Route53 — here are their nameservers."
Route53 looks up the A record for `rohandevops.co.in`.
Returns: the IP address of the nearest CloudFront edge location.

**Step 2 — TLS Handshake**
The browser connects to CloudFront and says "I want HTTPS."
CloudFront presents the ACM SSL certificate for `rohandevops.co.in`.
The browser verifies: Is it from a trusted CA? Is it for this domain? Is it not expired?
All pass → encrypted connection established. Padlock appears.

**Step 3 — CloudFront Cache Check**
The browser requests `index.html`.
CloudFront checks: "Do I have a cached copy of this file at this edge location?"
If yes → returns the cached file immediately. S3 is never contacted.
If no → proceeds to Step 4.

**Step 4 — Origin Fetch**
CloudFront sends a signed request to S3 (signed with the OAC identity).
S3 checks the bucket policy: "Is this request from the authorized CloudFront distribution?"
Yes → S3 returns `index.html`.
CloudFront caches the file at this edge location for future requests.
CloudFront returns the file to the browser.

**Step 5 — Browser Renders**
Browser receives `index.html`, sees a `<link>` to `style.css`.
Makes another request for `style.css` — same journey, served from cache.
Page renders.

**Total time for a cached request:** under 50ms from most locations.
**Total time for an uncached (first) request:** 200-400ms typically.

---

## Key Decisions Made and Why

**Decision 1: Keep S3 bucket private**
We kept S3 fully private and used OAC. We could have made it public and it would have worked, but it would be a security vulnerability. In a real job, making an S3 bucket public triggers security alerts and would require justification.

**Decision 2: ACM certificate in us-east-1**
CloudFront is a global service managed from us-east-1. It only reads ACM certificates from us-east-1. We created our certificate there even though the rest of our infrastructure could be in any region.

**Decision 3: Use Route53 instead of GoDaddy DNS**
Better AWS integration, Alias record support for CloudFront, and consistency with how real AWS infrastructure is managed at companies.

**Decision 4: 403 → 404 error page mapping**
When a file doesn't exist in S3, S3 returns HTTP 403 (Forbidden) — not 404 (Not Found) — because from S3's perspective, the request is forbidden since the file doesn't exist in the private bucket. We told CloudFront to intercept 403 responses, serve our custom error.html, and return a 404 status code to the browser. This gives users a friendly error page and the correct HTTP status code.

**Decision 5: Redirect HTTP to HTTPS**
We configured CloudFront to redirect all HTTP traffic to HTTPS. Plain HTTP is never served. This is a security and SEO best practice.

---

## What Happens If You Skip Each Service

| If you remove... | What breaks |
|---|---|
| **CloudFront** | No HTTPS on custom domain. No global CDN. S3 must be public. Higher cost. |
| **ACM certificate** | No HTTPS. Browser shows "Not Secure" warning. Users leave. |
| **Route53** | Domain doesn't point to CloudFront. Site unreachable via custom domain. |
| **OAC** | Either S3 must be public (security risk) OR CloudFront can't read files (site broken). |
| **GoDaddy nameserver change** | GoDaddy still controls DNS. Route53 records are ignored. Domain doesn't work. |
| **Default root object (index.html)** | Visiting rohandevops.co.in returns an XML error or blank page instead of your site. |
| **Custom error page** | Bad URLs show raw AWS XML error to users — looks completely broken and unprofessional. |
| **HTTP → HTTPS redirect** | Users on plain HTTP get an insecure connection. Mixed content warnings. |

---

## Problems Faced and How They Were Solved

**Problem 1: Origin path was set to /index.html**
During CloudFront creation, the origin path was accidentally set to `/index.html`. This would have caused requests to append `/index.html` to every path, breaking navigation. Fixed by clearing the origin path field completely.

**Problem 2: WAF (Web Application Firewall) was enabled by default**
The new AWS CloudFront wizard enables WAF security protections by default. WAF costs $14+/month minimum — completely unnecessary for a static portfolio site. Disabled it before creating the distribution.

**Problem 3: "No resources found" when trying to create Route53 alias record**
When creating the A record in Route53, the CloudFront distribution didn't appear in the dropdown because it was still in "Deploying" status. CloudFront takes 5-10 minutes to deploy globally. Had to wait for status to change to "Enabled" before the alias record could be created.

**Problem 4: DNS propagation delay**
After changing GoDaddy nameservers to Route53, Tests 2, 3, and 4 (custom domain) failed while Test 1 (direct CloudFront URL) passed. This is normal — DNS propagation takes 30 minutes to 2 hours globally as nameserver changes spread across the internet. The solution is to wait and test using `https://dnschecker.org`.

---

## Cost Breakdown

| Service | Cost |
|---|---|
| S3 storage (< 1GB) | ~$0.02/month |
| S3 requests (low traffic) | ~$0.01/month |
| CloudFront data transfer (first 1TB/month) | Free tier |
| CloudFront HTTPS requests (first 10M/month) | Free tier |
| Route53 hosted zone | $0.50/month |
| ACM certificate | Free |
| **Total** | **~$0.53/month** |

Compare this to running an EC2 t3.micro instance: ~$8/month + data transfer costs.

---

## What I Learned

**Technical learnings:**
- ACM certificates for CloudFront must always be created in us-east-1, regardless of where other resources are
- S3 with OAC returns 403 (not 404) for missing files — this is a well-known gotcha
- CloudFront cache invalidation is a real operational task that happens after every frontend deployment
- DNS changes are not instant — propagation is a real thing to plan for
- The new CloudFront wizard is simpler but hides advanced settings — some configs must be done post-creation
- Alias records in Route53 are free to query; CNAME records are not — always prefer Alias for AWS resources

**Architecture learnings:**
- Separating concerns: storage (S3), delivery (CloudFront), security (ACM + OAC), and DNS (Route53) are all separate layers
- Defense in depth: S3 is private, OAC restricts access, HTTPS encrypts traffic, Route53 controls DNS — multiple layers of security
- Serverless doesn't mean "no infrastructure" — it means AWS manages the infrastructure for you

**DevOps mindset learnings:**
- Always question default settings — WAF was enabled by default and would have cost money unnecessarily
- Read error messages carefully — "No resources found" in the Route53 dropdown told us to wait for CloudFront to finish deploying
- Test incrementally — testing the CloudFront URL directly (Test 1) before testing the custom domain (Test 2) helped isolate that the issue was DNS, not the infrastructure

---

## Files in This Project

```
mysite/
├── index.html          # Portfolio homepage
├── error.html          # Custom 404 error page
├── style.css           # Styles for both pages
├── DEPLOYMENT_GUIDE.txt # Step-by-step AWS setup guide
└── README.md           # This file — full project explanation
```

---

## Connect With Me

- LinkedIn: [linkedin.com/in/ruhon-deb](https://www.linkedin.com/in/ruhon-deb)
- Email: ruhondeb28@email.com
- Live Site: [https://rohandevops.co.in](https://rohandevops.co.in)

---

*This project is part of a structured AWS learning journey targeting DevOps/SRE roles. Each project covers real-world architecture patterns used in production environments.*