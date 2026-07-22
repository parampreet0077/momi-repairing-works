# Momi Repairing Works

A full-stack web application for Momi Repairing Works — a workshop that repairs and fabricates agriculture machines, main doors, and chogaths.

---

## Project Structure

```
momi-repairing-works/
├── backend/                  ← Flask API (deploy to Render)
│   ├── app.py                ← Main server
│   ├── requirements.txt
│   ├── Procfile              ← Render deployment config
│   ├── data/                 ← Live JSON database
│   ├── uploads/              ← Uploaded gallery images
│   └── database/             ← Seed/default data (reference copies)
│       ├── seed-users.json
│       ├── seed-site-data.json
│       ├── seed-enquiries.json
│       └── seed-orders.json
│
├── frontend/                 ← Static site (deploy to Vercel / Netlify)
│   ├── index.html
│   ├── services.html
│   ├── contact.html
│   ├── admin-login.html
│   ├── admin.html
│   ├── css/style.css
│   ├── js/script.js
│   └── images/
│
├── .gitignore
├── README.md
└── vercel.json
```

---

## Backend Setup (Local)

```bash
cd backend
pip install -r requirements.txt
python app.py
```

The backend runs on `http://localhost:5000`.

### Environment Variables (Optional)

| Variable           | Purpose                              |
|--------------------|--------------------------------------|
| `MRW_FRONTEND_URL` | Allowed CORS origin — **required** (e.g. `https://momi-repairing-works.vercel.app`)|
| `MRW_SMTP_HOST`    | SMTP server for email notifications  |
| `MRW_SMTP_PORT`    | SMTP port                            |
| `MRW_SMTP_USERNAME`| SMTP username                        |
| `MRW_SMTP_PASSWORD`| SMTP password                        |
| `MRW_NOTIFY_TO`    | Email address to receive enquiries   |
| `FLASK_ENV`        | Set to `production` on Render        |

---

## Admin Login

Credentials are stored in `backend/data/users.json`:

```json
{
  "username": "ranjeetsingh",
  "password": "88900838582"
}
```

To change credentials, edit this file directly.

---

## Frontend Setup (Local)

Open `frontend/index.html` directly in your browser, **or** serve with any static server:

```bash
npx serve frontend
```

For development with the local backend, set `BASE_URL` in `frontend/js/script.js`:

```js
const BASE_URL = "http://localhost:5000";
```

For production, leave `BASE_URL = ""` if using a reverse proxy, or set it to the Render backend URL.

---

## Deployment

### Backend → Render
1. Connect `backend/` folder as the Render service root
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn app:app`
4. Set `FLASK_ENV=production` and `MRW_FRONTEND_URL=<your-vercel-url>` in Render env vars

### Frontend → Vercel
1. Connect `frontend/` folder as the Vercel project root
2. Set `BASE_URL` in `script.js` to your Render backend URL
3. Deploy as a static site (no build step needed)
