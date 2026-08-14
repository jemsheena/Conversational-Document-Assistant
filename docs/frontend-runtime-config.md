# Frontend Dynamic Configuration for Cloud Run

The frontend now supports **runtime configuration** of the backend API URL, enabling seamless deployment to Cloud Run where the frontend and backend run as separate services.

## How It Works

### Development (localhost)
- Frontend runs on `http://localhost:5173`
- API requests go to `/api` (proxied by Vite dev server to `http://localhost:8000`)
- No configuration needed

### Production (Cloud Run)
- Frontend deployed to: `https://frontend-hash.run.app`
- Backend deployed to: `https://backend-hash.run.app`
- Nginx startup script injects `BACKEND_URL` environment variable into `index.html` at runtime
- Frontend JavaScript reads `window.__BACKEND_URL__` and uses it for all API calls

## Implementation Details

### Frontend Changes

**`index.html`** — Placeholder for runtime config injection:
```html
<script>
  window.__BACKEND_URL__ = '${BACKEND_URL}' || '';
</script>
```

**`src/api/client.js`** — Smart URL detection:
```javascript
const getApiBase = () => {
  // Cloud Run: use injected backend URL
  if (window.__BACKEND_URL__) {
    return window.__BACKEND_URL__
  }
  // Dev: use /api proxy
  return '/api'
}
```

### Docker & Nginx

**`Dockerfile`** — Multi-stage build with entrypoint:
1. Build React app with Vite
2. Copy to nginx
3. Run entrypoint script before starting nginx

**`docker-entrypoint.sh`** — Startup script:
1. Reads `BACKEND_URL` environment variable
2. Substitutes it into `index.html` using `sed`
3. Reads `PORT` environment variable (Cloud Run sets this)
4. Updates nginx config to listen on dynamic port
5. Starts nginx

### CI/CD Integration

**`.github/workflows/cloud-run-deploy.yml`** — Updated workflow:
1. Build & push backend image
2. Deploy backend to Cloud Run (get service URL)
3. Build & push frontend image
4. Deploy frontend with `BACKEND_URL` env var pointing to backend service URL

## Deployment

### Local Development

```bash
# No configuration needed; uses /api proxy
docker compose up -d
```

### Cloud Run Deployment

#### Option 1: GitHub Actions (Automated)

Push to `main` branch. Workflow automatically:
1. Deploys backend and retrieves its URL
2. Deploys frontend with backend URL configured

**Required GitHub secrets:**
```
GCP_SA_KEY (service account JSON)
GCP_PROJECT_ID (your-project-id)
GCP_REGION (us-central1)
CLOUD_RUN_BACKEND_SERVICE (backend-service-name)
CLOUD_RUN_FRONTEND_SERVICE (frontend-service-name)
DATABASE_URL (postgresql://...)
JWT_SECRET (your-secret)
GROQ_API_KEY (your-groq-key)
```

#### Option 2: Manual Deployment

```bash
# Deploy backend first
gcloud run deploy backend-svc \
  --image gcr.io/PROJECT_ID/backend:latest \
  --region us-central1 \
  --set-env-vars DATABASE_URL=...,JWT_SECRET=...,GROQ_API_KEY=...

# Get backend URL
BACKEND_URL=$(gcloud run services describe backend-svc \
  --region us-central1 \
  --format 'value(status.url)')

# Deploy frontend with backend URL
gcloud run deploy frontend-svc \
  --image gcr.io/PROJECT_ID/frontend:latest \
  --region us-central1 \
  --set-env-vars BACKEND_URL=$BACKEND_URL
```

## Testing

### Verify Frontend Configuration

1. Deploy to Cloud Run
2. Open frontend in browser
3. Open browser console (F12)
4. Check:
   ```javascript
   console.log(window.__BACKEND_URL__)  // Should show backend service URL
   ```
5. Network tab should show API calls to the backend service URL

### Verify API Connectivity

```bash
# Frontend should be able to reach backend
curl -X GET https://frontend-hash.run.app/api/health
# Should return 200 from backend
```

## Environment Variables

### Frontend Container

| Variable | Purpose | Example |
|---|---|---|
| `BACKEND_URL` | Backend API URL injected at runtime | `https://backend-hash.run.app` |
| `PORT` | HTTP listen port (Cloud Run sets this) | `8080` |

### How They Work

1. **BACKEND_URL**: Injected into `index.html` by entrypoint script via `sed` substitution
2. **PORT**: Updated in nginx config at startup to listen on the specified port

## Troubleshooting

### Frontend shows "No relevant sources found" or API errors

- ✅ Check `window.__BACKEND_URL__` in browser console
- ✅ Verify backend service URL is correct
- ✅ Check CORS headers: backend should have `CORS_ORIGINS` set to include frontend service URL

### Blank page or 404 errors

- ✅ Check nginx logs: `gcloud run logs read frontend-svc --region us-central1`
- ✅ Verify `/etc/nginx/conf.d/default.conf` has correct PORT
- ✅ Check if `index.html` was correctly substituted

### API calls failing with CORS errors

Set backend CORS to allow frontend origin:
```env
CORS_ORIGINS=https://frontend-hash.run.app
```

## Related Documentation

- [docs/cloud-run.md](cloud-run.md) — Cloud Run deployment guide
- [README.md](../README.md#deployment) — General deployment info
