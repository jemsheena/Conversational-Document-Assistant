# Frontend Runtime Configuration (AWS EC2)

This guide explains how to configure the frontend to dynamically detect the backend API URL at runtime, enabling portable deployments across AWS EC2 instances.

## Overview

**Problem:** Frontend has hardcoded `/api` proxy path. On AWS with separate backend and frontend services, this breaks.

**Solution:** Inject `BACKEND_URL` at container startup via nginx entrypoint script, making it available as `window.__BACKEND_URL__` in JavaScript.

## How It Works

### Development (Vite)

```
Frontend (Vite dev server)
  ↓
window.__BACKEND_URL__ = '' (empty, falsy)
  ↓
API client falls back to `/api` proxy (configured in vite.config.js)
  ↓
Backend (same machine)
```

### Production (EC2 + Docker)

```
Frontend (Docker on EC2)
  ↓
docker-entrypoint.sh runs first (nginx setup)
  ↓
Substitutes ${BACKEND_URL} env var into index.html
  ↓
window.__BACKEND_URL__ = 'http://backend-alb.us-east-1.elb.amazonaws.com:8000'
  ↓
API client uses real backend URL
  ↓
Backend (separate EC2 instance or ALB)
```

## Implementation Details

### 1. Frontend HTML Entry Point

**File:** `frontend/index.html`

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Conversational Document Assistant</title>
  </head>
  <body>
    <div id="root"></div>
    
    <!-- Runtime config injected by nginx (EC2) or set to empty (dev) -->
    <script>
      window.__BACKEND_URL__ = '${BACKEND_URL}' || '';
    </script>
    
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

**How it works:**
- On EC2: `${BACKEND_URL}` is replaced by nginx startup script (e.g., `http://backend-alb:8000`)
- In dev: `${BACKEND_URL}` remains literal (is falsy), so API client uses `/api` proxy

### 2. API Client

**File:** `frontend/src/api/client.js`

```javascript
const getApiBase = () => {
  // Production (EC2): window.__BACKEND_URL__ is injected by nginx
  if (typeof window !== 'undefined' && window.__BACKEND_URL__) {
    return window.__BACKEND_URL__;
  }
  // Development: use Vite proxy (configured in vite.config.js)
  return '/api';
};

const API_BASE = import.meta.env.VITE_API_BASE || getApiBase();

export const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

**Fallback chain:**
1. `VITE_API_BASE` environment variable (if set during build)
2. `window.__BACKEND_URL__` (injected by nginx at runtime)
3. `/api` (development fallback, uses Vite proxy)

### 3. Docker Entrypoint Script

**File:** `frontend/docker-entrypoint.sh`

```bash
#!/bin/bash
set -e

# Default port to 80 (can override with PORT env var for EC2, ECS, etc.)
PORT=${PORT:-80}

# If BACKEND_URL is provided, substitute it into index.html
if [ -n "$BACKEND_URL" ]; then
  echo "📝 Injecting BACKEND_URL: $BACKEND_URL"
  sed -i "s|\${BACKEND_URL}|$BACKEND_URL|g" /usr/share/nginx/html/index.html
else
  echo "✅ No BACKEND_URL provided, using /api proxy (dev mode)"
  sed -i "s|\${BACKEND_URL}||g" /usr/share/nginx/html/index.html
fi

# Update nginx to listen on the correct port
sed -i "s|listen 80|listen $PORT|g" /etc/nginx/conf.d/default.conf

# Start nginx
exec nginx -g "daemon off;"
```

**Steps:**
1. Reads `PORT` env var (defaults to 80)
2. If `BACKEND_URL` provided: replaces `${BACKEND_URL}` in index.html
3. If not provided: replaces with empty string (uses `/api` proxy)
4. Updates nginx listen port
5. Starts nginx

### 4. Dockerfile

**File:** `frontend/Dockerfile`

```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Runtime stage
FROM nginx:alpine

# Copy built app
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy and make entrypoint executable
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 80

# Run entrypoint (substitutes vars and starts nginx)
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
```

## AWS Deployment

### Option 1: EC2 + ALB (Recommended)

```bash
# Build Docker image
docker build -t conversational-doc-assistant-frontend:latest frontend/

# Push to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

docker tag conversational-doc-assistant-frontend:latest \
  123456789.dkr.ecr.us-east-1.amazonaws.com/conversational-doc-assistant-frontend:latest

docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/conversational-doc-assistant-frontend:latest

# Launch EC2 instance with docker-compose
docker run -d \
  -e BACKEND_URL=http://backend-alb.us-east-1.elb.amazonaws.com:8000 \
  -p 80:80 \
  123456789.dkr.ecr.us-east-1.amazonaws.com/conversational-doc-assistant-frontend:latest

