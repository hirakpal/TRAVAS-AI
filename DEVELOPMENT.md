# Development Guide

Guide for setting up and developing TRAVAS-AI.

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/hirakpal/TRAVAS-AI.git
cd TRAVAS-AI
```

### 2. Create Virtual Environment

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using conda
conda create -n travas python=3.10
conda activate travas
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
# Or for development with testing
pip install -e ".[dev]"
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your API keys
nano .env  # or use your editor
```

**Required:**
- `OPENAI_API_KEY` - for OpenAI (or ANTHROPIC_API_KEY or GOOGLE_API_KEY)

### 5. Run Atithi Agent

```bash
# Interactive mode
python main.py

# Single command
python main.py "I need a hotel in Delhi for 3 nights"

# Specify provider
python main.py -p anthropic
python main.py -p gemini

# Show status
python main.py --status
```

## Project Structure

```
TRAVAS-AI/
├── agents/                 # Agent implementations
│   ├── atithi_agent.py    # Hotel concierge agent
│   ├── base_agent.py      # Base agent class
│   └── registry.py        # Agent registry
├── config/                 # Configuration
│   ├── settings.py        # Settings management
│   └── prompts.py         # System prompts
├── llm/                    # LLM provider clients
│   ├── client.py          # LLM factory
│   ├── openai_client.py   # OpenAI implementation
│   └── anthropic_client.py# Anthropic implementation
├── models/                 # Data models
│   ├── guest.py           # Guest profiles
│   ├── hotel.py           # Hotel information
│   └── preferences.py     # User preferences
├── utils/                  # Utilities
│   ├── logger.py          # Logging
│   └── validators.py      # Input validation
├── tests/                  # Test suite
├── main.py                # Entry point
├── requirements.txt       # Dependencies
└── .env.example          # Environment template
```

## Testing

### Run All Tests

```bash
pytest
```

### Run Specific Test

```bash
pytest tests/test_agents.py
pytest tests/test_agents.py::test_atithi_initialization
```

### With Coverage

```bash
pytest --cov=agents --cov=llm --cov=models tests/
```

## Code Quality

### Format Code

```bash
black agents/ llm/ models/ utils/ main.py
```

### Check Style

```bash
flake8 agents/ llm/ models/ utils/ main.py
```

### Type Checking

```bash
mypy agents/ llm/ models/ utils/
```

### All Checks

```bash
black --check agents/ llm/ models/ utils/ main.py
flake8 agents/ llm/ models/ utils/ main.py
mypy agents/ llm/ models/ utils/
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

```bash
# Edit files
# Run tests
pytest

# Format code
black .
flake8 .
```

### 3. Commit Changes

```bash
git add .
git commit -m "Descriptive commit message"
```

### 4. Push and Create PR

```bash
git push origin feature/your-feature-name
# Create pull request on GitHub
```

## Adding a New Agent

### 1. Create Agent File

```bash
touch agents/new_agent.py
```

### 2. Implement Agent

```python
from agents.base_agent import BaseAgent
from config.prompts import NEW_AGENT_SYSTEM_PROMPT

class NewAgent(BaseAgent):
    def __init__(self, provider="openai", api_key=None):
        super().__init__(
            name="NewAgent",
            provider=provider,
            api_key=api_key,
            system_prompt=NEW_AGENT_SYSTEM_PROMPT
        )
        # Implementation...

    def chat(self, user_message: str) -> str:
        # Implementation...
        pass

    def _get_response(self) -> str:
        # Implementation...
        pass
```

### 3. Register Agent

```python
# In agents/registry.py
from agents.new_agent import NewAgent
AgentRegistry.register("new-agent", NewAgent)
```

### 4. Add System Prompt

```python
# In config/prompts.py
NEW_AGENT_SYSTEM_PROMPT = """
Your system prompt here...
"""
```

### 5. Write Tests

```bash
# In tests/test_agents.py
def test_new_agent():
    agent = NewAgent()
    response = agent.chat("test message")
    assert response is not None
```

## Adding a New LLM Provider

### 1. Create Client

```bash
touch llm/provider_client.py
```

### 2. Implement Client

```python
from llm.client import BaseLLMClient

class ProviderClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)
        # Initialize provider client

    def call(self, messages: list, temperature=0.7, max_tokens=2048, **kwargs) -> str:
        # Call provider API
        pass
```

### 3. Register Provider

```python
# In llm/client.py
LLMClient.register_provider("provider_name", ProviderClient)
```

## Environment Variables

See `.env.example` for all available options.

**Critical:**
- Set at least one LLM API key (OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY)
- Set DEFAULT_LLM_PROVIDER to match your available key

**Optional:**
- LOG_LEVEL, LOG_FILE for custom logging
- DATABASE_URL for database storage
- Feature flags for enabling/disabling features

## Troubleshooting

### ImportError: No module named 'openai'

```bash
pip install openai
# Or install all dependencies
pip install -r requirements.txt
```

### API Key Not Found

Check that:
1. `.env` file exists in project root
2. API keys are set correctly in `.env`
3. Running in correct directory

```bash
# Verify .env is loaded
python -c "from config.settings import Settings; print(Settings.OPENAI_API_KEY[:10])"
```

### Rate Limiting

If getting rate limit errors:
1. Check your LLM provider's rate limits
2. Implement exponential backoff
3. Consider using a different provider

### Memory Issues

For large conversation histories:
1. Reduce `max_history` in agent initialization
2. Periodically reset agent with `agent.reset()`
3. Clear old logs

## Documentation

- [README.md](README.md) - Project overview
- [DEVELOPMENT.md](DEVELOPMENT.md) - This file
- Code comments and docstrings

## Contributing

1. Follow PEP 8 style guide
2. Write tests for new features
3. Update documentation
4. Ensure all tests pass
5. Submit pull request

## Support

- GitHub Issues: Report bugs or feature requests
- Email: hirakpal@gmail.com

## License

MIT License - See LICENSE file
