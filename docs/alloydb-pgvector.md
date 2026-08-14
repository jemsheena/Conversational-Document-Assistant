# RDS for PostgreSQL + pgvector (AWS Vector Store)

This guide explains how to use **pgvector** with **Amazon RDS for PostgreSQL** for distributed vector search in your AWS deployment (EC2 + RDS).

## Why pgvector + RDS?

| Feature | FAISS (Default) | pgvector + RDS |
|---|---|---|
| **Deployment** | Single instance only | Distributed EC2 instances |
| **Data persistence** | File-based indices | Managed database persistence |
| **Scaling** | Cannot scale horizontally | Multi-AZ failover, read replicas |
| **Cost** | Free (local) | Pay per RDS instance |
| **Backup/Recovery** | Manual file management | AWS automated backups |
| **Multi-AZ** | Not supported | Supported (HA) |

**Use pgvector if:**
- Running multiple EC2 backend instances (ALB + auto-scaling)
- Need automatic failover / high availability
- Want AWS-managed backups
- Plan to scale to >50M vectors

**Stick with FAISS if:**
- Single EC2 instance deployment
- Minimal operational overhead
- <10M vectors, file-based persistence OK

## Architecture

```
Frontend (EC2 or CloudFront + S3)
    ↓
ALB (Application Load Balancer)
    ↓
Backend (EC2 Auto-Scaling Group)
    ↓
RDS for PostgreSQL (Multi-AZ, pgvector extension)
    ↓
Document chunks + embeddings (stored in `chunks.embedding` column)
```

## Setup Steps

### 1. Create RDS Instance with PostgreSQL

#### AWS Console

1. Go to **RDS → Databases → Create database**
2. Select **PostgreSQL** (version 13+)
3. Choose **Multi-AZ deployment** (recommended for production)
4. Select instance class (e.g., `db.t3.medium` for dev, `db.r6i.xlarge` for prod)
5. Configure:
   - Database name: `rag`
   - Username: `postgres`
   - Password: (use AWS Secrets Manager)
6. Storage: 100 GB (gp3, auto-scaling enabled)
7. Connectivity:
   - VPC: Same VPC as EC2 instances
   - Public accessibility: No
   - Security group: Allow port 5432 from EC2 security group
8. Backup: Retention 30 days
9. Enable **Enhanced monitoring**
10. Create database

#### AWS CLI

```bash
aws rds create-db-instance \
  --db-instance-identifier rag-postgres \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 15.3 \
  --allocated-storage 100 \
  --storage-type gp3 \
  --master-username postgres \
  --master-user-password "$(openssl rand -base64 32)" \
  --vpc-security-group-ids sg-xxxxx \
  --db-subnet-group-name default-vpc-xxxxx \
  --multi-az \
  --storage-encrypted \
  --enable-cloudwatch-logs-exports postgresql \
  --region us-east-1
```

### 2. Enable pgvector Extension

Connect to RDS instance and run:

```bash
# Get RDS endpoint
aws rds describe-db-instances \
  --db-instance-identifier rag-postgres \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text
# Output: rag-postgres.xxxxx.us-east-1.rds.amazonaws.com

# Connect via psql or AWS System Manager
aws ssm start-session --target i-xxxxx  # EC2 instance in same VPC

# Install pgvector extension
psql -h rag-postgres.xxxxx.us-east-1.rds.amazonaws.com -U postgres -d postgres

postgres=> CREATE DATABASE rag;
postgres=> \c rag
rag=> CREATE EXTENSION IF NOT EXISTS vector;
rag=> SELECT * FROM pg_extension WHERE extname='vector';
```

Or use AWS Systems Manager Session Manager from an EC2 instance:

```bash
# SSH to EC2 instance
ssh ec2-user@EC2_IP

# Install psql
sudo yum install postgresql15-client -y

# Connect to RDS
psql -h rag-postgres.xxxxx.us-east-1.rds.amazonaws.com -U postgres -d postgres
postgres=> CREATE DATABASE rag;
postgres=> \c rag
rag=> CREATE EXTENSION IF NOT EXISTS vector;
```

### 3. Store Credentials Securely

Use **AWS Secrets Manager** to store database credentials:

