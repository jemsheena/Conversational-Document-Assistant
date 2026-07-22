# n8n Ingestion Automation

This workflow gives the document-ingestion API a lightweight automation layer: a webhook starts the flow, the uploaded PDF is forwarded to the existing `POST /api/ingest` endpoint, and the result is branched into success or failure notifications. It is intentionally thin and does not change ingestion behavior in the backend; it only wraps the current API with a notification step.

## Importing into n8n

1. Open n8n.
2. Go to **Workflows**.
3. Select **Import from File**.
4. Choose [`automation/n8n/ingest-notification-workflow.json`](n8n/ingest-notification-workflow.json).
5. Save the workflow and set the required environment variables before activating it.

## Required Configuration

- `BACKEND_URL` - Base URL for the backend service reachable from n8n. Defaults to `http://backend:8000`.
- `SLACK_WEBHOOK_URL` - Slack incoming webhook URL used by the success and failure notification nodes.
- `BACKEND_AUTH_TOKEN` - JWT access token used to authenticate the ingest request to the backend.
- `N8N_ENCRYPTION_KEY` - Persistent encryption key for n8n.
- `N8N_HOST` - Hostname for the n8n service.
- `N8N_WEBHOOK_URL` - Public base URL used by n8n when generating webhook links.
- `N8N_EDITOR_BASE_URL` - Base URL for the n8n editor UI.
- `N8N_BLOCK_ENV_ACCESS_IN_NODE` - Set to `false` so node expressions can read `$env.BACKEND_URL` and `$env.SLACK_WEBHOOK_URL`.

## Manual Test

After importing the workflow and starting n8n, trigger it with a multipart upload that includes a PDF file and a `collection` field:

```bash
curl -X POST "http://localhost:5678/webhook/ingest-trigger" \
  -F "collection=demo" \
  -F "files=@./sample.pdf;type=application/pdf"
```

## Authentication

The backend ingest route requires a valid JWT in the `Authorization` header. Set `BACKEND_AUTH_TOKEN` to a real access token from the app, or generate a service JWT signed with the same `JWT_SECRET` used by the backend. Without that token, the ingest request will return `401 Not authenticated`.

## Scope

This workflow calls the existing `/api/ingest` endpoint as-is. It does not alter backend ingestion logic, validation, chunking, embeddings, or storage behavior.
