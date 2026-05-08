# Project 1 — Static Website on AWS
## S3 + CloudFront + ACM + Route53

**Live Site:** https://rohandevops.co.in  
**Stack:** AWS S3, CloudFront, ACM, Route53, GoDaddy  
**Cost:** ~$0.50/month  

---

## Architecture

<div align="center">
  <img src="img/Screenshot 2026-05-07 184653.png" >
</div>


---

## Services Used

| Service | Purpose |
|---|---|
| AWS S3 | Stores the static HTML, CSS files (private bucket) |
| AWS CloudFront | CDN — serves files globally with caching, handles HTTPS |
| AWS ACM | Free SSL certificate for HTTPS (must be in us-east-1) |
| AWS Route53 | DNS management — routes domain to CloudFront |
| GoDaddy | Domain registrar — nameservers pointed to Route53 |

---

## Project Files

```
mysite/
├── index.html      → Homepage
├── error.html      → Custom 404 page
└── style.css       → Styling
```

---

## Phase 1 — AWS Console Setup

**Step 1.1 — Log in to AWS Console**

- Go to: https://console.aws.amazon.com
- Sign in with your root account

**Step 1.2 — Set your region to us-east-1**

- Click the region dropdown (top right corner)
- Select **US East (N. Virginia) us-east-1**
- ⚠️ Stay in this region for the ENTIRE project. CloudFront SSL certificates ONLY work from us-east-1.

-----

## Phase 2 — Create S3 Bucket

**Step 2.1 — Go to S3**

- Search for “S3” in the top search bar and click it

**Step 2.2 — Create bucket**

- Click the orange **Create bucket** button
- Bucket name: type your domain name EXACTLY (e.g. `rohandevops.xyz`)
- AWS Region: `us-east-1`
- Scroll to **Block Public Access settings** — make sure ALL checkboxes are **checked**
  - This is intentional — we keep it private, CloudFront will access it
- Click **Create bucket**

**Step 2.3 — Upload your 3 files**

- Click on your newly created bucket
- Click **Upload** → **Add files**
- Select all 3 files: `index.html`, `error.html`, `style.css`
- Click **Upload** and wait for the green “Upload succeeded” message
- Click **Close**

> ✅ Checkpoint: You should see 3 files listed in your bucket. Do NOT touch bucket permissions yet.

-----

## Phase 3 — Create SSL Certificate (ACM)

**Step 3.1 — Go to Certificate Manager**

- Search for “Certificate Manager” and click it
- Confirm you are in `us-east-1`

**Step 3.2 — Request certificate**

- Click **Request a certificate**
- Select **Request a public certificate**
- Click **Next**

**Step 3.3 — Add your domain names**

- Under “Fully qualified domain name”, type your root domain: `rohandevops.xyz`
- Click **Add another name to this certificate**
- Type: `*.rohandevops.xyz` (wildcard — covers www and any subdomain)
- Validation method: **DNS validation** (default)
- Key algorithm: **RSA 2048** (default)
- Click **Request**

**Step 3.4 — Get the CNAME records for validation**

- You will land on the certificate detail page (status: “Pending validation” — this is normal)
- Scroll to the **Domains** section
- Copy both the **CNAME name** and **CNAME value** from one of the rows
  - Both domains usually share the same CNAME record
- ⚠️ Keep this tab open — you need these values in the next phase.

-----

## Phase 4 — Point GoDaddy Domain to Route53

### Part A — Create Hosted Zone

**Step 4.1 — Go to Route53**

- Search for “Route53” and click it
- In the left sidebar, click **Hosted zones** → **Create hosted zone**

**Step 4.2 — Fill in hosted zone details**

- Domain name: `rohandevops.xyz` (no www)
- Type: **Public hosted zone**
- Click **Create hosted zone**

**Step 4.3 — Copy the nameservers**

- Find the **NS** (Name Server) record in the records table
- Copy all 4 values (without the trailing dot), e.g.:
  
  ```
  ns-123.awsdns-45.com
  ns-678.awsdns-90.net
  ns-111.awsdns-22.org
  ns-999.awsdns-01.co.uk
  ```
- Save these — you need them in GoDaddy