```bash
# Create secret
aws secretsmanager create-secret \
  --name rag/rds/postgres \
  --secret-string '{"username":"postgres","password":"...","host":"rag-postgres.xxxxx.rds.amazonaws.com","port":5432,"dbname":"rag"}'

# Retrieve in application
aws secretsmanager get-secret-value \
  --secret-id rag/rds/postgres \
  --query SecretString \
  --output text
```

Update `.env` on EC2:

```env
# Use Secrets Manager ARN or construct from secret
DATABASE_URL=postgresql://postgres:PASSWORD@rag-postgres.xxxxx.us-east-1.rds.amazonaws.com:5432/rag
```

### 4. Install Python Dependencies

On EC2 instance:

```bash
cd /opt/conversational-doc-assistant/backend

# Install pgvector support
pip install pgvector

# Verify
python -c "from pgvector.sqlalchemy import Vector; print('✅ pgvector installed')"
```

### 5. Run Migrations

```bash
# Run Alembic migrations
alembic upgrade head

# Verify schema
psql -h RDS_ENDPOINT -U postgres -d rag -c "\d chunks"
# Should show: embedding | vector(384)
```

### 6. Enable pgvector in Application

Edit `.env`:

```env
VECTOR_STORE=pgvector
DATABASE_URL=postgresql://postgres:PASSWORD@rag-postgres.xxxxx.rds.amazonaws.com:5432/rag
```

Restart backend:

```bash
sudo systemctl restart rag-backend
# or
docker pull ghcr.io/jemsheena/conversational-doc-assistant-backend:latest
docker run -e VECTOR_STORE=pgvector -e DATABASE_URL=... ...
```

## RDS Performance Tuning

### Instance Sizing

| Vectors | Use Case | Instance Size | Estimated Cost |
|---|---|---|---|
| < 1M | Dev/Test | `db.t3.micro` | ~$10/month |
| 1–10M | Small team | `db.t3.medium` | ~$80/month |
| 10–100M | Production | `db.r6i.large` | ~$300/month |
| > 100M | High-scale | `db.r6i.xlarge` + read replicas | $1,000+/month |

### HNSW Index Tuning

Migration creates default HNSW index:

```sql
CREATE INDEX idx_chunks_embedding_hnsw
ON chunks USING hnsw (embedding vector_cosine_ops)
WITH (m=16, ef_construction=64)
```

For RDS, consider:
- **Small (<10M vectors):** Leave defaults
- **Medium (10–100M):** Increase `m=32, ef_construction=128`
- **Large (>100M):** Use IVFFlat instead: `WITH (lists=1000)`

Rebuild:

```sql
DROP INDEX idx_chunks_embedding_hnsw;
CREATE INDEX CONCURRENTLY idx_chunks_embedding_hnsw
ON chunks USING hnsw (embedding vector_cosine_ops)
WITH (m=32, ef_construction=128);
```

### RDS Parameter Group

Optimize for vector workloads:

```bash
# Via AWS Console: RDS → Parameter Groups → Create group
# Or CLI:
aws rds create-db-parameter-group \
  --db-parameter-group-name rag-postgres-params \
  --db-parameter-group-family postgres15 \
  --description "Tuned for RAG + pgvector"

# Modify parameters
aws rds modify-db-parameter-group \
  --db-parameter-group-name rag-postgres-params \
  --parameters "ParameterName=shared_buffers,ParameterValue={DBParameterGroupName:rag-postgres-params,ApplyMethod:immediate},ParameterValue=262144"  # 2GB for medium instance

# Apply to instance
aws rds modify-db-instance \
  --db-instance-identifier rag-postgres \
  --db-parameter-group-name rag-postgres-params \
  --apply-immediately
```

## Deployment with EC2 + ALB

### Multi-Instance Backend (Auto-Scaling)

All backend instances read from the same RDS database:

```yaml
# CloudFormation / Terraform example
Backend:
  LaunchTemplate:
    ImageId: ami-xxxxx  # Custom AMI with backend pre-built
    Environment:
      VECTOR_STORE: pgvector
      DATABASE_URL: arn:aws:secretsmanager:...

  AutoScalingGroup:
    MinSize: 2
    MaxSize: 10
    DesiredCapacity: 2
    TargetGroupArn: arn:aws:elasticloadbalancing:...

ALB:
  TargetGroup:
    HealthCheckPath: /health
    HealthCheckInterval: 30s
```

