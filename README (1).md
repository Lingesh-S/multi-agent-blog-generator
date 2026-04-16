# 🤖 Multi-Agent Blog Generator with LangGraph

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-green.svg)](https://github.com/langchain-ai/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

> **A production-ready, scalable multi-agent system that orchestrates specialized AI agents to research topics and generate high-quality blog posts automatically.**

Built with **LangGraph** for workflow orchestration, this project demonstrates advanced agentic AI patterns, state management, and enterprise-grade software architecture—perfect for showcasing ML engineering expertise.

## 🎥 Demo

```bash
# Generate a blog post in seconds
$ python -m src.cli.main generate --topic "The Future of AI Agents"

Initializing Multi-Agent Blog Generator...
✓ Researcher gathering information...
✓ Writer drafting content...
✓ Editor reviewing quality...

📄 Blog Post Generated!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: "The Future of AI Agents: Transforming Technology in 2026"
Word Count: 612 words
Quality Score: 0.87
Reading Time: 3 minutes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 🎯 Key Features

### 🔄 **Multi-Agent Architecture**
- **Researcher Agent**: Searches the web using DuckDuckGo/Serper/Tavily APIs
- **Writer Agent**: Generates engaging blog content using LLMs
- **Editor Agent**: Reviews quality and provides actionable feedback
- **Orchestrator**: Coordinates workflow using LangGraph state machines

### 🎨 **Flexible & Extensible**
- 🔌 **Multiple LLM Support**: Ollama (local), OpenAI, or custom providers
- 🔍 **Multiple Search Providers**: DuckDuckGo (free), Serper, Tavily
- 🎭 **Customizable Tones**: Professional, casual, technical, friendly
- 📊 **Configurable Parameters**: Word count, audience, requirements

### 🏗️ **Production-Ready**
- 🐳 **Docker Support**: Containerized deployment with docker-compose
- ⚡ **CLI Interface**: Rich terminal UI with progress indicators
- 🔧 **API Ready**: FastAPI framework prepared for REST endpoints
- 📝 **Comprehensive Logging**: Structured logging with multiple levels
- 🧪 **Testing Framework**: Unit tests with pytest and coverage

### 📈 **Enterprise Features**
- ✅ **Error Handling**: Retry logic with exponential backoff
- ⚙️ **Configuration Management**: Environment-based with validation
- 📊 **Monitoring**: Execution metrics and performance tracking
- 🔐 **Security**: API key management and input validation
- 🎯 **Scalability**: Stateless agents for horizontal scaling

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Agent Orchestrator                      │
│                         (LangGraph)                              │
└─────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
         ┌──────────────┐ ┌──────────┐ ┌──────────────┐
         │  Researcher  │ │  Writer  │ │   Editor     │
         │    Agent     │ │  Agent   │ │   Agent      │
         └──────┬───────┘ └────┬─────┘ └──────┬───────┘
                │              │               │
                ▼              ▼               ▼
         ┌──────────────┐ ┌──────────┐ ┌──────────────┐
         │ Web Search   │ │   LLM    │ │   Quality    │
         │ DuckDuckGo   │ │ Ollama/  │ │  Assessment  │
         │ Serper/Tavily│ │  OpenAI  │ │   & Feedback │
         └──────────────┘ └──────────┘ └──────────────┘

                    Shared State (TypedDict)
         ┌─────────────────────────────────────────┐
         │ • topic, requirements, audience         │
         │ • research_data, sources                │
         │ • blog_post, metadata                   │
         │ • quality_score, feedback               │
         │ • execution_time, status                │
         └─────────────────────────────────────────┘
```

### Workflow
1. **Researcher** searches the web and gathers information
2. **Writer** creates blog post from research data
3. **Editor** reviews quality and provides feedback
4. *Optional*: Loop back to Writer for revisions based on feedback

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Ollama installed (for local LLM) OR OpenAI API key
- Docker (optional, for containerized deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/multi-agent-blog-generator.git
   cd multi-agent-blog-generator
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Pull Ollama model (if using local LLM)**
   ```bash
   ollama pull llama3
   ```

### Basic Usage

#### 🖥️ **Command Line Interface**

```bash
# Simple generation
python -m src.cli.main generate --topic "The Future of AI Agents"

# With custom parameters
python -m src.cli.main generate \
  --topic "Machine Learning in Healthcare" \
  --audience "healthcare professionals" \
  --tone "professional" \
  --words 800 \
  --output ml_healthcare.md

# Batch processing from config file
python -m src.cli.main batch batch_config.json

# Check system health
python -m src.cli.main check
```

#### 🐍 **Python Script**

```python
from src.agents.orchestrator import MultiAgentOrchestrator

# Initialize orchestrator
orchestrator = MultiAgentOrchestrator()

# Generate blog post
result = orchestrator.run(
    topic="The Future of AI Agents",
    user_requirements="Focus on practical applications and business impact",
    target_audience="business professionals",
    tone="professional",
    word_count=600
)

# Access results
print(f"Title: {result['blog_title']}")
print(f"Content: {result['blog_post']}")
print(f"Quality Score: {result.get('quality_score', 'N/A')}")
print(f"Word Count: {result['blog_metadata']['word_count']}")
```

#### 🐳 **Docker Deployment**

```bash
# Start all services (Ollama + Blog Generator)
cd docker
docker-compose up -d

# View logs
docker-compose logs -f blog-generator

# Generate via API (when API is implemented)
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI Agents in 2026",
    "word_count": 500,
    "tone": "professional"
  }'

# Stop all services
docker-compose down
```

## 📁 Project Structure

```
multi-agent-blog-generator/
├── src/
│   ├── agents/              # Agent implementations
│   │   ├── __init__.py
│   │   ├── base.py         # Base agent class
│   │   ├── researcher.py   # Researcher agent
│   │   ├── writer.py       # Writer agent
│   │   ├── editor.py       # Editor agent (NEW)
│   │   └── orchestrator.py # Main workflow orchestrator
│   ├── tools/              # External tools integration
│   │   ├── __init__.py
│   │   ├── search.py       # Web search tools
│   │   └── llm.py          # LLM provider abstractions
│   ├── state/              # State management
│   │   ├── __init__.py
│   │   └── schema.py       # State definitions
│   ├── api/                # REST API (FastAPI)
│   │   ├── __init__.py
│   │   ├── app.py          # API application
│   │   └── routes.py       # API endpoints
│   ├── cli/                # Command-line interface
│   │   ├── __init__.py
│   │   └── main.py
│   ├── config/             # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py
│   └── utils/              # Utility functions
│       ├── __init__.py
│       ├── logger.py
│       └── validators.py
├── tests/                  # Unit and integration tests
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_orchestrator.py
│   └── test_api.py
├── examples/               # Example scripts
│   ├── basic_usage.py
│   ├── custom_workflow.py
│   └── batch_processing.py
├── docker/                 # Docker configuration
│   ├── Dockerfile
│   └── docker-compose.yml
├── docs/                   # Documentation
│   ├── architecture.md
│   ├── adding_agents.md
│   └── deployment.md
├── .env.example           # Environment variables template
├── .gitignore
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
├── pytest.ini            # Pytest configuration
├── setup.py              # Package setup
└── README.md
```

## 🔧 Configuration

### Environment Variables

Configure the system by editing `.env`:

```env
# LLM Provider (ollama or openai)
LLM_PROVIDER=ollama
LLM_MODEL=llama3
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# OpenAI Configuration (if using OpenAI)
OPENAI_API_KEY=your_api_key_here

# Search Configuration
SEARCH_PROVIDER=duckduckgo  # Options: duckduckgo, serper, tavily
SEARCH_MAX_RESULTS=5
SEARCH_TIMEOUT=10

# Application Settings
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
ENVIRONMENT=development

# Agent Configuration
RESEARCHER_RETRIES=3
WRITER_MIN_WORDS=300
EDITOR_ENABLED=true

# Performance
MAX_CONCURRENT_AGENTS=5
AGENT_TIMEOUT=300
CACHE_ENABLED=true
```

### Provider Options

| Provider | Type | Cost | Pros | Cons |
|----------|------|------|------|------|
| **Ollama (llama3)** | LLM | Free | No API costs, runs locally | Requires powerful hardware |
| **OpenAI (GPT-4)** | LLM | Paid | High quality, fast | Requires API key, costs money |
| **DuckDuckGo** | Search | Free | No API key needed | Rate limited |
| **Serper** | Search | Paid | Better results, faster | Requires API key |
| **Tavily** | Search | Paid | AI-optimized search | Requires API key |

## 💼 Use Cases & Applications

### **Content Marketing**
- Generate blog posts for company blogs
- Create technical documentation
- Write product descriptions
- Draft newsletter content

### **Research & Analysis**
- Summarize latest developments in a field
- Create industry trend reports
- Generate literature reviews
- Compile competitive analysis

### **Education**
- Create study guides from topics
- Generate explainer articles
- Write educational content
- Develop course materials

### **Personal Projects**
- Maintain a personal blog
- Document technical projects
- Create learning resources
- Build a content portfolio

## 🔧 Configuration

## 🎨 Extending the System

### Adding a New Agent

1. Create a new agent class in `src/agents/`:
```python
from src.agents.base import BaseAgent
from src.state.schema import AgentState

class ReviewerAgent(BaseAgent):
    def execute(self, state: AgentState) -> dict:
        # Your agent logic here
        return {"review_score": 0.95}
```

2. Register in orchestrator:
```python
workflow.add_node("Reviewer", reviewer_agent.execute)
workflow.add_edge("Writer", "Reviewer")
```

### Adding a New Tool

1. Create tool in `src/tools/`:
```python
def wikipedia_search(query: str) -> str:
    # Implementation
    return results
```

2. Use in agent:
```python
from src.tools.search import wikipedia_search
results = wikipedia_search(state["topic"])
```

## 🧪 Testing

Run the full test suite:
```bash
pytest tests/ -v --cov=src
```

Run specific tests:
```bash
pytest tests/test_agents.py -v
```

## 🐳 Docker Deployment

**Build and run:**
```bash
docker-compose up -d
```

**Access API:**
```
http://localhost:8000
```

## 📊 Performance Considerations

- **Parallel Processing**: Agents can run concurrently where dependencies allow
- **Caching**: Implements LRU cache for repeated searches
- **Rate Limiting**: Built-in throttling for API calls
- **Async Support**: FastAPI endpoints support async operations

## 🔐 Security Best Practices

- API keys stored in environment variables
- Input validation on all endpoints
- Rate limiting on API endpoints
- Sanitization of user inputs
- CORS configuration for production

## 📈 Monitoring & Logging

Structured logging with different levels:
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Agent started", extra={"agent": "researcher"})
logger.error("Search failed", extra={"query": topic})
```

View logs:
```bash
tail -f logs/app.log
```

## 🛠️ Tech Stack

### **Core Framework**
- **LangGraph** - Multi-agent workflow orchestration
- **LangChain** - LLM framework and tooling
- **Python 3.9+** - Primary programming language

### **LLM Providers**
- **Ollama** - Local LLM execution (llama3, mistral, etc.)
- **OpenAI** - GPT-4, GPT-3.5-turbo

### **Search & Data**
- **DuckDuckGo** - Free web search
- **Serper API** - Enhanced search capabilities
- **Tavily API** - AI-optimized search

### **Infrastructure**
- **FastAPI** - Modern web framework for APIs
- **Pydantic** - Data validation and settings
- **Docker** - Containerization
- **Pytest** - Testing framework

### **Developer Tools**
- **Black** - Code formatting
- **Flake8** - Linting
- **MyPy** - Type checking
- **Rich** - Terminal UI

## 🗺️ Roadmap

### ✅ **Completed (v1.0)**
- [x] Multi-agent architecture with LangGraph
- [x] Researcher, Writer, and Editor agents
- [x] Multiple LLM provider support
- [x] CLI interface with Rich output
- [x] Docker deployment
- [x] Comprehensive documentation
- [x] Unit testing framework

### 🚧 **In Progress (v1.1)**
- [ ] REST API implementation with FastAPI
- [ ] Web-based UI dashboard
- [ ] Advanced caching system
- [ ] Prometheus metrics integration

### 🔮 **Planned (v2.0)**
- [ ] **RAG Integration**: Add vector database for knowledge retrieval
- [ ] **Multi-language Support**: Generate content in multiple languages
- [ ] **Image Generation**: Integrate DALL-E or Stable Diffusion
- [ ] **SEO Optimizer Agent**: Optimize content for search engines
- [ ] **Social Media Agent**: Format content for different platforms
- [ ] **A/B Testing**: Test different prompts and strategies
- [ ] **Analytics Dashboard**: Track performance metrics
- [ ] **Custom Templates**: Pre-defined blog styles and formats

### 🌟 **Future Possibilities**
- [ ] Fine-tuned models for specific domains
- [ ] Multi-modal content (text + images + videos)
- [ ] Real-time collaboration features
- [ ] Plugin system for custom agents
- [ ] Cloud deployment templates (AWS, GCP, Azure)
- [ ] Integration with CMS platforms (WordPress, Medium)

## 🎓 Learning Resources

Want to understand how this project works? Check out these resources:

- **LangGraph Tutorial**: [Official Documentation](https://python.langchain.com/docs/langgraph)
- **Multi-Agent Systems**: [LangChain Guide](https://python.langchain.com/docs/use_cases/agent_workflows)
- **Agentic AI Patterns**: [Best Practices](https://www.anthropic.com/index/agentic-ai)
- **Project Architecture**: See `docs/architecture.md` for detailed breakdown

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Search powered by [DuckDuckGo](https://duckduckgo.com/)
- LLM support via [Ollama](https://ollama.com/) and [OpenAI](https://openai.com/)

## 📮 Contact & Support

### **Found a Bug?**
Open an issue on [GitHub Issues](https://github.com/yourusername/multi-agent-blog-generator/issues)

### **Have Questions?**
- 📧 Email: your.email@example.com
- 🐦 Twitter: [@yourtwitter](https://twitter.com/yourtwitter)
- 💼 LinkedIn: [Your Name](https://linkedin.com/in/yourprofile)

### **Want to Contribute?**
See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines

**Project Link**: [https://github.com/yourusername/multi-agent-blog-generator](https://github.com/yourusername/multi-agent-blog-generator)

---

## ⭐ Show Your Support

If this project helped you, please consider:
- ⭐ Starring the repository
- 🐛 Reporting bugs or suggesting features
- 📝 Writing about your experience
- 🤝 Contributing improvements

---

## 📜 Citation

If you use this project in your research or work, please cite:

```bibtex
@software{multi_agent_blog_generator,
  author = {Your Name},
  title = {Multi-Agent Blog Generator with LangGraph},
  year = {2026},
  url = {https://github.com/yourusername/multi-agent-blog-generator}
}
```

---

<div align="center">

**Built with ❤️ using LangGraph and Python**

*Perfect for AI/ML Engineering portfolios and real-world content generation*

[⬆ Back to Top](#-multi-agent-blog-generator-with-langgraph)

</div>
