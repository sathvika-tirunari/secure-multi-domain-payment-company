# Secure Multi-Domain Payment Company (Educational Demo)

> **Educational project.** Use only on systems you own or are explicitly authorised to test.

## 1. Problem Statement
Payment companies split their systems into separate services (public site, customer portal, payment app, admin portal, API) so that one weakness does not expose everything. Students need a safe sandbox to study that design.

## 2. Objective
Build an educational prototype of a fictional payment company with five logical services, shared security controls and **simulated** payments only.

## 3. Features
- Five logical services: main website, customer portal, mock payment app, admin portal, JSON API
- Registration, login and sessions with hashed passwords
- Role-based access (`customer` / `admin`), re-checked in the database each request
- Disabled accounts are blocked immediately, even with an active session
- Mock payments: amount validation (Decimal), merchant/method allow-lists, demo balance, approval/decline rules, review flag
- Audit log of security events (never stores passwords)
- CSRF, security headers, login throttling, JSON error handling for `/api/`
- `.env.example` with placeholders only

## 4. Technologies Used
- Python 3
- Flask (blueprints)
- SQLite
- Jinja2 + CSS

## 5. Folder Structure
```text
06-secure-multi-domain-payment-company/
  .env.example
  .gitignore
  LICENSE
  README.md
  app.py
  config.py
  db.py
  requirements.txt
  security.py
  services/__init__.py
  services/admin.py
  services/api.py
  services/payments.py
  services/portal.py
  services/site.py
  static/style.css
  templates/admin/dashboard.html
  templates/base.html
  templates/error.html
  templates/pay/form.html
  templates/portal/dashboard.html
  templates/portal/login.html
  templates/portal/register.html
  templates/site/about.html
  templates/site/home.html
```

## 6. Installation Steps
1. Install **Python 3.9 or newer** from <https://www.python.org/downloads/> (tick "Add Python to PATH" on Windows).
2. Open a terminal **inside this project folder**.
3. Create and activate a virtual environment:
   - Windows: `python -m venv venv` then `venv\Scripts\activate`
   - macOS/Linux: `python3 -m venv venv` then `source venv/bin/activate`
4. Install the dependencies: `pip install -r requirements.txt`

## 7. Commands to Run
```bash
python app.py
# First run prints the admin password (user: admin). Or set your own first:
#   Windows (PowerShell): $env:DEMO_ADMIN_PASSWORD="YourStrongPass123"
#   macOS/Linux:          export DEMO_ADMIN_PASSWORD="YourStrongPass123"
# Open http://127.0.0.1:5000
```

## 8. How It Works
See **Architecture and data flow** below.

### Architecture
| Service | Path (this demo) | Production idea | Module |
|---|---|---|---|
| Main website | `/` | `www.payco.example` | `services/site.py` |
| Customer portal | `/portal` | `portal.payco.example` | `services/portal.py` |
| Mock payment app | `/pay` | `pay.payco.example` | `services/payments.py` |
| Admin portal | `/admin` | `admin.payco.example` (restricted network) | `services/admin.py` |
| API / backend | `/api` | `api.payco.example` | `services/api.py` |

All services run in **one Flask process** for simplicity; each is a Blueprint so it could later be split into separate deployments on separate domains. Shared code: `security.py` (CSRF, headers, access control, validation), `db.py` (SQLite + audit log), `config.py` (settings from environment).

### Data flow of a payment
1. Customer logs in at the portal (session cookie set, event audited).
2. Customer submits the mock payment form with CSRF token -> `/pay/`.
3. Server validates amount (Decimal, 2 d.p., > 0), merchant and method against allow-lists.
4. `simulate_payment()` applies local rules: decline if over the limit or balance, flag if >= review threshold.
5. The transaction row is saved, balance updated for approved payments, event written to the audit log.
6. The customer sees the result in the portal; the admin sees it in the admin portal; `/api/me/transactions` returns it as JSON.

## 9. Example Input / Output
1. Register `carol_1` (password `CarolPass123`), log in -> demo wallet shows **$1,000.00** (fictional).
2. Pay `12.50` to *Demo Coffee Shop* -> `SIM-XXXXXXXXXXXX: APPROVED - Approved (simulated).` and balance becomes **$987.50**.
3. Pay `1500.00` -> `DECLINED - Over the demo per-payment limit.`
4. Visit `/admin/` as a customer -> **Error 403**.
5. `GET /api/health` -> `{"demo": true, "status": "ok"}`

## 10. Screenshots
_Add your own screenshots after running the project (do not use screenshots from elsewhere)._

| Description | Screenshot |
|---|---|
| Main screen / output | `docs/screenshot-1.png` _(placeholder)_ |
| Another feature | `docs/screenshot-2.png` _(placeholder)_ |

## 11. Demo Link
`<YOUR-DEMO-LINK-HERE>` _(placeholder: this project has not been deployed by the author of this template)_

## 12. Security Measures
- **No real payment data:** the form has no card number, CVV, expiry or bank fields; method and merchant come from fixed lists
- Banner on every page marking the app as an educational demo
- Password hashing, parameterised SQL, server-side validation
- RBAC checked server-side against the database; disabled users locked out
- CSRF tokens, security headers, HttpOnly/SameSite cookies
- Login throttling and audit logging
- Secrets only from environment variables (`.env.example` has placeholders)
- Money stored as integer cents to avoid floating-point errors

## 13. Limitations
- Not a real payment system and must never be used as one
- Single process: the five services share one database and one cookie domain, so real domain isolation is described but not implemented
- In-memory throttling; development server only
- No email, no 2FA, no password reset

## 14. Future Improvements
- Split into separate deployments per subdomain with separate cookies and databases
- Token-based API authentication
- Two-factor authentication for admins
- Automated tests and CI
- Transaction refund simulation

## 15. GitHub Upload Instructions
1. Sign in at <https://github.com> and click **New repository** (the **+** icon, top right).
2. Name it `06-secure-multi-domain-payment-company`, choose Public or Private, and click **Create repository**.
3. On the new repo page click **uploading an existing file**.
4. Drag in the **contents** of this folder (files and sub-folders, *not* the ZIP itself). Hidden files such as `.gitignore` must be included.
5. Write a commit message such as `Initial commit` and click **Commit changes**.
6. Edit `LICENSE` and replace `<YOUR NAME>`; add real screenshots to a `docs/` folder and update the README.

## License
MIT. See `LICENSE`.
