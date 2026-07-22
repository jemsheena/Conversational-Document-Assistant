# n8n ingestion workflow

This folder contains an importable n8n workflow that accepts a webhook call, forwards an uploaded PDF to `POST /api/ingest`, checks the HTTP response, and sends either a success or failure notification through a Slack incoming webhook.

## What it does

- Receives a webhook request with a PDF upload.
- Forwards the uploaded file to the backend ingest API as multipart form data.
- Checks the backend response status.
- Sends a success notification when ingestion succeeds.
- Logs the failure and sends a failure notification when ingestion does not succeed.

## Import steps

1. Open n8n.
2. Choose **Workflows** -> **Import from File**.
3. Select [`pdf-ingestion-workflow.json`](pdf-ingestion-workflow.json).
4. Set the environment variables or credentials listed below.
5. Activate the workflow and send a test webhook request with a PDF file.

## Required environment variables

- `N8N_BACKEND_URL` - Backend base URL reachable from the n8n container. The compose file defaults this to `http://backend:8000`.
- `SLACK_WEBHOOK_URL` - Slack incoming webhook URL used for success and failure notifications.
- `N8N_ENCRYPTION_KEY` - Persistent encryption key for n8n.
- `N8N_BASIC_AUTH_USER` - Optional basic-auth username for the n8n editor.
- `N8N_BASIC_AUTH_PASSWORD` - Optional basic-auth password for the n8n editor.

## Webhook expectations

- `collection` is optional. If omitted, the backend defaults to `default`.
- The uploaded file should be sent as multipart form data using the field name `files`.
- The webhook path in the exported workflow is `ingest-pdf`.

## Notes

- The workflow uses a Slack incoming webhook via an HTTP Request node so you can fill in a placeholder URL without creating a dedicated Slack app credential.
- This is intentionally lightweight and calls the existing backend ingest endpoint as-is.
