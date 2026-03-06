# Architecture Documentation

## Overview

The Multi-Agent Blog Generator is built using a modular, scalable architecture that separates concerns and allows easy extension. This document explains the key architectural decisions and components.

## Core Principles

### 1. **Agent-Based Architecture**
Each agent is a specialized component with a single responsibility:
- **Researcher**: Gathers information from the web
- **Writer**: Creates blog content from research
- **Editor**: Reviews and provides quality feedback

### 2. **State Management**
- Centralized state using TypedDict for type safety
- Immutable state updates (functional approach)
- State validation at boundaries

### 3. **Provider Abstraction**
- LLM providers abstracted (Ollama, OpenAI)
- Search providers abstracted (DuckDuckGo, Serper, Tavily)
- Easy to add new providers

### 4. **Configuration Management**
- Environment-based configuration
- Pydantic for validation
- Separate concerns: LLM, Search, API, etc.

## Component Breakdown

### State Layer (`src/state/`)
```python
AgentState (TypedDict)
├── Input Fields (topic, requirements, etc.)
├── Research Data
├── Writing Output
├── Editor Feedback
└── Execution Metadata
```

**Responsibilities:**
- Define shared data structure
- Validate state integrity
- Provide factory functions

### Agent Layer (`src/agents/`)
```
BaseAgent (Abstract)
├── ResearcherAgent
├── WriterAgent
└── EditorAgent
```

**BaseAgent provides:**
- Lifecycle management (timing, logging)
- Error handling
- Status tracking
- Metric logging

**Each agent:**
- Inherits from BaseAgent
- Implements `execute(state) -> dict`
- Returns state updates
- Is stateless (no instance variables modified)

### Tool Layer (`src/tools/`)
```
Tools
├── SearchTool (Web search abstraction)
└── LLMProvider (LLM abstraction)
```

**Purpose:**
- Isolate external dependencies
- Provide consistent interfaces
- Enable testing with mocks

### Orchestrator (`src/agents/orchestrator.py`)
```
MultiAgentOrchestrator
├── Initializes agents
├── Builds LangGraph workflow
├── Manages execution
└── Provides run() interface
```

**Workflow Definition:**
```
START → Researcher → Writer → Editor → END
```

With conditional routing in IterativeOrchestrator:
```
START → Researcher → Writer → Editor
                        ↑_________|
                    (if needs_revision)
```

### Configuration Layer (`src/config/`)
- Centralized settings using Pydantic
- Environment variable loading
- Validation on startup
- Provider-specific configurations

### API Layer (`src/api/`) (Optional)
FastAPI application providing:
- REST endpoints for blog generation
- Async support
- Request validation
- Error handling

### CLI Layer (`src/cli/`)
Command-line interface providing:
- Interactive generation
- Batch processing
- Configuration checking
- Rich terminal output

## Data Flow

### 1. Initialization
```
User Request → Configuration → Orchestrator → Agent Initialization
```

### 2. Execution
```
Orchestrator.run()
    ↓
Create Initial State
    ↓
Invoke LangGraph
    ↓
Researcher Agent
    ├── Search Web
    ├── Extract Data
    └── Update State
    ↓
Writer Agent
    ├── Read Research Data
    ├── Generate Blog Post
    └── Update State
    ↓
Editor Agent (optional)
    ├── Review Content
    ├── Assess Quality
    └── Update State
    ↓
Return Final State
```

### 3. State Updates
Each agent returns a dictionary of updates:
```python
{
    "research_data": [...],
    "execution_time": {"Researcher": 5.2},
    "agent_status": {"Researcher": "completed"}
}
```

LangGraph merges these updates into the state.

## Scalability Considerations

### Horizontal Scaling
- **Stateless Agents**: No shared state between requests
- **API Deployment**: Multiple workers via uvicorn
- **Containerization**: Docker support for easy deployment

### Vertical Scaling
- **Async Operations**: Support for async LLM calls
- **Caching**: Research results can be cached
- **Batch Processing**: CLI supports batch mode

### Performance Optimization
- **Parallel Agent Execution**: Some agents can run concurrently
- **Lazy Loading**: Agents only initialized when needed
- **Connection Pooling**: Reuse HTTP connections for search

## Extension Points

### Adding a New Agent
1. Create class inheriting from `BaseAgent`
2. Implement `execute(state) -> dict`
3. Add to orchestrator graph
4. Define edges (dependencies)

Example:
```python
class TranslatorAgent(BaseAgent):
    def execute(self, state):
        blog_post = state["blog_post"]
        translated = self.translate(blog_post)
        return {"translated_post": translated}
```

### Adding a New Search Provider
1. Implement `SearchProvider` interface
2. Add to `SearchTool` provider selection
3. Update configuration schema

### Adding a New LLM Provider
1. Implement `BaseLLMProvider` interface
2. Add to `LLMProvider` initialization
3. Update configuration schema

## Testing Strategy

### Unit Tests
- Test individual components in isolation
- Mock external dependencies (LLM, Search)
- Focus on business logic

### Integration Tests
- Test agent coordination
- Test with real providers (marked `@pytest.mark.integration`)
- Verify state updates

### End-to-End Tests
- Test complete workflows
- Verify output quality
- Performance benchmarks

## Error Handling

### Levels of Error Handling

1. **Tool Level**: Retry with exponential backoff
   ```python
   for attempt in range(max_retries):
       try:
           return tool.execute()
       except Exception:
           time.sleep(2 ** attempt)
   ```

2. **Agent Level**: Graceful degradation
   ```python
   try:
       result = self.execute(state)
   except Exception as e:
       return {"error_log": [error_info]}
   ```

3. **Orchestrator Level**: Comprehensive error reporting
   ```python
   try:
       return self.app.invoke(state)
   except Exception as e:
       logger.error(...)
       raise WorkflowError(...)
   ```

## Security Considerations

1. **API Key Management**
   - Never commit keys to git
   - Use environment variables
   - Validate on startup

2. **Input Validation**
   - Validate all user inputs
   - Sanitize for LLM prompts
   - Length limits on topics

3. **Rate Limiting**
   - API endpoints rate-limited
   - Search API throttling
   - LLM call quotas

4. **Output Sanitization**
   - No sensitive data in logs
   - Error messages don't expose internals

## Monitoring & Observability

### Logging
- Structured logging (JSON format)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Agent-specific loggers

### Metrics
- Execution time per agent
- Success/failure rates
- Quality scores
- Token usage (if using paid APIs)

### Health Checks
- API health endpoint
- LLM connectivity check
- Search API availability

## Future Enhancements

### Short Term
- [ ] Add more search providers (Google, Bing)
- [ ] Support for image generation
- [ ] Multi-language support
- [ ] Template system for different blog styles

### Medium Term
- [ ] RAG integration for knowledge base
- [ ] Fine-tuned models for specific domains
- [ ] A/B testing framework for prompts
- [ ] Analytics dashboard

### Long Term
- [ ] Multi-modal content (text + images + videos)
- [ ] Real-time collaboration features
- [ ] Plugin system for custom agents
- [ ] Distributed workflow execution

## References

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [LangChain Documentation](https://python.langchain.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
