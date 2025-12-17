# Quick Start: Testing with Free Models

Your backend now supports multiple LLM providers! Here's how to test immediately:

## Option 1: OpenRouter (Recommended - Easiest)

**1. Get a free API key:**
- Go to: https://openrouter.ai/keys
- Sign up (takes 30 seconds)
- Copy your API key

**2. Update your `.env`:**
```bash
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-YOUR-KEY-HERE
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
```

**3. Restart your server:**
```bash
uvicorn main:app --reload --port 8000
```

**4. Test it:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "message": "Hello, tell me a joke!"}'
```

## Option 2: Groq (Very Fast, Free)

**1. Get API key:**
- Go to: https://console.groq.com/
- Sign up
- Get your API key

**2. Update `.env`:**
```bash
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_YOUR-KEY-HERE
GROQ_MODEL=llama-3.1-70b-versatile
```

**3. Restart and test!**

## Free Models Available

### OpenRouter:
- `meta-llama/llama-3.1-8b-instruct:free` - Good general purpose
- `google/gemma-2-9b-it:free` - Google's model
- `mistralai/mistral-7b-instruct:free` - Mistral AI

### Groq:
- `llama-3.1-70b-versatile` - Powerful, very fast
- `mixtral-8x7b-32768` - Long context (32k tokens)
- `gemma2-9b-it` - Fastest

## What Changed?

- **No code changes needed** - all your agents work exactly the same
- **Just update `.env`** to switch providers
- **Backward compatible** - OpenAI still works if you set `LLM_PROVIDER=openai`

## Need Help?

Check the full guide: `docs/PROVIDER_SETUP.md`

