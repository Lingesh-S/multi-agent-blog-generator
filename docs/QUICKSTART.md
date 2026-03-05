# Quick Start Guide

Get your Multi-Agent Blog Generator up and running in 5 minutes!

## Prerequisites

- Python 3.9+ installed
- Ollama installed (or OpenAI API key)
- 10 minutes of your time

## Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/multi-agent-blog-generator.git
cd multi-agent-blog-generator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your preferred settings
# For Ollama (local, free):
#   LLM_PROVIDER=ollama
#   LLM_MODEL=llama3
# For OpenAI:
#   LLM_PROVIDER=openai
#   OPENAI_API_KEY=your_key_here
```

## Step 3: Pull Ollama Model (if using Ollama)

```bash
ollama pull llama3
```

## Step 4: Run Your First Generation

### Option A: Python Script
```python
from src.agents.orchestrator import MultiAgentOrchestrator

orchestrator = MultiAgentOrchestrator()
result = orchestrator.run(topic="The Future of AI")
print(result["blog_post"])
```

### Option B: Command Line
```bash
python -m src.cli.main generate --topic "The Future of AI"
```

### Option C: Example Script
```bash
python examples/basic_usage.py
```

## Step 5: Verify Installation

```bash
# Check system status
python -m src.cli.main check
```

Expected output:
```
✓ Configuration valid
✓ LangGraph
✓ DuckDuckGo Search
✓ Connected to Ollama
✓ Model 'llama3' available
```

## Common Issues

### Issue: "Module not found"
**Solution:** Make sure you're in the virtual environment
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Cannot connect to Ollama"
**Solution:** Start Ollama service
```bash
ollama serve
# In another terminal:
ollama pull llama3
```

### Issue: "DuckDuckGo search failed"
**Solution:** Check internet connection or try different search provider
```bash
# In .env file:
SEARCH_PROVIDER=duckduckgo
```

## Next Steps

- **Customize agents**: See `docs/adding_agents.md`
- **Deploy with Docker**: See `docker/` directory
- **Run tests**: `pytest tests/ -v`
- **Start API server**: `python -m src.api.app`

## Configuration Options

### LLM Providers
```bash
# Ollama (local, free)
LLM_PROVIDER=ollama
LLM_MODEL=llama3

# OpenAI (requires API key)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
OPENAI_API_KEY=sk-...
```

### Search Providers
```bash
# DuckDuckGo (free, no API key)
SEARCH_PROVIDER=duckduckgo

# Serper (requires API key)
SEARCH_PROVIDER=serper
SERPER_API_KEY=your_key

# Tavily (requires API key)
SEARCH_PROVIDER=tavily
TAVILY_API_KEY=your_key
```

### Blog Settings
```bash
# Writing configuration
WRITER_MIN_WORDS=300
EDITOR_ENABLED=true

# Agent behavior
RESEARCHER_RETRIES=3
MAX_CONCURRENT_AGENTS=5
```

## Usage Examples

### Generate with Custom Parameters
```bash
python -m src.cli.main generate \
  --topic "Machine Learning in Healthcare" \
  --audience "healthcare professionals" \
  --tone "professional" \
  --words 800 \
  --output ml_healthcare.md
```

### Batch Generation
Create `batch_config.json`:
```json
{
  "topics": [
    {
      "topic": "AI in Education",
      "audience": "teachers",
      "word_count": 600,
      "output": "ai_education.md"
    },
    {
      "topic": "Blockchain for Supply Chain",
      "audience": "business professionals",
      "word_count": 700,
      "output": "blockchain_supply.md"
    }
  ]
}
```

Run:
```bash
python -m src.cli.main batch batch_config.json
```

## Docker Deployment

```bash
# Build and start services
cd docker
docker-compose up -d

# Check logs
docker-compose logs -f

# Access API
curl http://localhost:8000/health
```

## Getting Help

- **Documentation**: See `docs/` directory
- **Issues**: Open an issue on GitHub
- **Examples**: Check `examples/` directory

## Pro Tips

1. **Start Small**: Test with short topics first
2. **Monitor Logs**: Check `logs/app.log` for details
3. **Experiment**: Try different prompts and configurations
4. **Iterate**: Use the editor agent for quality control
5. **Cache Results**: Enable caching for repeated searches

## What's Next?

After you're comfortable with basic usage:

1. **Extend Agents**: Add custom agents for your use case
2. **Integrate APIs**: Use the FastAPI server in your apps
3. **Optimize Performance**: Enable caching and parallel execution
4. **Deploy Production**: Use Docker for scalable deployment

Happy generating! 🚀
