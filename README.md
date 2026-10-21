# Digital Inheritance Vault

A full-stack MVP for storing encrypted digital secrets, assigning nominees, tracking owner heartbeat, and releasing vault contents after inactivity.

## Stack

- Django REST Framework backend with JWT auth
- Fernet encryption for secret content
- React + Vite frontend
- Console email backend for demo release emails

## Run Locally

Backend:

```powershell
cd backend
.venv\Scripts\python manage.py runserver 127.0.0.1:8010
```

Frontend:

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5174
```

Open the frontend at `http://127.0.0.1:5174`.

You can confirm the backend is running at:

- `http://127.0.0.1:8010/`
- `http://127.0.0.1:8010/api/`
- `http://127.0.0.1:8010/api/health/`

## Demo Flow

1. Register a vault owner.
2. Add at least one secret.
3. Add at least one nominee.
4. Open the Demo tab.
5. Click `Simulate inactivity`.
6. Click `Run check`.
7. The Result panel shows the check summary. If the vault releases and nominees exist, the release email content also prints in the Django backend console.

## View Backend Data

Use Django Admin for the easiest database view:

1. Open `http://127.0.0.1:8010/admin/`
2. Login with:
   - Username: `vaultadmin`
   - Password: `VaultAdmin@123`
3. Open the `Vault` models:
   - `Secrets`
   - `Nominees`
   - `User profiles`
   - `Release events`

The `Secrets` admin page shows a decrypted preview and decrypted content field. The raw SQLite table stores encrypted text.

You can also open the admin-only JSON database snapshot after logging into Admin:

```txt
http://127.0.0.1:8010/api/admin-data/
```

For direct SQLite access, open this file with a SQLite viewer:

```txt
D:\DDV\backend\db.sqlite3
```

Useful table names:

- `auth_user`
- `vault_userprofile`
- `vault_secret`
- `vault_nominee`
- `vault_releaseevent`

If you use VS Code, install a SQLite viewer extension, then right-click `backend/db.sqlite3` and open the database. Remember: `vault_secret.encrypted_content` is encrypted, so use Django Admin or `/api/admin-data/` to see decrypted content.

## Backend Endpoints

- `POST /api/register/`
- `POST /api/token/`
- `GET /api/dashboard/`
- `POST /api/heartbeat/`
- `POST /api/simulate-inactivity/`
- `POST /api/check-inactivity/`
- `GET/POST /api/secrets/`
- `GET/POST /api/nominees/`

## Production Notes

This MVP emails decrypted contents for demonstration. A production system should use verified nominees, one-time access links, audit logs, environment-based encryption keys, HTTPS, warning emails, and a scheduled worker such as Celery Beat or cron.