### Part B — Update GoDaddy

**Step 4.4 — Log in to GoDaddy**

- Go to: https://www.godaddy.com
- Log in → **My Products** → find your domain → click **DNS** or **Manage**

**Step 4.5 — Change nameservers**

- Scroll to the **Nameservers** section
- Click **Change / Edit**
- Select **Enter my own nameservers (advanced)**
- Delete the existing GoDaddy nameservers
- Enter the 4 AWS nameservers (one per field) and save

> ⏳ Propagation usually takes 5 min to 2 hours (up to 24 hours in some cases). You can continue to next steps.

To verify your nameserver change: https://www.whatsmydns.net/#NS/your_domain_name

-----

## Phase 5 — Add Certificate Validation Record in Route53

**Step 5.1 — Go back to your Hosted Zone**

- Route53 → Hosted Zones → click your domain
- Click **Create record**

**Step 5.2 — Add the CNAME validation record**

- Record name: paste only the part of the CNAME name **before** your domain
  - e.g. if the CNAME name is `_abc123def456.rohandevops.xyz`, type only `_abc123def456`
- Record type: **CNAME**
- Value: paste the CNAME value from ACM (e.g. `_xyz789.acm-validations.aws.`)
- TTL: `300`
- Click **Create records**

**Step 5.3 — Wait for certificate to be issued**

- Go back to Certificate Manager
- Refresh every few minutes until status changes from “Pending validation” to **Issued**
- This usually takes 5–15 minutes
- ⚠️ Do NOT proceed until status is “Issued”

> ✅ Checkpoint: Certificate status = **Issued**

-----

## Phase 6 — Create CloudFront Distribution

**Step 6.1 — Go to CloudFront**

- Search for “CloudFront” and click it
- Click **Create a CloudFront distribution**

**Step 6.2 — Configure the distribution**

- Distribution name: anything you want
- Distribution type: **Single website or app**
- Route 53 managed domain: enter your domain name and click **Next**
- Origin type: **S3**
- S3 bucket: choose the bucket you created, leave all other settings default
- Click **Next** → select **Do not enable security protections** → click **Next**
- Keep everything default on the next screen → click **Next**
- Click **Create distribution**

**Step 6.3 — Edit general settings**

- On the distribution page, find the **General** section and click **Edit**
- Alternate domain name: add your domain (e.g. `www.rohandevops.co.in`)
- Default root object: `index.html`
- Click **Save changes**
- In the General section, click **Route domain to CloudFront** and set up routing automatically

**Step 6.4 — Add custom error page**

- On the distribution page, click **Error pages** → **Create custom error response**
  - HTTP error code: `403`
  - Enable **Customize error response**
  - Response page path: `/error.html`
  - HTTP response code: `404`
- Click **Save changes**

> ✅ You can now access your application via your CloudFront distribution domain name.

## Key Things I Learned

- ACM certificates for CloudFront **must** be created in `us-east-1` — no exceptions
- Keep S3 bucket **private** — use OAC, not public bucket
- S3 returns `403` (not `404`) for missing files when using OAC — always map 403 → error page
- `DNS_PROBE_POSSIBLE` error is a local DNS cache issue — run `ipconfig /flushdns` to fix
- DNS propagation takes 30 min–2 hours after changing nameservers
- CloudFront cache invalidation (`/*`) is needed after every file update in S3

---
## Proof of Work:
<div align="center">
  <img src="img/Screenshot 2026-05-07 132036.png" >
</div>

<div align="center">
  <img src="img/Screenshot 2026-05-07 184109.png" >
</div>

---
## Testing Checklist

- [ ] `https://d2cizf62nlkbin.cloudfront.net` → site loads (direct CloudFront URL)
- [ ] `https://rohandevops.co.in` → site loads with padlock
- [ ] `https://www.rohandevops.co.in` → site loads with padlock
- [ ] `http://rohandevops.co.in` → auto redirects to HTTPS
- [ ] `https://rohandevops.co.in/randompage` → shows custom error page

---

## Connect

- LinkedIn: [linkedin.com/in/ruhon-deb](https://www.linkedin.com/in/ruhon-deb)
- Email: ruhondeb28@email.com
