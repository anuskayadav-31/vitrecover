# VITRecover

**WEB-01 — VIT Campus Lost & Found Recovery Portal**

VITRecover replaces scattered WhatsApp lost-and-found messages with a campus-specific workflow that protects student identity while still allowing legitimate ownership verification.

## Product idea

The key design decision is that **finding an item does not automatically reveal the finder's identity**. Instead, the finder creates a private challenge such as “What branch is written on the ID card?” A claimant answers it; the finder privately approves or rejects the claim. Only after approval should the parties coordinate the physical handoff.

### Real-world applications

- Lost ID cards and room keys in hostels.
- Calculators/lab equipment left in academic blocks.
- Earphones/wallets recovered in food courts.
- Secure handoff through reception/security desks instead of exposing phone numbers.

## Requirements covered

- Separate LOST/FOUND board.
- VIT-specific landmark/location list.
- Required categories: ID Cards, Room Keys, Calculators, Lab Equipment, Earphones, Wallets.
- Student authentication with password hashing.
- Public listings do not display registration number, email or phone number.
- Private verification challenge + claim response.
- Finder dashboard with Approve/Reject.
- Resolution lifecycle.
- Input validation for allowed locations/categories/statuses.
- Loading/empty/submitted states represented through simple server-rendered UI and empty-state messaging.

## Run locally

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

The SQLite database `vitrecover.db` is created automatically.

## Architecture

```text
Browser
  |
  v
FastAPI application
  |
  +---- Authentication / session cookie
  +---- Listings API / forms
  +---- Private claims
  +---- Finder approval workflow
  +---- Resolution lifecycle
  |
  v
SQLite
```

## Privacy model

The active board intentionally stores and displays only item information. The user's registration number, email and password hash are not rendered into public listing cards. A production deployment should replace the demo cookie/session approach with secure server-side sessions, CSRF protection, HTTPS, rate limiting, audit logs and institutional identity integration.

## Extension roadmap

1. VIT SSO / institutional email verification.
2. Image upload to S3 with malware/content validation.
3. Encrypted private messaging after approval.
4. QR code handoff receipt at a campus checkpoint.
5. Moderator workflow for suspicious listings.
6. AWS deployment with CloudFront/S3 + API Gateway/Lambda + DynamoDB/RDS depending on workload.

This is an educational MVP; it is not intended as a production campus identity system without the security hardening listed above.
