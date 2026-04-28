# DiceQuest Analytics

🎲 An interactive text adventure game with real-time analytics and multi-language support.

## Overview

DiceQuest Analytics is a portfolio project showcasing a full-stack Python application combining:

- **Game Engine**: Story-driven adventure with dice-based mechanics
- **Backend**: FastAPI REST API for game logic and data persistence
- **Frontend**: Streamlit interface for interactive gameplay and analytics
- **Analytics**: Data analysis and player statistics tracking
- **Multi-language**: Support for English and Hungarian

## Tech Stack

- **Python 3.12** - Modern Python for backend and frontend
- **FastAPI** - High-performance web framework for API
- **Streamlit** - Rapid prototyping for interactive frontend
- **SQLite** - Lightweight database for game data persistence
- **pandas** - Data analysis and statistics
- **PyYAML** - Story and configuration management
- **pytest** - Comprehensive testing framework
- **Ruff** - Linting and formatting
- **GitHub Actions** - CI/CD pipeline
- **Docker** - Containerization for consistent deployment
- **pre-commit** - Git hooks for code quality

## Project Structure

```
dicequest-analytics/
├── app/                        # Backend application
│   ├── api/                   # FastAPI application and routes
│   │   ├── main.py           # FastAPI app setup
│   │   └── routes/           # API endpoint handlers
│   ├── core/                 # Core game logic
│   │   ├── story_engine.py  # Story narrative system
│   │   ├── dice.py          # Dice rolling mechanics
│   │   └── combat.py        # Combat system
│   ├── models/               # Data models
│   │   ├── schemas.py       # Pydantic request/response models
│   │   └── database.py      # SQLite database management
│   └── analytics/            # Analytics engine
│       └── reports.py       # Analytics report generation
├── streamlit_app/            # Frontend application
│   ├── Game.py              # Main game page
│   ├── api_client.py        # HTTP client for backend calls
│   ├── i18n.py              # Shared UI translation helpers
│   ├── ui_translations.py   # HU/EN UI string dictionaries
│   └── pages/               # Multi-page interface
│       └── Analytics.py     # Analytics dashboard
├── data/                     # Game and configuration data
│   ├── story.yaml          # Story scenarios and branching
│   └── i18n/               # Translation files
│       ├── en.yaml         # English translations
│       └── hu.yaml         # Hungarian translations
├── tests/                   # Pytest test suite
├── .github/workflows/       # GitHub Actions CI/CD
├── pyproject.toml          # Project configuration and dependencies
├── Dockerfile              # FastAPI backend container
├── Dockerfile.streamlit    # Streamlit frontend container
├── docker-compose.yml      # Local multi-service orchestration
├── .env.example            # Environment variable reference
├── .pre-commit-config.yaml # Pre-commit hooks configuration
└── README.md               # This file
```

## Installation

### Prerequisites

- Python 3.12+
- pip or uv package manager

### Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/dicequest-analytics.git
cd dicequest-analytics
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -e ".[dev]"
```

4. Install pre-commit hooks:

```bash
pre-commit install
```

## Running the Application

### 1. Start the FastAPI backend

```bash
uvicorn app.api.main:app --reload
```

The API will be available at `http://localhost:8000`

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 2. Start the Streamlit frontend

```bash
streamlit run streamlit_app/Game.py
```

The app will be available at `http://localhost:8501`

## Event Logging (SQLite)

Game events are logged for analytics into `data/dicequest.db`.

- `sessions` stores one row per game session.
- `events` stores gameplay events such as game start, choices, checks, combat, random events, and endings.

This is an MVP persistence layer used for pandas-based analytics. When running with Docker, mount `./data` as a volume to persist the database across restarts. Without a persistent volume, the database resets on each container start — which is acceptable for portfolio/demo use.

## Testing

Run the test suite:

```bash
pytest                          # Run all tests
pytest --cov=app               # Run with coverage report
pytest -v                      # Verbose output
pytest -k "test_name"          # Run specific test
```

## Code Quality

### Formatting

Format code with Ruff:

```bash
ruff format .
```

### Linting

Lint with Ruff:

```bash
ruff check .
ruff check . --fix              # Auto-fix issues
```

### Type Checking

Type check with mypy:

```bash
mypy app
```

### Pre-commit Hooks

Hooks run automatically before commit. To run manually:

```bash
pre-commit run --all-files
```

## Development

### Adding New Features

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Implement your feature with tests
3. Run tests and quality checks
4. Submit a pull request

### Project Guidelines

- Write tests for new features
- Follow PEP 8 style guide
- Use type hints where practical
- Keep functions focused and modular
- Document complex logic

## Deployment

This project consists of two persistent services (FastAPI + Streamlit) and requires a writable filesystem for SQLite. **Vercel is not compatible** with this architecture — it supports only serverless functions and has an ephemeral filesystem.

### Local Docker (recommended for development)

```bash
docker compose up --build
```

- API: `http://localhost:8000`
- Streamlit: `http://localhost:8501`

The `./data` directory is mounted as a volume so the SQLite database persists between restarts.

### Railway (recommended for production)

[Railway](https://railway.app) is the simplest platform for this stack: it supports Docker, persistent volumes, and multiple services in one project.

1. Push the repository to GitHub.
2. Create a new Railway project and connect the repository.
3. Add two services from the same repo:
   - **API service**: Root directory `/`, Dockerfile `Dockerfile`
   - **Streamlit service**: Root directory `/`, Dockerfile `Dockerfile.streamlit`
4. Add a persistent volume to the API service mounted at `/app/data`.
5. Set environment variables in Railway:
   - API service → `ALLOWED_ORIGINS=https://<your-streamlit-service>.railway.app`
   - Streamlit service → `API_BASE_URL=https://<your-api-service>.railway.app`

### Alternative: Streamlit Community Cloud + Railway/Render

The Streamlit frontend can be deployed for free on [Streamlit Community Cloud](https://streamlit.io/cloud) (connects directly to a public GitHub repo). Host the FastAPI backend separately on Railway or Render, then set `API_BASE_URL` in the Streamlit Cloud secrets settings.

### Environment variables reference

See [.env.example](.env.example) for all configurable environment variables.

## Planned Features

- [ ] Full story narrative implementation with branching paths
- [ ] Advanced combat system with special abilities
- [ ] Player progression and leveling system
- [ ] Inventory and item management
- [ ] Multiplayer support via WebSockets
- [ ] Advanced analytics dashboard with charts
- [ ] Achievement and badge system
- [ ] Save/load game functionality
- [ ] Mobile-friendly UI
- [ ] Sound effects and ambient music
- [ ] Difficulty levels and game modes
- [ ] Procedural dungeon generation

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Ensure all checks pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Author

Your Name - [@yourhandle](https://twitter.com/yourhandle)

## Acknowledgments

- FastAPI documentation and community
- Streamlit for rapid prototyping
- pytest for testing framework
- The open-source Python community

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

Happy adventuring! 🎲
