# GitLab MCP Server

<div align="center">

**A Python-based MCP (Model Context Protocol) server for GitLab integration**

<!-- Build & Quality Badges -->
[![CI](https://github.com/nostoslabs/gitlab-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/nostoslabs/gitlab-mcp/actions/workflows/ci.yml)
[![CodeQL](https://github.com/nostoslabs/gitlab-mcp/actions/workflows/codeql.yml/badge.svg)](https://github.com/nostoslabs/gitlab-mcp/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/gh/nostoslabs/gitlab-mcp/branch/master/graph/badge.svg)](https://codecov.io/gh/nostoslabs/gitlab-mcp)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

<!-- Language & Framework -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-package%20manager-green.svg?logo=python)](https://github.com/astral-sh/uv)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.12.4+-orange.svg)](https://github.com/jlowin/fastmcp)
[![python-gitlab](https://img.shields.io/badge/python--gitlab-6.4.0+-blue.svg?logo=gitlab)](https://python-gitlab.readthedocs.io/)

<!-- Code Quality -->
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://img.shields.io/badge/mypy-checked-blue.svg?logo=python)](http://mypy-lang.org/)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

<!-- Repository Stats -->
[![GitHub stars](https://img.shields.io/github/stars/nostoslabs/gitlab-mcp?style=social)](https://github.com/nostoslabs/gitlab-mcp/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/nostoslabs/gitlab-mcp?style=social)](https://github.com/nostoslabs/gitlab-mcp/network/members)
[![GitHub issues](https://img.shields.io/github/issues/nostoslabs/gitlab-mcp)](https://github.com/nostoslabs/gitlab-mcp/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/nostoslabs/gitlab-mcp)](https://github.com/nostoslabs/gitlab-mcp/pulls)
[![GitHub last commit](https://img.shields.io/github/last-commit/nostoslabs/gitlab-mcp)](https://github.com/nostoslabs/gitlab-mcp/commits/master)

<!-- License & Docker -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-available-blue.svg?logo=docker)](https://github.com/nostoslabs/gitlab-mcp/pkgs/container/gitlab-mcp)

[Features](#features) •
[Quick Start](#quick-start) •
[Documentation](#documentation) •
[Development](#development) •
[Architecture](#architecture)

</div>

---

## Overview

GitLab MCP Server is a comprehensive Python implementation of the Model Context Protocol for GitLab, providing **88 tools** to interact with GitLab's API. Built with Clean Architecture principles and the FastMCP framework, it offers type-safe, tested, and maintainable access to GitLab's full feature set.

### Key Highlights

- **88 GitLab Tools** - Full feature parity with TypeScript implementation
- **Clean Architecture** - 4-layer architecture for maintainability and testability
- **Type-Safe** - Full type hints with mypy strict mode enforcement
- **Well-Tested** - 240+ tests with 72% coverage
- **Production-Ready** - Docker support, CI/CD pipelines, security scanning
- **Multiple Transports** - stdio, SSE, and Streamable HTTP support

---

## Features

### GitLab Operations (88 Tools)

The server provides comprehensive GitLab API access across 19 categories:

| Category | Tools | Description |
|----------|-------|-------------|
| **Issues** | 6 | Create, read, update, delete, and list issues |
| **Merge Requests** | 9 | Full MR lifecycle management including diffs |
| **Projects** | 5 | Project management and search |
| **Pipelines** | 7 | CI/CD pipeline operations and job management |
| **Repository** | 4 | File operations and repository tree navigation |
| **Branches** | 3 | Branch creation, deletion, and listing |
| **Wikis** | 7 | Wiki page management and attachments |
| **Milestones** | 10 | Milestone tracking and burndown charts |
| **Labels** | 3 | Label management and organization |
| **Commits** | 2 | Commit details and diffs |
| **Discussions** | 2 | Issue and MR discussions/threads |
| **Users** | 1 | User information retrieval |
| **Members** | 1 | Project member management |
| **Namespaces** | 3 | Namespace operations and verification |
| **Groups** | 1 | Group project listing |
| **Jobs** | 2 | Pipeline job control (play, cancel) |
| **Issue Links** | 2 | Issue relationship tracking |
| **Draft Notes** | 0 | (Planned - see roadmap) |
| **Events** | 0 | (Planned - see roadmap) |

### Architecture Features

- **Clean Architecture** - Separation of concerns across 4 distinct layers
- **FastMCP Framework** - Modern async-first MCP implementation
- **python-gitlab** - Official GitLab Python client for API access
- **Pydantic** - Data validation and settings management
- **Structured Logging** - Production-ready logging with structlog
- **Retry Logic** - Automatic retries with exponential backoff (tenacity)

### Security & Quality

- **Read-Only Mode** - Optional safety mode for production environments
- **Access Control** - Project allowlist/denylist support
- **Tool Filtering** - Regex-based tool access control
- **Type Safety** - 100% mypy strict mode compliance
- **Security Scanning** - Bandit static analysis and pip-audit
- **Pre-commit Hooks** - Automatic code quality enforcement

---

## Quick Start

### Prerequisites

- **Python 3.11+** - Required for modern type hints and async features
- **[uv](https://github.com/astral-sh/uv)** - Fast Python package manager (recommended)
- **GitLab Personal Access Token** - With appropriate API scopes

### Installation

```bash
# Install uv package manager (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/nostoslabs/gitlab-mcp.git
cd gitlab-mcp

# Install all dependencies
uv sync

# Copy and configure environment variables
cp .env.example .env
# Edit .env and set your GITLAB_PERSONAL_ACCESS_TOKEN
```

### Configuration

Create a `.env` file with your GitLab credentials:

```bash
# ============================================
# Required Configuration
# ============================================
GITLAB_PERSONAL_ACCESS_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx
GITLAB_API_URL=https://gitlab.com  # or your self-hosted GitLab URL

# ============================================
# Optional Configuration
# ============================================

# Project Access Control
GITLAB_PROJECT_ID=123456                      # Default project
GITLAB_ALLOWED_PROJECT_IDS=123456,789012     # Comma-separated list

# Security Features
GITLAB_READ_ONLY_MODE=false                  # Enable read-only mode
GITLAB_DENIED_TOOLS_REGEX=                   # Regex to block tools

# Feature Toggles
USE_GITLAB_WIKI=true                         # Enable wiki tools
USE_MILESTONE=true                           # Enable milestone tools
USE_PIPELINE=true                            # Enable pipeline tools

# Transport Configuration
SSE=false                                    # Server-Sent Events mode
STREAMABLE_HTTP=false                        # Streamable HTTP mode
HOST=127.0.0.1                              # Server host
PORT=8080                                   # Server port

# Network Proxy (optional)
HTTP_PROXY=
HTTPS_PROXY=
NO_PROXY=localhost,127.0.0.1

# Advanced Options
GITLAB_AUTH_COOKIE_PATH=                    # Cookie auth path
GITLAB_COMMIT_FILES_PER_PAGE=20            # Pagination size
LOG_LEVEL=INFO                             # Logging level
```

### Running the Server

```bash
# Run with stdio transport (default)
uv run python -m gitlab_mcp

# Run with Server-Sent Events transport
SSE=true uv run python -m gitlab_mcp

# Run with Streamable HTTP transport
STREAMABLE_HTTP=true HOST=0.0.0.0 PORT=8080 uv run python -m gitlab_mcp
```

### Testing the Installation

```bash
# Run all tests
make test

# Run tests with coverage report
make test-cov

# Run quality checks
make all
```

---

## Architecture

GitLab MCP Server follows **Clean Architecture** principles with 4 distinct layers:

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│  ┌────────────────────────────────────────────────────┐    │
│  │  FastMCP Server (server.py)                        │    │
│  │  • 88 Tool Handlers                                │    │
│  │  • Pydantic Schemas                                │    │
│  │  • Transport: stdio/SSE/HTTP                       │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Use Cases                                          │    │
│  │  • CreateIssue, UpdateMergeRequest, etc.          │    │
│  │  • Business Logic Orchestration                    │    │
│  │  • DTOs (Data Transfer Objects)                   │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Entities                                           │    │
│  │  • Issue, MergeRequest, Project, Pipeline          │    │
│  │  • Pure business logic (no dependencies)           │    │
│  │  • Value Objects: ProjectId, Pagination            │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            ↑
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │  GitLab API Client (python-gitlab + httpx)         │    │
│  │  • Repository Implementations                       │    │
│  │  • Configuration (Pydantic Settings)               │    │
│  │  • Logging (structlog)                             │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
src/gitlab_mcp/
├── domain/                    # Pure business logic (no external deps)
│   ├── entities/             # Issue, MergeRequest, Project, Pipeline
│   └── value_objects/        # ProjectId, Pagination, IssueIid
│
├── application/              # Use cases and orchestration
│   ├── interfaces/          # Repository ports (abstract)
│   ├── dtos/                # Data transfer objects
│   └── use_cases/           # Business logic (CreateIssue, etc.)
│
├── infrastructure/          # External services integration
│   ├── config/             # Pydantic Settings (environment vars)
│   ├── gitlab/             # python-gitlab client & repositories
│   └── logging/            # Structured logging setup
│
├── presentation/           # MCP interface (FastMCP)
│   ├── server.py          # Main FastMCP server setup
│   ├── schemas/           # Pydantic validation schemas
│   └── tools/             # 88 MCP tool handlers (19 categories)
│       ├── issues/
│       ├── merge_requests/
│       ├── projects/
│       ├── pipelines/
│       ├── repository/
│       ├── branches/
│       ├── wikis/
│       ├── milestones/
│       ├── labels/
│       ├── commits/
│       ├── discussions/
│       ├── users/
│       ├── members/
│       ├── namespaces/
│       ├── groups/
│       ├── jobs/
│       ├── issue_links/
│       ├── draft_notes/
│       └── events/
│
├── services/              # Shared services
│   └── gitlab_client_factory.py
│
├── __main__.py           # Entry point
└── server.py             # FastMCP server (main file)
```

---

## Development

### Development Setup

```bash
# Install development dependencies
uv sync --dev

# Install pre-commit hooks
uv run pre-commit install

# Verify installation
make help
```

### Available Commands

The project includes a comprehensive Makefile for all development tasks:

```bash
# Code Quality
make format        # Format code with black and ruff
make lint          # Lint code with ruff (must pass with 0 errors)
make type-check    # Type check with mypy (must pass with 0 errors)

# Testing
make test          # Run all tests
make test-cov      # Run tests with coverage report

# Complete Validation
make all           # Run all quality checks (format + lint + type-check + test)

# Cleanup
make clean         # Remove cache and generated files

# Help
make help          # Show all available commands
```

### Quality Standards

All code must meet these standards before merging:

- **Linting**: Zero ruff errors
- **Type Checking**: Zero mypy errors
- **Formatting**: Black-formatted code
- **Testing**: All tests passing
- **Coverage**: Maintain 70%+ overall coverage

### Testing Strategy

The project follows **Test-Driven Development (TDD)** with three test layers:

```bash
# Unit Tests - Fast, isolated tests
uv run pytest tests/unit/

# Integration Tests - API interaction tests
uv run pytest tests/integration/

# End-to-End Tests - Full workflow tests
uv run pytest tests/e2e/

# Run specific test file
uv run pytest tests/unit/presentation/tools/issues/test_create_issue.py -v

# Run with coverage
uv run pytest --cov=src --cov-report=html --cov-report=term-missing
```

**Coverage Targets by Layer:**

- Domain Layer: 100% (pure business logic)
- Application Layer: 90%+ (use cases)
- Infrastructure Layer: 80%+ (external integrations)
- Presentation Layer: 85%+ (MCP tools)

### Adding New Tools

To add a new GitLab tool, follow the [IMPLEMENTATION_GUIDE.md](docs/IMPLEMENTATION_GUIDE.md):

1. **Domain**: Create entity if needed (e.g., `Issue`, `MergeRequest`)
2. **Application**: Create use case with tests (e.g., `CreateIssueUseCase`)
3. **Infrastructure**: Implement repository method for API calls
4. **Presentation**: Create Pydantic schema and MCP tool handler
5. **Testing**: Write unit, integration, and e2e tests
6. **Documentation**: Update tool catalog and API docs

### Pre-commit Hooks

The project uses pre-commit hooks to enforce quality:

- Trailing whitespace removal
- End-of-file fixer
- YAML validation
- Large file check
- Black formatting
- Ruff linting
- Mypy type checking
- Bandit security scanning

```bash
# Run manually
uv run pre-commit run --all-files
```

---

## Docker Deployment

### Building the Image

```bash
# Build the Docker image
docker build -t gitlab-mcp .

# Build with specific Python version
docker build --build-arg PYTHON_VERSION=3.12 -t gitlab-mcp:py312 .
```

### Running with Docker

```bash
# Run with environment file
docker run -it --env-file .env gitlab-mcp

# Run with SSE transport
docker run -it --env-file .env -p 8080:8080 -e SSE=true gitlab-mcp

# Run in detached mode
docker run -d --name gitlab-mcp-server --env-file .env gitlab-mcp
```

### Docker Compose

```bash
# Start the server
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the server
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

The Docker image uses:
- **Multi-stage build** for minimal size
- **Chainguard Python base** for security
- **Health checks** for container monitoring
- **Non-root user** for security (planned)

---

## CI/CD

### GitHub Actions Workflows

The project includes 5 automated workflows:

1. **CI** (`.github/workflows/ci.yml`)
   - Code quality checks (black, ruff, mypy)
   - Test execution with coverage
   - Security scanning (bandit, pip-audit)
   - Codecov integration

2. **CodeQL** (`.github/workflows/codeql.yml`)
   - Security vulnerability scanning
   - Code quality analysis

3. **Docker Publish** (`.github/workflows/docker-publish.yml`)
   - Automated Docker image builds
   - Push to container registry

4. **Release** (`.github/workflows/release.yml`)
   - Automated version tagging
   - Release notes generation

5. **SonarCloud** (`.github/workflows/sonarcloud.yml`)
   - Code quality metrics
   - Technical debt tracking

### Running CI Locally

```bash
# Run the same checks as CI
make all

# Individual checks
make format
make lint
make type-check
make test-cov
```

---

## Documentation

Comprehensive documentation is available in the `docs/` directory:

| Document | Description |
|----------|-------------|
| **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** | Clean Architecture principles and layer details |
| **[IMPLEMENTATION_GUIDE.md](docs/IMPLEMENTATION_GUIDE.md)** | Step-by-step guide for implementing tools |
| **[TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** | TDD approach and testing patterns |
| **[QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** | Code templates and quick snippets |
| **[MISSING_TOOLS_ROADMAP.md](docs/MISSING_TOOLS_ROADMAP.md)** | Future tool implementation plan |

### Additional Resources

- **TypeScript Reference**: The original TypeScript implementation is preserved in `old/` for reference
- **API Documentation**: See [GitLab API Docs](https://docs.gitlab.com/ee/api/)
- **python-gitlab**: [Official Documentation](https://python-gitlab.readthedocs.io/)
- **FastMCP**: [Framework Documentation](https://github.com/jlowin/fastmcp)

---

## Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITLAB_PERSONAL_ACCESS_TOKEN` | Yes | - | GitLab API token |
| `GITLAB_API_URL` | No | `https://gitlab.com` | GitLab instance URL |
| `GITLAB_PROJECT_ID` | No | - | Default project ID |
| `GITLAB_ALLOWED_PROJECT_IDS` | No | - | Allowed project IDs (comma-separated) |
| `GITLAB_READ_ONLY_MODE` | No | `false` | Enable read-only mode |
| `GITLAB_DENIED_TOOLS_REGEX` | No | - | Regex to block specific tools |
| `USE_GITLAB_WIKI` | No | `true` | Enable wiki tools |
| `USE_MILESTONE` | No | `true` | Enable milestone tools |
| `USE_PIPELINE` | No | `true` | Enable pipeline tools |
| `SSE` | No | `false` | Use Server-Sent Events transport |
| `STREAMABLE_HTTP` | No | `false` | Use Streamable HTTP transport |
| `HOST` | No | `127.0.0.1` | Server host (SSE/HTTP modes) |
| `PORT` | No | `8080` | Server port (SSE/HTTP modes) |
| `HTTP_PROXY` | No | - | HTTP proxy URL |
| `HTTPS_PROXY` | No | - | HTTPS proxy URL |
| `NO_PROXY` | No | - | Proxy bypass list |
| `GITLAB_AUTH_COOKIE_PATH` | No | - | Cookie authentication file |
| `GITLAB_COMMIT_FILES_PER_PAGE` | No | `20` | Commit pagination size |
| `LOG_LEVEL` | No | `INFO` | Logging level |

### Transport Modes

The server supports three transport modes with the following priority:

1. **Streamable HTTP** (if `STREAMABLE_HTTP=true`) - Highest priority
2. **SSE** (if `SSE=true` and `STREAMABLE_HTTP!=true`) - Medium priority
3. **stdio** (default) - Standard input/output

---

## Troubleshooting

### Common Issues

**Issue**: `GITLAB_PERSONAL_ACCESS_TOKEN not set`
```bash
# Solution: Set your token in .env file
echo "GITLAB_PERSONAL_ACCESS_TOKEN=glpat-xxxxxxxxxxxx" >> .env
```

**Issue**: Tests failing with authentication errors
```bash
# Solution: Use test token for unit tests
env GITLAB_PERSONAL_ACCESS_TOKEN=test_token uv run pytest tests/unit/
```

**Issue**: Import errors when running the server
```bash
# Solution: Reinstall dependencies
uv sync --reinstall
```

**Issue**: Type checking errors
```bash
# Solution: Run mypy with verbose output
uv run mypy src/ --verbose
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
LOG_LEVEL=DEBUG uv run python -m gitlab_mcp
```

---

## Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Write** tests for your changes
4. **Ensure** all quality checks pass (`make all`)
5. **Commit** your changes
6. **Push** to your branch
7. **Open** a Pull Request

### Code Style

- Follow PEP 8 (enforced by Black and Ruff)
- Use type hints for all functions
- Write docstrings for public APIs
- Keep functions focused and testable
- Maintain Clean Architecture boundaries

---

## Project Status

### Current Implementation

- ✅ **Core Infrastructure**: Complete
- ✅ **88 GitLab Tools**: Fully implemented
- ✅ **Clean Architecture**: 4 layers implemented
- ✅ **Testing Framework**: 240+ tests, 72% coverage
- ✅ **CI/CD**: GitHub Actions workflows
- ✅ **Docker**: Production-ready containers
- ✅ **Documentation**: Comprehensive guides

### Roadmap

See [MISSING_TOOLS_ROADMAP.md](docs/MISSING_TOOLS_ROADMAP.md) for future enhancements.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **FastMCP** - Modern MCP framework by @jlowin
- **python-gitlab** - Official GitLab Python client
- **TypeScript Version** - Original implementation (preserved in `old/` directory)
- **Clean Architecture** - Inspired by Uncle Bob's architecture principles

---

<div align="center">

**Made with ❤️ using Python and Clean Architecture**

[Report Bug](https://github.com/nostoslabs/gitlab-mcp/issues) •
[Request Feature](https://github.com/nostoslabs/gitlab-mcp/issues) •
[Documentation](docs/)

</div>
