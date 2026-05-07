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

## Deployment Steps

### Step 1 — S3 Bucket
- Create bucket named exactly as your domain (e.g. `rohandevops.co.in`)
- Region: `us-east-1`
- Block ALL public access — keep bucket private
- Upload `index.html`, `error.html`, `style.css`

### Step 2 — ACM Certificate
- Go to Certificate Manager in `us-east-1` (mandatory for CloudFront)
- Request public certificate for `yourdomain.com` and `*.yourdomain.com`
- Validation method: DNS validation
- Add the CNAME validation record in Route53
- Wait for status → **Issued**

### Step 3 — Route53
- Create a public hosted zone for your domain
- Copy the 4 NS records to GoDaddy nameservers
- Add ACM validation CNAME record
- After CloudFront is created, add:
  - A record (Alias) → root domain → CloudFront distribution
  - A record (Alias) → www → CloudFront distribution

### Step 4 — GoDaddy
- Go to DNS → Nameservers → Custom
- Replace GoDaddy nameservers with the 4 Route53 NS records
- Wait 30 min–2 hours for propagation

### Step 5 — CloudFront Distribution
- Origin: your S3 bucket
- Origin path: leave blank
- Enable private S3 access (OAC) — keeps bucket private
- WAF: disable (unnecessary cost for static site)
- After creation, edit Settings:
  - Alternate domain names: `yourdomain.com` and `www.yourdomain.com`
  - Custom SSL certificate: select ACM cert
  - Default root object: `index.html`
- Error pages tab → Create custom error response:
  - HTTP error code: `403`
  - Response page path: `/error.html`
  - HTTP response code: `404`

---

## Key Things I Learned

- ACM certificates for CloudFront **must** be created in `us-east-1` — no exceptions
- Keep S3 bucket **private** — use OAC, not public bucket
- S3 returns `403` (not `404`) for missing files when using OAC — always map 403 → error page
- `DNS_PROBE_POSSIBLE` error is a local DNS cache issue — run `ipconfig /flushdns` to fix
- DNS propagation takes 30 min–2 hours after changing nameservers
- CloudFront cache invalidation (`/*`) is needed after every file update in S3

---
## Proof:
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
