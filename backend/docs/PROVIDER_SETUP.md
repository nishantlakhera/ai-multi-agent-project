# Multi-Provider LLM Setup Guide

Your backend now supports multiple LLM providers with minimal configuration changes!

## Supported Providers

1. **OpenAI** (Default)
2. **OpenRouter** (Recommended for testing - one key for all models)
3. **Groq** (Fast, generous free tier)
4. **Google Gemini**

## Quick Start

### Switch Providers (No Code Changes!)

Just update your `.env` file:

#### 1. OpenAI (Default)
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

#### 2. OpenRouter (Easiest - Single Key)
```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
```

**Get API Key:** https://openrouter.ai/keys

**Free Models:**
- `meta-llama/llama-3.1-8b-instruct:free`
- `google/gemma-2-9b-it:free`
- `mistralai/mistral-7b-instruct:free`

**Browse all models:** https://openrouter.ai/models

#### 3. Groq (Fast & Free)
```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.1-70b-versatile
```

**Get API Key:** https://console.groq.com/

**Available Models:**
- `llama-3.1-70b-versatile` (Best overall)
- `mixtral-8x7b-32768` (Long context)
- `gemma2-9b-it` (Fast)

#### 4. Google Gemini
```env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=...
GEMINI_MODEL=gemini-pro
```

**Get API Key:** https://makersuite.google.com/app/apikey

## Advanced Configuration

### Override Individual Settings

```env
LLM_PROVIDER=openrouter
LLM_API_KEY=sk-or-v1-...           # Overrides provider-specific key
LLM_MODEL=anthropic/claude-3-haiku  # Overrides default model
LLM_BASE_URL=https://custom-api.com # Custom endpoint
```

### Embeddings

For providers that don't support embeddings, you can mix and match:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.1-70b-versatile

# Use OpenAI for embeddings
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-small
```

## Testing Different Providers

### 1. Test with OpenRouter (Free)

```bash
# Update .env
echo "LLM_PROVIDER=openrouter" >> .env
echo "OPENROUTER_API_KEY=sk-or-v1-YOUR-KEY" >> .env
echo "OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free" >> .env

# Restart server
uvicorn main:app --reload --port 8000

# Test
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "Hello!"}'
```

### 2. Compare Providers

Create multiple `.env` files:

```bash
# .env.openai
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# .env.groq
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...

# .env.openrouter
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...
```

Switch between them:
```bash
cp .env.openrouter .env
uvicorn main:app --reload
```

## Cost Comparison

| Provider | Model | Cost per 1M tokens | Notes |
|----------|-------|-------------------|-------|
| OpenAI | gpt-4o-mini | $0.15 / $0.60 | Standard quality |
| OpenRouter | llama-3.1-8b | **FREE** | Good for testing |
| Groq | llama-3.1-70b | **FREE** (limited) | Very fast |
| Gemini | gemini-pro | **FREE** (limited) | Google's latest |

## Troubleshooting

### Error: "Invalid API key"
- Check your API key is correct
- Verify the provider name matches: `openai`, `openrouter`, `groq`, or `gemini`

### Error: "Model not found"
- Check model name is correct for your provider
- For OpenRouter, ensure model includes provider prefix: `meta-llama/...`

### Embeddings Not Working
- Some providers don't support embeddings
- Set `OPENAI_API_KEY` for embeddings even if using another provider for chat

### Slow Responses
- Try Groq (fastest)
- Check your internet connection
- For OpenRouter, try different models

## Best Practices

1. **Development:** Use OpenRouter free models
2. **Testing:** Use Groq for speed
3. **Production:** Use OpenAI or paid OpenRouter models
4. **Cost-sensitive:** Mix providers (Groq for chat, OpenAI for embeddings)

## Need Help?

- OpenRouter Docs: https://openrouter.ai/docs
- Groq Docs: https://console.groq.com/docs
- Gemini Docs: https://ai.google.dev/docs

