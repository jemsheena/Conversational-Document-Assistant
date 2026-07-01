# Groq Integration Guide

## Overview

This Conversational Document Assistant now uses **Groq** as the default LLM provider. Groq provides ultra-fast inference with an OpenAI-compatible API, making it an excellent choice for real-time conversational AI applications.

## Why Groq?

- **⚡ Ultra-Fast**: 10-100x faster inference than traditional cloud providers
- **💰 Cost-Effective**: Generous free tier with competitive pricing
- **🎯 High Quality**: Access to top-tier models (Llama 3.3, Mixtral, Gemma)
- **🔌 Easy Integration**: OpenAI-compatible API for seamless migration
- **🚀 Reliable**: Enterprise-grade infrastructure with high availability

## Quick Start

### 1. Get Your Groq API Key

1. Visit [Groq Console](https://console.groq.com/keys)
2. Sign up or log in
3. Create a new API key
4. Copy your key (starts with `gsk_`)

### 2. Configure Your Application

The application is already configured to use Groq by default. Add your key to a local `.env` file (never commit it):

```bash
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

### 3. Start the Application

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or run backend directly
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

## Available Groq Models

| Model | Context Window | Speed | Best For |
|-------|---------------|-------|----------|
| `llama-3.3-70b-versatile` | 128K tokens | Very Fast | **Recommended** - Best overall performance |
| `llama-3.1-70b-versatile` | 128K tokens | Very Fast | Alternative high-quality option |
| `mixtral-8x7b-32768` | 32K tokens | Ultra Fast | Fastest responses, good quality |
| `gemma2-9b-it` | 8K tokens | Ultra Fast | Lightweight, quick answers |

### Model Selection Guide

**For Document Q&A (Current Use Case):**
- **Best Choice**: `llama-3.3-70b-versatile` - Excellent balance of quality and speed
- **Fastest**: `mixtral-8x7b-32768` - When speed is critical
- **Lightweight**: `gemma2-9b-it` - For simple queries

**To Change Model:**

Edit `.env`:
```bash
GROQ_MODEL=mixtral-8x7b-32768
```

Or set environment variable:
```bash
export GROQ_MODEL=mixtral-8x7b-32768
```

## Configuration Options

### Environment Variables

```bash
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional (with defaults)
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_BASE_URL=https://api.groq.com/openai/v1
LLM_PROVIDER=groq
```

### Docker Compose

The `docker-compose.yml` is already configured with Groq support:

```yaml
environment:
  - LLM_PROVIDER=${LLM_PROVIDER:-groq}
  - GROQ_API_KEY=${GROQ_API_KEY:-}
  - GROQ_MODEL=${GROQ_MODEL:-llama-3.3-70b-versatile}
```

## Performance Characteristics

### Speed Comparison

| Provider | Avg Response Time | Tokens/Second |
|----------|------------------|---------------|
| Groq (Mixtral) | ~0.5s | 500-800 |
| Groq (Llama 3.3) | ~1.0s | 300-500 |
| OpenAI (GPT-4) | ~3-5s | 50-100 |
| HuggingFace (Free) | ~10-30s | 10-30 |

### Cost Comparison (per 1M tokens)

| Provider | Input | Output |
|----------|-------|--------|
| Groq | $0.05-0.27 | $0.10-0.27 |
| OpenAI GPT-4o-mini | $0.15 | $0.60 |
| OpenAI GPT-4 | $5.00 | $15.00 |

*Note: Groq offers a generous free tier for development*

## Switching Between Providers

The application supports multiple LLM providers. To switch:

### Switch to OpenAI

```bash
# .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
DEFAULT_LLM_MODEL=gpt-4o-mini
```

### Switch to HuggingFace (Free)

```bash
# .env
LLM_PROVIDER=huggingface
HUGGINGFACE_API_KEY=hf_...  # Optional
HUGGINGFACE_MODEL=gpt2
```

### Switch to Local LLM (Ollama)

```bash
# .env
LLM_PROVIDER=local
LOCAL_LLM_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=llama3.1:8b
```

## Troubleshooting

### Error: "GROQ_API_KEY not set"

**Solution**: Ensure your `.env` file contains:
```bash
GROQ_API_KEY=gsk_your_actual_key_here
```

### Error: "Invalid Groq API key"

**Solutions**:
1. Verify your API key at [Groq Console](https://console.groq.com/keys)
2. Ensure no extra spaces in `.env` file
3. Regenerate a new API key if needed

### Error: "Model not found"

**Solution**: Use one of the supported models:
- `llama-3.3-70b-versatile`
- `llama-3.1-70b-versatile`
- `mixtral-8x7b-32768`
- `gemma2-9b-it`

### Error: "Rate limit exceeded"

**Solutions**:
1. Wait a few moments and retry
2. Check your usage at [Groq Console](https://console.groq.com)
3. Consider upgrading your plan for higher limits

### Slow Responses

**Possible Causes**:
1. Network latency - Check your internet connection
2. Large context - Reduce document chunk size
3. Model selection - Try `mixtral-8x7b-32768` for faster responses

## API Rate Limits

### Free Tier (Default)
- **Requests per minute**: 30
- **Requests per day**: 14,400
- **Tokens per minute**: 20,000

### Paid Tiers
Visit [Groq Pricing](https://groq.com/pricing) for current limits and pricing.

## Best Practices

### 1. Model Selection
- Use `llama-3.3-70b-versatile` for production (best quality)
- Use `mixtral-8x7b-32768` for development (fastest)
- Use `gemma2-9b-it` for simple queries (most efficient)

### 2. Context Management
- Keep system prompts concise
- Limit retrieved document chunks to 6-12
- Use reranking to improve relevance

### 3. Error Handling
- Implement retry logic for rate limits
- Provide fallback to other providers if needed
- Log errors for monitoring

### 4. Cost Optimization
- Cache frequent queries (already implemented)
- Use appropriate models for task complexity
- Monitor usage in Groq Console

## Advanced Configuration

### Custom Base URL

If using a proxy or custom endpoint:

```bash
GROQ_BASE_URL=https://your-proxy.com/v1
```

### Multiple Environments

**Development** (`.env.development`):
```bash
LLM_PROVIDER=groq
GROQ_MODEL=mixtral-8x7b-32768  # Faster for dev
```

**Production** (`.env.production`):
```bash
LLM_PROVIDER=groq
GROQ_MODEL=llama-3.3-70b-versatile  # Best quality
```

## Monitoring and Logging

The application logs Groq API calls:

```
⚡ Groq Request - Model: llama-3.3-70b-versatile, Base URL: https://api.groq.com/openai/v1
📝 Prompt length: 1234 chars (system) + 567 chars (user)
✅ Response completed successfully
```

Monitor logs for:
- Request patterns
- Error rates
- Response times
- Token usage

## Security Considerations

### API Key Protection

1. **Never commit** `.env` to version control
2. Use `.env.example` for templates
3. Rotate keys regularly
4. Use environment-specific keys

### Production Deployment

```bash
# Use secrets management
export GROQ_API_KEY=$(aws secretsmanager get-secret-value --secret-id groq-api-key)

# Or use Docker secrets
docker secret create groq_api_key groq_key.txt
```

## Support and Resources

- **Groq Documentation**: https://console.groq.com/docs
- **API Reference**: https://console.groq.com/docs/api-reference
- **Community**: https://groq.com/community
- **Status Page**: https://status.groq.com

## Migration from Other Providers

### From OpenAI

Groq uses OpenAI-compatible API, so migration is seamless:

```bash
# Before
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# After
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
```

### From HuggingFace

```bash
# Before
LLM_PROVIDER=huggingface
HUGGINGFACE_API_KEY=hf_...

# After
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
```

## Conclusion

Groq integration provides a powerful, fast, and cost-effective solution for your conversational document assistant. The OpenAI-compatible API ensures easy integration and migration, while the ultra-fast inference speeds deliver an excellent user experience.

For questions or issues, refer to the [Groq Documentation](https://console.groq.com/docs) or check the application logs for detailed error messages.