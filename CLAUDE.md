# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains documentation and plans for reimplementing the GitLab MCP (Model Context Protocol) Server in **Python** using **Clean Architecture** principles and the **FastMCP** library.

### Original TypeScript Implementation

The **original TypeScript implementation** is preserved in the `old/` directory as a reference. It's a TypeScript-based server that supports multiple transport modes (stdio, SSE, and Streamable HTTP) and exposes 88 tools for GitLab operations including merge requests, issues, pipelines, wikis, milestones, and more.

**See `old/README.md` for details on referencing the TypeScript code.**

### Python Reimplementation (Current Work)

The goal is to recreate this server in Python with:
- **Clean Architecture** (4 layers: Domain, Application, Infrastructure, Presentation)
- **FastMCP** framework for MCP protocol
- **Test-Driven Development** (TDD) approach
- **uv** package manager
- **Full type safety** with mypy

## Development Commands (Python Implementation)

### Package Management (uv)
- `uv run python -m gitlab_mcp` - Run the server
- `uv run pytest` - Run tests
- `uv run pytest --cov=src` - Run tests with coverage
- `uv add package-name` - Add production dependency
- `uv add --dev package-name` - Add development dependency

### Testing
- `make test` - Run all tests
- `make test-cov` - Run tests with coverage report
- `uv run pytest tests/unit/` - Run unit tests only
- `uv run pytest tests/integration/` - Run integration tests only
- `uv run pytest tests/e2e/` - Run end-to-end tests only

### Code Quality
- `make format` - Format code with black and ruff
- `make lint` - Lint code with ruff
- `make type-check` - Type check with mypy
- `make all` - Run all quality checks and tests

### Old TypeScript Implementation
The original TypeScript code is in `old/` directory:
- `cd old/ && npm run build` - Build TypeScript version
- `cd old/ && npm run dev` - Run TypeScript version
- See `old/README.md` for complete reference

## Architecture (Python Clean Architecture)

The Python implementation follows Clean Architecture with 4 distinct layers:

### Layer Structure
```
Presentation → Application → Domain ← Infrastructure
```

- **Domain Layer** (`src/gitlab_mcp/domain/`) - Pure business logic
  - Entities: Issue, MergeRequest, Pipeline, Project, etc.
  - Value Objects: ProjectId, Pagination, IssueIid
  - No external dependencies

- **Application Layer** (`src/gitlab_mcp/application/`) - Use cases
  - Use Cases: CreateIssue, UpdateIssue, MergeMergeRequest, etc.
  - DTOs: Data transfer objects
  - Interfaces: Repository ports (abstract)

- **Infrastructure Layer** (`src/gitlab_mcp/infrastructure/`) - External services
  - GitLab API client (httpx-based)
  - Repository implementations
  - Configuration (Pydantic settings)
  - Logging

- **Presentation Layer** (`src/gitlab_mcp/presentation/`) - MCP interface
  - FastMCP tools (88 tools)
  - Pydantic schemas for validation
  - Tool handlers (thin wrappers)

### Reference TypeScript Implementation
The original TypeScript code structure (in `old/` directory):
- **old/index.ts** (~5700 lines) - Monolithic implementation with all 88 tools
- **old/schemas.ts** (~2000 lines) - Zod schemas
- **old/customSchemas.ts** - Custom utilities

**See `old/README.md` for how to reference the TypeScript code when implementing Python version.**

### Configuration

Environment variables (same for Python implementation):
- **Required**: `GITLAB_PERSONAL_ACCESS_TOKEN`
- **API**: `GITLAB_API_URL` (defaults to https://gitlab.com/api/v4)
- **Project Control**: `GITLAB_PROJECT_ID`, `GITLAB_ALLOWED_PROJECT_IDS`
- **Security**: `GITLAB_READ_ONLY_MODE`, `GITLAB_DENIED_TOOLS_REGEX`
- **Features**: `USE_GITLAB_WIKI`, `USE_MILESTONE`, `USE_PIPELINE`
- **Transport**: `SSE`, `STREAMABLE_HTTP`, `HOST`, `PORT`
- **Network**: `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`
- **Auth**: `GITLAB_AUTH_COOKIE_PATH`
- **Pagination**: `GITLAB_COMMIT_FILES_PER_PAGE` (default 20)

In Python, these are loaded using Pydantic Settings in `src/gitlab_mcp/infrastructure/config/settings.py`

## Implementation Guide for Python Version

**For AI agents implementing the Python version**, follow these documents in order:

1. **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Read first to understand Clean Architecture
2. **[docs/IMPLEMENTATION_GUIDE.md](docs/IMPLEMENTATION_GUIDE.md)** - Step-by-step task breakdown
3. **[docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** - TDD approach and testing patterns
4. **[docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** - Code templates and commands

### Referencing the TypeScript Code

The original TypeScript implementation in `old/` can be used as a reference:

- **API patterns**: See `old/index.ts` for GitLab API endpoint usage
- **Business logic**: Extract from TypeScript functions and move to use cases
- **Data structures**: Convert Zod schemas in `old/schemas.ts` to Pydantic models
- **Tool implementations**: Reference switch cases in `old/index.ts` (~line 4347)

**See `old/README.md` for detailed guide on using the TypeScript reference.**

### Key Differences from TypeScript Version

| Aspect | TypeScript (old/) | Python (new) |
|--------|------------------|--------------|
| **Architecture** | Monolithic (single file) | Clean Architecture (4 layers) |
| **Validation** | Zod schemas | Pydantic models |
| **HTTP Client** | node-fetch | httpx (async) |
| **Testing** | Integration tests | TDD with unit/integration/e2e |
| **Package Manager** | npm | uv |
| **Structure** | All in index.ts | Separated by layer |

## Important Patterns for Python

### Adding New Tools (Python)

1. **Domain**: Create entity if needed (e.g., `Issue`, `MergeRequest`)
2. **Application**: Create use case (e.g., `CreateIssueUseCase`) with tests
3. **Application**: Create DTOs (input/output data transfer objects)
4. **Infrastructure**: Implement repository method for API call
5. **Presentation**: Create Pydantic schema for tool input
6. **Presentation**: Create MCP tool handler (thin wrapper)
7. Add to tool filtering lists if read-only

### Testing Pattern (Python TDD)

1. Write failing test first
2. Implement minimal code to pass
3. Refactor while keeping tests green
4. Validate coverage meets requirements

See [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md) for details.