# Or with ECS task definition (see below)
```

### Option 2: ECS Fargate

```json
{
  "name": "frontend",
  "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/conversational-doc-assistant-frontend:latest",
  "portMappings": [
    {
      "containerPort": 80,
      "hostPort": 80,
      "protocol": "tcp"
    }
  ],
  "environment": [
    {
      "name": "BACKEND_URL",
      "value": "http://backend-alb.us-east-1.elb.amazonaws.com:8000"
    }
  ],
  "logConfiguration": {
    "logDriver": "awslogs",
    "options": {
      "awslogs-group": "/ecs/frontend",
      "awslogs-region": "us-east-1",
      "awslogs-stream-prefix": "ecs"
    }
  }
}
```

### Option 3: Docker Compose (Local Testing)

```yaml
version: '3.8'
services:
  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    ports:
      - "80:80"
    environment:
      BACKEND_URL: http://backend:8000
    depends_on:
      - backend

  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:password@postgres:5432/rag
      VECTOR_STORE: faiss
```

## Testing

### Verify window.__BACKEND_URL__ (Browser)

```javascript
// Open DevTools Console and run:
console.log('BACKEND_URL:', window.__BACKEND_URL__);

// Should output:
// BACKEND_URL: http://backend-alb.us-east-1.elb.amazonaws.com:8000
```

### Verify API Calls (Network Tab)

1. Open DevTools → Network tab
2. Send a chat message
3. Inspect request URL:
   - Should be `http://backend-alb.us-east-1.elb.amazonaws.com:8000/chat/stream`
   - NOT `/api/chat/stream` (unless in dev mode)

### Test Locally with Docker

```bash
# Build image
docker build -t frontend:latest frontend/

# Run with BACKEND_URL
docker run -d \
  -e BACKEND_URL=http://localhost:8000 \
  -p 3000:80 \
  frontend:latest

# Open http://localhost:3000
# Check DevTools Console:
# console.log(window.__BACKEND_URL__)
# Should output: http://localhost:8000
```

## Troubleshooting

### Blank Page or 404

**Problem:** Frontend loads but shows blank page / 404 errors

**Solution:**
```bash
# 1. Check nginx config
docker exec CONTAINER_ID nginx -T

# 2. Check index.html was substituted correctly
docker exec CONTAINER_ID cat /usr/share/nginx/html/index.html | grep BACKEND_URL

# 3. View nginx error logs
docker logs CONTAINER_ID
```

### API Calls Return 404 or Connection Refused

**Problem:** Frontend loads, but API calls fail

**Possible causes:**
1. `BACKEND_URL` not set or wrong
2. Backend service not running
3. Security group rules missing

**Solution:**
```bash
# 1. Verify BACKEND_URL is injected
# In DevTools Console:
console.log('BACKEND_URL:', window.__BACKEND_URL__);

# 2. Test backend connectivity from EC2
curl -v http://backend-alb.us-east-1.elb.amazonaws.com:8000/health

# 3. Check security group allows 8000 from frontend SG
aws ec2 describe-security-groups --group-ids sg-backend \
  --query 'SecurityGroups[0].IpPermissions' | grep 8000
```

### CORS Errors

**Problem:** API calls blocked by CORS

**Solution:** Backend must allow frontend origin

```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://frontend.example.com", "https://frontend.example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Or use wildcard for development:
```python
allow_origins=["*"]  # Only for dev!
```

## Advanced: Multi-Region Deployment

If you have backend services in multiple AWS regions, use Route53 geolocation routing:

```bash
# Create Route53 weighted alias
# Points requests to nearest backend based on region
aws route53 create-resource-record-sets \
  --hosted-zone-id ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.myapp.com",
        "Type": "A",
        "SetIdentifier": "us-east-1",
        "GeolocationLocation": {"CountryCode": "US"},
        "AliasTarget": {
          "HostedZoneId": "Z35SXDOTRQ7X7K",
          "DNSName": "backend-alb-us-east-1.elb.amazonaws.com",
          "EvaluateTargetHealth": true
        }
      }
    }]
  }'

# Set BACKEND_URL to Route53 alias
export BACKEND_URL=http://api.myapp.com:8000
```

## Related Documentation

- [README.md](../README.md#deployment) — General deployment
- [deploy/deploy-aws.sh](../deploy/deploy-aws.sh) — AWS EC2 deployment script
- [docker-entrypoint.sh](../frontend/docker-entrypoint.sh) — Entrypoint source
- [nginx.conf](../frontend/nginx.conf) — Nginx configuration
