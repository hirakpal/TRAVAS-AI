# TRAVAS-AI: Travel + AI Agent System

A comprehensive AI-powered travel assistant platform featuring multiple specialized agents to help travelers discover hotels, plan itineraries, and get personalized travel recommendations.

## Features

- **Atithi Agent** — Warm, culturally-aware hotel recommendation assistant
- **Multi-turn Conversations** — Stateful dialogue management
- **Multiple LLM Support** — OpenAI, Anthropic Claude, Google Gemini
- **Verified Information** — No fabricated hotel details or reviews
- **Accessible Design** — Respect for diverse needs and preferences

## Project Structure

```
TRAVAS-AI/
├── agents/
│   ├── __init__.py
│   ├── atithi_agent.py          # Atithi hotel concierge agent
│   ├── base_agent.py            # Base agent class
│   └── registry.py              # Agent registry and factory
├── config/
│   ├── __init__.py
│   ├── settings.py              # Configuration management
│   └── prompts.py               # System prompts library
├── models/
│   ├── __init__.py
│   ├── guest.py                 # Guest profile models
│   ├── hotel.py                 # Hotel information models
│   └── preferences.py           # User preferences
├── llm/
│   ├── __init__.py
│   ├── client.py                # LLM client factory
│   ├── openai_client.py         # OpenAI implementation
│   ├── anthropic_client.py      # Anthropic implementation
│   └── gemini_client.py         # Google Gemini implementation
├── utils/
│   ├── __init__.py
│   ├── logger.py                # Logging utilities
│   └── validators.py            # Input validation
├── tests/
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_models.py
│   └── test_llm.py
├── requirements.txt             # Python dependencies
├── setup.py                     # Package setup
├── .env.example                 # Environment variables template
├── pyproject.toml              # Project metadata
└── main.py                     # Entry point
```

## Installation

### Prerequisites
- Python 3.8+
- pip or uv package manager

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hirakpal/TRAVAS-AI.git
   cd TRAVAS-AI
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

## Quick Start

### Using Atithi Agent (OpenAI)

```python
from agents.atithi_agent import AtithiAgent

# Initialize agent
agent = AtithiAgent(
    provider="openai",
    api_key="your-openai-key"
)

# Start conversation
response = agent.chat(
    "I need a hotel in Delhi for 3 nights with my family. "
    "Budget is around ₹5000 per night."
)

print(response)
```

### Using with Anthropic Claude

```python
from agents.atithi_agent import AtithiAgent

agent = AtithiAgent(
    provider="anthropic",
    api_key="your-anthropic-key"
)

response = agent.chat("What hotels would you recommend in Mumbai?")
```

### Multi-turn Conversation

```python
from agents.atithi_agent import AtithiAgent

agent = AtithiAgent(provider="openai", api_key="your-key")

# First turn
response1 = agent.chat("I'm looking for a hotel in Goa")
print(response1)

# Second turn (context maintained)
response2 = agent.chat("We prefer vegetarian food and need a beach view")
print(response2)

# Third turn
response3 = agent.chat("Can you recommend the top 3 options for us?")
print(response3)
```

## Configuration

### Environment Variables (.env)

```env
# LLM API Keys
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key

# Default Provider
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4-turbo

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/travas.log

# Hotel Data Source
HOTEL_DATA_SOURCE=local  # local, api, database
```

### Settings Configuration

Edit `config/settings.py` to customize:
- Temperature settings for LLM
- Max tokens for responses
- Timeout values
- Retry policies
- Conversation history limits

## Agents

### Atithi Agent

A warm, culturally-aware hotel recommendation assistant that:
- Understands traveler needs through conversation
- Recommends hotels without pressure
- Explains recommendations with reasoning
- Respects dietary and accessibility needs
- Never invents hotel information

**Trigger words:** "hotel", "accommodation", "where to stay", "book a room"

## API Documentation

### Agent Interface

```python
class BaseAgent:
    def chat(self, message: str) -> str:
        """Send a message and get response"""
        
    def reset(self) -> None:
        """Reset conversation history"""
        
    def get_history(self) -> list:
        """Get conversation history"""
```

## Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agents.py

# Run with coverage
pytest --cov=agents tests/
```

## Development

### Adding a New Agent

1. Create `agents/new_agent.py` inheriting from `BaseAgent`
2. Implement required methods: `chat()`, `reset()`, `get_history()`
3. Register in `agents/registry.py`
4. Add tests in `tests/`

### Adding LLM Provider

1. Create `llm/provider_client.py` inheriting from `BaseLLMClient`
2. Implement `call()` method with provider's API
3. Register in `llm/client.py`

## Best Practices

- Always use environment variables for API keys
- Never commit `.env` file with real keys
- Test extensively before production deployment
- Log all interactions for debugging
- Validate user inputs before processing
- Handle API errors gracefully

## Performance

- Response time: < 2 seconds for typical queries
- Context window: Up to 100 conversation turns
- Concurrent users: Limited by LLM provider rate limits

## Troubleshooting

### API Key Issues
- Verify keys are in `.env` file
- Check API quota limits
- Ensure keys have required permissions

### Rate Limiting
- Implement exponential backoff in retry logic
- Check LLM provider's rate limit documentation
- Consider caching for repeated queries

### Memory Issues
- Limit conversation history length
- Clear old sessions periodically
- Use database for long-term storage

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Email: hirakpal@gmail.com

## Roadmap

- [ ] Integration with real hotel APIs
- [ ] Itinerary planning agent
- [ ] Flight recommendation agent
- [ ] Budget planning assistant
- [ ] Multi-language support
- [ ] Web UI/Chat interface
- [ ] Mobile app
- [ ] Admin dashboard

## Acknowledgments

Built with ❤️ for travelers worldwide.

**Remember: Atithi Devo Bhava** — The guest is divine.
