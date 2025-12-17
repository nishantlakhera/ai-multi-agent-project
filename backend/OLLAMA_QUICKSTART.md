# Quick Start: Using Ollama with Your Backend

## Step-by-Step Setup

### 1. Install Ollama

**macOS:**
```bash
brew install ollama
```

**Or download:** https://ollama.com/download

### 2. Start Ollama
```bash
ollama serve
```
Leave this running in a terminal.

### 3. Pull Models (in a new terminal)

**For Chat:**
```bash
ollama pull llama3
```

**For Embeddings:**
```bash
ollama pull nomic-embed-text
```

### 4. Update Your `.env`

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

### 5. Test It

```bash
# Test configuration
python test_provider.py

# Start backend
uvicorn main:app --reload --port 8000

# Test API
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "Hello from Ollama!"}'
```

## ✅ Benefits

- ✅ **100% Free** - No API costs ever
- ✅ **Privacy** - All data stays on your machine
- ✅ **Fast** - No network latency
- ✅ **Offline** - Works without internet
- ✅ **No Quotas** - Use as much as you want

## 🎯 Recommended Models

**Fast & Good Quality:**
- `llama3` - General purpose (8B)
- `mistral` - Code & reasoning (7B)
- `phi3` - Very fast (3.8B)

**Embeddings:**
- `nomic-embed-text` - Best for RAG (137M)

## 🔧 Troubleshooting

**"Connection refused"**
```bash
# Make sure Ollama is running
ollama serve
```

**"Model not found"**
```bash
# Pull the model first
ollama pull llama3
ollama pull nomic-embed-text
```

**Slow first response**
- Normal! Model loads into memory on first request
- Subsequent requests are fast

## 📚 Full Documentation

See `docs/OLLAMA_SETUP.md` for:
- All available models
- Performance tips
- Advanced configuration
- Troubleshooting guide

---

**You're now running LLMs locally for free! 🎉**

No more quota issues, no API costs, complete privacy!