### RDS Connection Management

For multiple EC2 instances connecting to RDS:

```python
# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from app.config import settings

# Connection pool optimized for RDS
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,           # Adjust based on max connections / number of instances
    max_overflow=20,        # Additional connections
    pool_recycle=3600,      # RDS idle connection timeout
    pool_pre_ping=True,     # Verify connection health
)
```

## AWS Monitoring

### CloudWatch Metrics

Monitor pgvector performance:

```bash
# View RDS metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=rag-postgres \
  --start-time 2026-08-14T00:00:00Z \
  --end-time 2026-08-14T23:59:59Z \
  --period 300 \
  --statistics Average,Maximum

# Create alarm for high CPU
aws cloudwatch put-metric-alarm \
  --alarm-name rag-rds-cpu-high \
  --alarm-description "Alert when RDS CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

### Query Logging

Enable slow query log on RDS:

```bash
# Modify parameter group
aws rds modify-db-parameter-group \
  --db-parameter-group-name rag-postgres-params \
  --parameters "ParameterName=log_min_duration_statement,ParameterValue=1000"  # 1 second

# View logs in CloudWatch Logs
aws logs tail /aws/rds/instance/rag-postgres/postgresql --follow
```

## Cost Estimation (AWS)

| Component | Instance | Monthly Cost |
|---|---|---|
| **RDS PostgreSQL** | `db.t3.medium` | ~$80 |
| **RDS Storage** | 100 GB gp3 | ~$10 |
| **Data transfer (to EC2)** | Same VPC (free) | $0 |
| **RDS Backups** | 30-day retention | ~$5 |
| **CloudWatch Logs** | Minimal | ~$1 |
| **Total** | | ~$96/month |

With read replicas (HA):
- Add `db.t3.medium` read replica: +$80/month
- Total with HA: ~$176/month

## Troubleshooting

### RDS Connection Refused

```bash
# Verify security group
aws ec2 describe-security-groups --group-ids sg-xxxxx

# Check inbound rule:
# Type: PostgreSQL, Protocol: TCP, Port: 5432, Source: EC2-security-group

# Test connectivity from EC2
ssh ec2-user@EC2_IP
psql -h rag-postgres.xxxxx.rds.amazonaws.com -U postgres -d postgres -c "SELECT 1"
```

### Slow Queries

```bash
# Check slow query log in CloudWatch
aws logs tail /aws/rds/instance/rag-postgres/postgresql --follow

# Run ANALYZE to update statistics
psql -h RDS_ENDPOINT -U postgres -d rag -c "ANALYZE chunks;"

# Check index usage
psql -h RDS_ENDPOINT -U postgres -d rag << 'SQL'
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE tablename = 'chunks'
ORDER BY idx_scan DESC;
SQL
```

### Out of Memory

```bash
# Increase RDS instance class
aws rds modify-db-instance \
  --db-instance-identifier rag-postgres \
  --db-instance-class db.r6i.large \
  --apply-immediately

# Or increase parameter group work_mem
aws rds modify-db-parameter-group \
  --db-parameter-group-name rag-postgres-params \
  --parameters "ParameterName=work_mem,ParameterValue=262144"
```

## Migration from FAISS to pgvector (AWS)

```bash
# On EC2 instance with both FAISS indices and RDS access:

# 1. Export FAISS vectors
python scripts/export_faiss_to_csv.py --output /tmp/vectors.csv

# 2. Update .env
VECTOR_STORE=pgvector
DATABASE_URL=postgresql://postgres:PASSWORD@rag-postgres.xxxxx.rds.amazonaws.com:5432/rag

# 3. Run migrations
alembic upgrade head

# 4. Import vectors into RDS
python scripts/import_csv_to_pgvector.py --input /tmp/vectors.csv

# 5. Verify
psql -h RDS_ENDPOINT -U postgres -d rag -c "SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL;"
```

## Related Documentation

- [README.md](../README.md#deployment) — General deployment
- [backend/alembic/versions/003_add_pgvector.py](../backend/alembic/versions/003_add_pgvector.py) — Migration
- [backend/rag/pgvector_store.py](../backend/rag/pgvector_store.py) — Implementation
- [AWS RDS Docs](https://docs.aws.amazon.com/rds/latest/UserGuide/PostgreSQL.pgvector.html) — Official pgvector support

