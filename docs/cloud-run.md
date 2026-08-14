# Cloud Run Deployment

This project can run as two Cloud Run services:

- `rag-backend` for the FastAPI API
- `rag-frontend` for the built Vite app served by nginx

## Backend image

The backend container now honors the `PORT` environment variable, so it works both locally and on Cloud Run.

## Recommended environment variables

Backend:

- `LLM_PROVIDER=gemini`
- `GEMINI_API_KEY` or `GEMINI_USE_VERTEXAI=true`
- `GEMINI_MODEL=gemini-2.5-flash`
- `DATABASE_URL` pointing at Cloud SQL or AlloyDB
- `JWT_SECRET`
- `STORAGE_BACKEND=s3` or `local`

Frontend:

- `VITE_API_BASE=https://<your-backend-service-url>/api`

## Build and deploy

1. Build and deploy the backend image.
2. Build the frontend with `VITE_API_BASE` set to the backend service URL.
3. Deploy the frontend image.
4. Set CORS on the backend to allow the frontend URL.

## Notes

- If you keep the frontend and backend on separate Cloud Run services, the frontend must be built with a backend base URL. The default `/api` value only works when both services are behind the same reverse proxy.
- For a demo deployment, Cloud Run + managed Postgres/AlloyDB + Secret Manager is a clean portfolio-grade stack.
