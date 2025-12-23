# Ollama Setup Guide

Your backend now supports **Ollama** for running local LLMs completely free!

## What is Ollama?

Ollama lets you run powerful LLMs locally on your machine:
- ✅ **100% Free** - No API costs
- ✅ **Privacy** - All data stays on your machine
- ✅ **Offline** - Works without internet
- ✅ **Fast** - No network latency
- ✅ **OpenAI Compatible** - Works with your existing code

## Quick Start

### 1. Install Ollama

**macOS:**
```bash
brew install ollama
```

**Or download from:** https://ollama.com/download

### 2. Start Ollama Service

```bash
ollama serve
```

This starts the Ollama API server at `http://localhost:11434`

### 3. Pull Models

**For Chat (choose one):**
```bash
# Llama 3 (8B) - Fast, general purpose
ollama pull llama3

# Mistral (7B) - Good for code and reasoning
ollama pull mistral

# Phi-3 (3.8B) - Very fast, smaller
ollama pull phi3

# Gemma 2 (9B) - Google's model
ollama pull gemma2

# CodeLlama (7B) - Best for coding
ollama pull codellama
```

**For Embeddings:**
```bash
# Nomic Embed Text - Best for RAG
ollama pull nomic-embed-text

# All-MiniLM - Smaller, faster
ollama pull all-minilm
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

# Test chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "Hello!"}'
```

## Available Models

Browse all models: https://ollama.com/library

### Recommended Models:

**General Purpose:**
- `llama3` - Meta's Llama 3 (8B)
- `llama3:70b` - Larger, more capable (requires more RAM)
- `mistral` - Mistral AI (7B)

**Code & Reasoning:**
- `codellama` - Code-focused
- `deepseek-coder` - Excellent for code
- `phi3` - Microsoft's small but capable

**Fast & Small:**
- `phi3:mini` - 2.7B params
- `gemma2:2b` - 2B params
- `tinyllama` - 1.1B params

**Embeddings:**
- `nomic-embed-text` - 137M, best for RAG
- `all-minilm` - 22M, faster
- `mxbai-embed-large` - 335M, highest quality

## Model Sizes & Requirements

| Model | Size | RAM Required | Speed |
|-------|------|--------------|-------|
| phi3:mini | 2.3GB | 4GB | ⚡⚡⚡ Very Fast |
| llama3 | 4.7GB | 8GB | ⚡⚡ Fast |
| mistral | 4.1GB | 8GB | ⚡⚡ Fast |
| llama3:70b | 39GB | 64GB | ⚡ Slower |
| nomic-embed-text | 274MB | 2GB | ⚡⚡⚡ Very Fast |

## Configuration Examples

### Basic Setup (Llama 3)
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

### Fast Setup (Phi-3)
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=phi3:mini
OLLAMA_EMBEDDING_MODEL=all-minilm
```

### Code-Focused Setup
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=codellama
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

### Custom Ollama Host
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://192.168.1.100:11434  # Remote Ollama server
OLLAMA_MODEL=llama3
```

## Ollama Commands

```bash
# List installed models
ollama list

# Run a model interactively
ollama run llama3

# Pull a model
ollama pull mistral

# Remove a model
ollama rm mistral

# Show model info
ollama show llama3

# Check Ollama version
ollama --version
```

## Troubleshooting

### "Connection refused" Error
**Problem:** Ollama service not running
**Solution:**
```bash
ollama serve
```

### "Model not found" Error
**Problem:** Model not pulled
**Solution:**
```bash
ollama pull llama3
ollama pull nomic-embed-text
```

### Slow Responses
**Problem:** Model too large for your machine
**Solution:** Use a smaller model
```env
OLLAMA_MODEL=phi3:mini  # Smaller, faster
```

### Out of Memory
**Problem:** Not enough RAM
**Solution:**
- Close other applications
- Use a smaller model
- Increase swap space

### Embeddings Not Working
**Problem:** Embedding model not pulled
**Solution:**
```bash
ollama pull nomic-embed-text
```

## Performance Tips

1. **Keep Ollama running** - Start with `ollama serve` and leave it running
2. **First request is slow** - Model loads into memory (subsequent requests are fast)
3. **Use smaller models** - Phi-3 and Mistral are fast and capable
4. **GPU acceleration** - Ollama automatically uses GPU if available (CUDA/Metal)
5. **Adjust context length** - Smaller context = faster responses

## Comparison: Cloud vs Ollama

| Feature | Cloud APIs | Ollama |
|---------|-----------|---------|
| Cost | Pay per token | Free |
| Privacy | Data sent to provider | 100% local |
| Internet | Required | Not required |
| Speed | Network latency | No latency |
| Setup | Easy (just API key) | Install required |
| Model Updates | Automatic | Manual (`ollama pull`) |

## Best Practices

1. **Start with Llama 3** - Good balance of quality and speed
2. **Use Nomic for embeddings** - Best for RAG applications
3. **Keep models updated** - Run `ollama pull <model>` periodically
4. **Monitor resources** - Check RAM usage with `htop` or Activity Monitor
5. **Test locally first** - Validate before deploying to production

## Advanced: Multi-Model Setup

Run different models for different tasks:

```python
# In your agents, you could:
# - Use codellama for code generation
# - Use llama3 for general chat
# - Use phi3 for fast responses
```

Update model dynamically in `.env`:
```env
LLM_MODEL=llama3  # or codellama, mistral, etc.
```

## Migration from Cloud to Ollama

Already using OpenAI/Groq? Easy migration:

1. Install Ollama and pull models
2. Update `.env`:
   ```env
   LLM_PROVIDER=ollama
   ```
3. No code changes needed!
4. Test with `python test_provider.py`

## Need Help?

- **Ollama Docs:** https://github.com/ollama/ollama
- **Model Library:** https://ollama.com/library
- **Discord:** https://discord.gg/ollama

---

**You're now running LLMs locally for free! 🎉**

