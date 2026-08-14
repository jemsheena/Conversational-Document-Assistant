# API Usage Limits & Billing Protection

This guide explains how to protect against unexpected API bills when using Groq, Gemini, or other LLM providers with the Conversational Document Assistant.

## Three Layers of Protection

### 1. **Application-Level Rate Limiting** ✅ Built-in

**Per-user, per-minute limit:**
- Default: 10 requests/minute per user
- Prevents spam and accidental DoS
- Configured via `CHAT_RATE_LIMIT` in `.env`

```env
CHAT_RATE_LIMIT=10  # Max chat requests per user per minute
```

When exceeded:
```
⚠️  Rate limit exceeded. Max 10 requests per minute.
```

### 2. **Daily Token Budget** ✅ Built-in

**Per-user, per-day token tracking:**
- Default: 1,000,000 tokens/day per user (~$0.05–0.27 on Groq free tier, ~$2–5 total)
- Tracks both input and output tokens
- Warns at 80%, blocks at 100%

```env
MAX_DAILY_TOKENS_PER_USER=1000000      # Per-user daily limit
DAILY_TOKEN_WARNING_THRESHOLD_PERCENT=80  # Warn at 80% usage
```

When warning triggers:
```
⚠️  Token budget alert: 85.5% of daily limit used (855,000 / 1,000,000 tokens)
```

When exceeded:
```
Daily token budget exceeded: 1,050,000 / 1,000,000
```

**Quick Reference:**
| Tokens/Day | Groq Cost | Use Case |
|---|---|---|
| 100,000 | ~$0.03 | Light testing |
| 500,000 | ~$0.15 | Small team |
| 1,000,000 | ~$0.30 | Medium usage |
| 5,000,000 | ~$1.50 | Production |

### 3. **Provider Account Limits** 🔧 Manual Setup

#### **Groq Free Tier** (Your Current Provider) ✅

1. Go to [console.groq.com](https://console.groq.com)
2. Sign into your account
3. **Settings → Billing** (if available)
   - Most accounts have no surprise charges on free tier
   - Optional: Enable email alerts
4. **View your API usage:**
   - [console.groq.com/keys](https://console.groq.com/keys) → API key dashboard
   - Shows tokens used, rate limits, quota status

**Pro tip:** Groq free tier is extremely generous. Most accounts never hit paid tiers. The app-level limits above are your primary protection.

---

#### **OpenAI (If You Switch Later)**

1. Go to [platform.openai.com/account/billing/overview](https://platform.openai.com/account/billing/overview)
2. **Billing → Usage Limits** → Set hard limit (e.g., $10)
3. **Billing → Email preferences** → Enable alerts at 50%, 80%, 100%
4. Add payment method (required)

**Cost:** ~$0.15 input / $0.60 output per 1M tokens (10× Groq) — Not recommended for this project

#### **Gemini (If You Switch Later)**

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. **Billing** → Select your project
3. **Budgets and alerts** → Create budget
4. Set monthly limit (e.g., $50)
5. Configure alerts (50%, 90%, 100%)

**Cost:** $0.075 input / $0.30 output per 1M tokens (3× Groq) — Good alternative to Groq

---

## Recommended Settings for Different Scenarios

### **Development (Local Testing)**
```env
CHAT_RATE_LIMIT=20              # Generous for testing
MAX_DAILY_TOKENS_PER_USER=100000  # ~$0.03/day
LLM_PROVIDER=local              # Use Ollama or LM Studio (free)
```

### **Small Team / Free Tier**
```env
CHAT_RATE_LIMIT=10              # Standard
MAX_DAILY_TOKENS_PER_USER=500000 # ~$0.15/day
LLM_PROVIDER=groq               # Groq free tier
```

### **Production with Budget Cap**
```env
CHAT_RATE_LIMIT=5               # Strict
MAX_DAILY_TOKENS_PER_USER=1000000  # ~$0.30/day = ~$9/month
LLM_PROVIDER=groq
```

---

## Monitoring Usage

### **Real-Time Stats Endpoint**

```bash
curl -X GET http://localhost:8000/api/metrics \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Response:
```json
{
  "latency_ms": {
    "mean": 245.3,
    "p95": 890.0,
    "count": 150
  },
  "tokens": {
    "total_in": 45000,
    "total_out": 12000,
    "count": 150
  },
  "retrieval_scores": {
    "mean": 0.72,
    "max": 0.95,
    "count": 150
  }
}
```

### **Per-User Budget Status**

Check user's daily token usage (from application logs or database):
```
User: alice@example.com
Tokens used today: 245,000 / 500,000 (49%)
Requests today: 12 / 600 (2%)
```

---

## Cost Examples (Real Numbers from Project)

**Groq Llama-3.3-70b (Recommended Free Tier)**
- Query: "What is RAG?" (77 chars input)
- Response: 160 tokens output
- Estimated cost: **$0.00003** (free tier)
- Rate limit: 10 req/min = 14,400 req/day

**Your Project's Metrics (Verified)**
| Phase | Duration | Tokens |
|---|---|---|
| Embedding query | 5–15 ms | ~2 |
| FAISS search | 1–5 ms | 0 |
| Reranking | 150–300 ms | 0 |
| LLM streaming | 2–3 sec | 150–600 |
| **Total per query** | **2–3 sec** | **150–650** |

**Monthly Cost Estimates (Groq Free Tier)**
- 100 queries/day = $0/month (free tier)
- 1,000 queries/day = $0/month (free tier)
- 10,000 queries/day = ~$1.50/month (still free tier for most)

---

## Troubleshooting

### "Rate limit exceeded"
- User has sent >10 requests/minute
- Wait 60 seconds or adjust `CHAT_RATE_LIMIT` if needed

### "Daily token budget exceeded"
- User hit their daily token limit
- Wait for daily reset (UTC midnight) or lower `MAX_DAILY_TOKENS_PER_USER`
- Check metrics endpoint to see current usage

### Unexpected bill on Groq/OpenAI
- Review provider console for actual usage
- Check if `CHAT_RATE_LIMIT` is actually enforced (verify middleware loaded)
- Enable provider-level billing alerts immediately

### "Which LLM provider is cheapest?"
1. **Free local:** Ollama/LM Studio (~0 cost, runs on your hardware)
2. **Free cloud:** Groq free tier (~$0 for most usage)
3. **Cheap cloud:** Gemini free tier + paid (~$0.075/1M tokens)
4. **Premium:** OpenAI (~$0.15–5.00/1M tokens)

---

## Related Documentation

- [GROQ_INTEGRATION.md](../GROQ_INTEGRATION.md) — LLM provider setup
- [.env.example](../.env.example) — Full configuration reference
- [README.md](../README.md#model-stack--performance) — Performance metrics & model comparison
