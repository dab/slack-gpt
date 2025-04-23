# Slack GPT-Assistant - Architecture Document

**Version:** 1.0
**Date:** 2024-07-26
**Status:** Final

## 1. Introduction

This document outlines the architecture for the Slack GPT-Assistant, a Python-based Slack bot designed to answer user questions by leveraging OpenAI's GPT models and a local PDF knowledge base. It is based on the requirements detailed in the `Slack GPT-Assistant PRD (Draft)`.

The primary goal of this architecture is to create a Minimum Viable Product (MVP) that is functional, relatively easy to deploy via Docker, and provides a foundation for future enhancements.

**Note:** This architecture is based on the current understanding of the PRD. Findings during implementation, particularly related to specific library interactions or performance characteristics under load, may necessitate minor refinements to the PRD and consequently, updates to this Architecture Document to maintain alignment.

## 2. Architectural Goals and Constraints

### Goals (Derived from PRD NFRs & Features)

*   **Responsiveness:** Acknowledge Slack commands within 3 seconds; provide final answers within 10 seconds (uncached) or sub-second (cached).
*   **Accuracy:** Provide relevant answers based on the configured PDF knowledge base and `gpt-4o-mini`.
*   **Reliability:** Handle errors gracefully (OpenAI API, Redis, PDF processing) and provide informative feedback to the user.
*   **Scalability (MVP):** Support approximately 100 concurrent users/requests within a single container instance.
*   **Security:** Protect API keys and credentials; apply basic input sanitization.
*   **Deployability:** Provide simple containerized deployment using Docker.
*   **Maintainability:** Ensure code quality and structure allow for future enhancements.
*   **User Experience:** Use Slack Block Kit for clear and readable responses.

### Constraints

*   **Technology Stack:** Must use Python, Slack Bolt, OpenAI API (`gpt-4o-mini`), Redis, PyMuPDF, and Docker as specified in the PRD.
*   **MVP Scope:** Focus on core `/ask` and `/help` functionality, PDF-based knowledge, and Redis caching. Advanced features (RAG, conversation memory, etc.) are explicitly out of scope for MVP.
*   **Testing (MVP):** While the PRD doesn't mandate automated tests, this architecture includes minimal unit testing requirements for core components to ensure robustness (see Section 8).
*   **Deployment Environment:** Assumed to be a standard container runtime environment capable of running Docker containers and connecting to external services (Slack, OpenAI, Redis).

## 3. Architectural Representation / Views

### 3.1. High-Level Overview

*   **Architectural Style:** **Monolith.** A single, containerized Python application handling all responsibilities (Slack interaction, PDF processing, caching, OpenAI interaction).
*   **Justification:** Suitable for the defined MVP scope. Reduces deployment complexity compared to microservices or serverless, allowing faster initial development. Sufficient for the target scale (~100 concurrent users) with asynchronous processing.

```mermaid
graph TD
    A[User via Slack Client] -- Sends /ask command --> B(Slack API);
    B -- Forwards Command --> C{Slack GPT-Assistant (Docker Container)};
    C -- Reads/Writes Cache --> D[(Redis)];
    C -- Extracts Text --> E[/data/ PDFs];
    C -- Sends Prompt --> F(OpenAI API - gpt-4o-mini);
    F -- Returns Completion --> C;
    C -- Sends Async Response --> B;
    B -- Displays Response --> A;

    style C fill:#lightblue,stroke:#333,stroke-width:2px
    style D fill:#f9f,stroke:#333,stroke-width:2px
    style F fill:#ccf,stroke:#333,stroke-width:2px
```
*Diagram: C4 Context Diagram (Simplified)*

### 3.2. Component View

The monolithic application is internally structured into logical components:

*   **`Slack Handler (main.py, handlers/)`**:
    *   Responsibilities: Receives incoming Slack events/commands (via Bolt), performs immediate `ack()`, validates input, dispatches requests to `Core Application Logic`, formats responses using Block Kit, sends asynchronous responses via `respond`/`say`.
    *   Interactions: Receives data from Slack API, delegates processing to `Core Application Logic`, sends responses back via Slack API.
*   **`Core Application Logic (handlers/ask_command.py)`**:
    *   Responsibilities: Orchestrates the `/ask` command flow: normalize question, check cache via `Redis Service`, if miss -> search PDFs via `Knowledge Base Service`, call `OpenAI Service`, update cache via `Redis Service`. Handles core error logic and "not found" scenarios.
    *   Interactions: Uses `Redis Service`, `Knowledge Base Service`, `OpenAI Service`.
*   **`Redis Service (services/redis_service.py)`**:
    *   Responsibilities: Manages connection pooling to Redis, handles cache GET/SET operations (with TTL), normalizes cache keys.
    *   Interactions: Connects to Redis instance. Called by `Core Application Logic`.
*   **`OpenAI Service (services/openai_service.py)`**:
    *   Responsibilities: Manages interaction with the OpenAI API, formats prompts (question + context), handles API calls and responses, implements basic error handling/retries.
    *   Interactions: Connects to OpenAI API. Called by `Core Application Logic`.
*   **`Knowledge Base Service (services/knowledge_base.py)`**:
    *   Responsibilities: Scans the configured directory for PDFs, extracts text using `PyMuPDF`, chunks text, performs keyword-based search on chunks to find relevant context for a given question. Handles PDF processing errors.
    *   Interactions: Reads files from the local filesystem (`/data`). Called by `Core Application Logic`.
*   **`Configuration/Utils (utils/, .env)`**:
    *   Responsibilities: Loads environment variables, provides utility functions (e.g., normalization, logging setup).
    *   Interactions: Used by various components.

```mermaid
graph TD
    subgraph Container [Slack GPT-Assistant]
        direction LR
        A[Slack Handler] --> B{Core Application Logic};
        B --> C[Redis Service];
        B --> D[OpenAI Service];
        B --> E[Knowledge Base Service];
        A --> F[Config/Utils];
        B --> F;
        C --> F;
        D --> F;
        E --> F;
    end

    G[User via Slack] --> A;
    A --> G;
    C --> H[(Redis)];
    D --> I(OpenAI API);
    E --> J[/data/ PDFs];

    style Container fill:#lightgrey,stroke:#333,stroke-width:2px
```
*Diagram: C4 Component Diagram (Simplified)*

### 3.3. Data View

*   **Primary Data Store:** Redis (Version 6.x / 7.x) used exclusively for caching.
*   **Data Model:** Key-value pairs.
    *   Key: SHA-256 hash of the normalized user question (lowercase, punctuation removed, whitespace collapsed).
    *   Value: JSON string containing the answer generated by OpenAI.
    *   TTL: Configurable (e.g., 24 hours, managed via Redis `SETEX` or `SET` + `EXPIRE`).
*   **Data Access:** Performed exclusively through the `Redis Service` component using the `redis-py` client library with connection pooling.
*   **Knowledge Base:** Unstructured text data extracted from PDF files stored on the local filesystem within the container (mounted from host or volume). Data is processed on-demand by the `Knowledge Base Service`.

```mermaid
erDiagram
    CACHE {
        string key PK "Normalized Question Hash (SHA-256)"
        json value "Stored Answer (JSON String)"
        datetime ttl "Managed by Redis TTL"
    }
    KNOWLEDGE_BASE {
        string file_path PK "Path to PDF file in /data"
        string extracted_text "Full text content"
        string[] text_chunks "Processed text segments"
    }

    CACHE ||--o{ KNOWLEDGE_BASE : "Answer derived from"
    note on KNOWLEDGE_BASE { "Data stored on filesystem, not in Redis." }
    note on CACHE { "Represents data in Redis." }
```
*Diagram: Conceptual Data Model (Redis Cache & Filesystem Knowledge Base)*

### 3.4. Deployment View

*   **Target Environment:** Docker container runtime.
*   **Artifacts:** A Docker image built using the provided `Dockerfile`.
*   **Configuration:** Environment variables (Slack tokens, OpenAI key, Redis connection details, PDF path) passed to the container at runtime (e.g., via `.env` file mount or orchestration platform).
*   **Knowledge Base Data:** The `/data` directory containing PDFs must be mounted into the container as a volume.
*   **Networking:** The container must expose a port (e.g., 3000, configurable) for Slack to send requests to. For local development/testing, a tool like `ngrok` is required to expose the local port publicly. The container must have outbound network access to Slack API, OpenAI API, and the Redis instance.
*   **CI/CD:** Out of scope for MVP. Future enhancement could involve building/testing/pushing the Docker image via GitHub Actions or similar.

## 4. Initial Project Setup (Manual Steps - Story 0)

These steps must be performed manually by the user before running the application:

1.  **Obtain Slack Credentials:**
    *   Create a Slack App ([https://api.slack.com/apps](https://api.slack.com/apps)).
    *   Configure Slash Commands (`/ask`, `/help`) under "Features" -> "Slash Commands".
    *   Enable required permissions/scopes (e.g., `commands`, `chat:write`).
    *   Install the app to the workspace and obtain the Bot User OAuth Token (`SLACK_BOT_TOKEN`) and App-Level Token (`SLACK_APP_TOKEN` - if using Socket Mode, though HTTP mode is assumed here).
    *   Obtain the Signing Secret (`SLACK_SIGNING_SECRET`) from "Basic Information".
2.  **Obtain OpenAI API Key:**
    *   Create an OpenAI account and obtain an API key (`OPENAI_API_KEY`).
3.  **Setup Redis Instance:**
    *   Provision a Redis instance (e.g., local Docker container, cloud service like Redis Cloud or AWS ElastiCache).
    *   Obtain connection details: Host (`REDIS_HOST`), Port (`REDIS_PORT`), Password (`REDIS_PASSWORD`). Ensure password authentication is enabled.
4.  **Clone Repository & Setup Environment File:**
    *   Clone the project Git repository.
    *   Copy `.env.example` to `.env`.
    *   Populate `.env` with the credentials obtained above (`SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, `OPENAI_API_KEY`, `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`).
    *   Set `PDF_DATA_DIR` in `.env` to the path *relative to the project root* where PDF documents will be placed (e.g., `./data/company_docs/`).
5.  **Populate Knowledge Base:**
    *   Create the directory specified by `PDF_DATA_DIR`.
    *   Place relevant PDF documents into this directory.
6.  **Build & Run Docker Container:**
    *   Build the Docker image: `docker build -t slack-gpt-assistant .`
    *   Run the container, ensuring environment variables are passed and the data directory is mounted:
        ```bash
        docker run -p 3000:3000 --env-file .env -v $(pwd)/data:/app/data --name slack-bot slack-gpt-assistant
        ```
        *(Adjust volume mount source path (`$(pwd)/data`) if PDFs are not in `./data` relative to project root)*
7.  **Configure Slack Request URL:**
    *   If running locally, start `ngrok`: `ngrok http 3000`. Note the public HTTPS URL.
    *   In the Slack App configuration ("Features" -> "Slash Commands"), set the Request URL for both `/ask` and `/help` to the public endpoint (e.g., `https://<your-ngrok-subdomain>.ngrok.io/slack/events`). If deploying, use the deployment URL + `/slack/events`.
    *   Similarly, configure the Request URL under "Event Subscriptions" if needed for other features later (though only commands are used for MVP).

**Justification for Manual Steps:** Credential generation requires user accounts and actions on external platforms. Configuration is environment-specific. Initial knowledge base population is user-dependent.

## 5. Technology Stack (Opinionated & Specific)

| Category             | Technology           | Version          | Notes                                        |
| -------------------- | -------------------- | ---------------- | -------------------------------------------- |
| Language             | Python               | `3.11.x`         | Specified in PRD. Use latest 3.11 patch.    |
| Web Framework        | Slack Bolt (Python)  | `~1.18.x`        | Latest stable 1.x version. Handles Slack API. |
| AI Client            | OpenAI (Python)      | `~1.x`           | Latest stable 1.x version.                   |
| Cache Client         | Redis (Python)       | `~5.0.x`         | Latest stable 5.x version.                   |
| PDF Processing       | PyMuPDF              | `~1.24.x`        | Latest stable. For text extraction.          |
| Env Variables        | python-dotenv        | `~1.0.x`         | Loading `.env` files.                        |
| Containerization     | Docker               | `Latest stable`  | As specified in PRD.                         |
| ASGI Server          | Uvicorn              | `~0.29.x`        | Production-grade server for Bolt app.        |
| **Infrastructure**   |                      |                  |                                              |
| Cache                | Redis                | `6.2+` / `7.x`   | In-memory cache store. Requires auth.      |
| AI Model             | OpenAI API           | `gpt-4o-mini`    | Specified model for Q&A.                     |
| **Development Tools**|                      |                  |                                              |
| Formatter            | black                | `~24.x`          | Code formatting.                             |
| Import Sorter        | isort                | `~5.13.x`        | Import sorting.                              |
| Linter               | flake8               | `~7.x`           | Code linting (style & errors).             |
| Type Checker         | mypy                 | `~1.9.x`         | Static type checking.                        |
| Testing Framework    | pytest               | `~8.x`           | Unit testing.                                |
| Async Test Support   | pytest-asyncio       | `~0.23.x`        | Testing async code with pytest.              |
| Mocking              | pytest-mock / unittest.mock | N/A      | Built-in or via pytest plugin.               |

*(Note: Specific patch versions denoted by `.x` should use the latest available stable patch at the time of development start. Ranges `~X.Y` allow compatible updates within that major/minor version series according to semantic versioning).*

## 6. Patterns and Standards (Opinionated & Specific)

*   **Architectural/Design Patterns:**
    *   **Service Layer:** External interactions (Redis, OpenAI, PDF Filesystem) are encapsulated in dedicated service classes (`RedisService`, `OpenAIService`, `KnowledgeBaseService`) within `app/services/`.
    *   **Asynchronous Task Processing:** Slack Bolt's built-in `asyncio` support will be used. Long-running tasks in command handlers (`/ask`) must be performed *after* calling `await ack()` and should utilize `await` for I/O-bound operations (Redis, OpenAI calls). Potentially CPU-bound PDF processing within `KnowledgeBaseService` should use `asyncio.to_thread` or `loop.run_in_executor` if performance testing indicates blocking issues.
    *   **Configuration Management:** Load configuration (API keys, Redis details, paths) from environment variables using `python-dotenv`. Centralize access if needed, but direct `os.getenv` within services is acceptable for MVP.
*   **API Design Standards:**
    *   **Style:** Interaction driven by Slack Slash Commands (`/ask`, `/help`) processed by Slack Bolt.
    *   **Data Format:** Input via Slack command payload (form-encoded). Output via Slack Block Kit (JSON) sent asynchronously using `respond()` or `say()`.
    *   **Authentication:** Slack request verification using the `SLACK_SIGNING_SECRET` handled automatically by Bolt.
*   **Coding Standards:**
    *   **Style Guide:** PEP 8 mandatory.
    *   **Formatter:** `black` mandatory (configured in `pyproject.toml`). Run automatically (e.g., pre-commit hook).
    *   **Linter:** `flake8` mandatory (configured in `pyproject.toml`). Check for errors and style issues. Plugins like `flake8-bugbear` recommended.
    *   **Import Sorting:** `isort` mandatory (configured in `pyproject.toml`). Run automatically.
    *   **Type Checking:** `mypy` mandatory (configured in `pyproject.toml`). Aim for type hints on all function signatures.
    *   **Naming Conventions:**
        *   Files: `snake_case.py` (e.g., `redis_service.py`, `ask_command.py`).
        *   Variables/Functions: `snake_case`.
        *   Classes: `PascalCase` (e.g., `RedisService`).
        *   Constants: `UPPER_SNAKE_CASE`.
    *   **Docstrings:** Google Style mandatory for all public modules, classes, functions, and methods. Explain purpose, args, returns, and any raised exceptions.
    *   **Test Files:** Place unit tests in `tests/` mirroring the `app/` structure, or adjacent (`_test.py`) if preferred (choose one convention). Structure: `tests/services/test_redis_service.py`.
*   **Error Handling Strategy:**
    *   Use Python's standard `try...except` blocks.
    *   Log detailed technical errors (including tracebacks) using the standard `logging` module configured to output to stdout/stderr.
    *   Catch specific exceptions where possible.
    *   In command handlers, catch exceptions from service calls and respond to the user with pre-defined, user-friendly error messages using Block Kit (as specified in PRD FR#5). Avoid exposing technical details to the user.
    *   For critical failures preventing core functionality (e.g., initial Redis connection failed and caching is deemed essential), the application may need to log the error and exit or respond with a general failure message.

## 7. Folder Structure

The project will adhere to the following directory structure, as proposed in the PRD:

```
slack-gpt-assistant/
├── app/                   # Main application source code
│   ├── __init__.py
│   ├── handlers/          # Slack event/command handlers
│   │   ├── __init__.py
│   │   └── ask_command.py
│   │   └── help_command.py
│   ├── services/          # External service interactions & business logic
│   │   ├── __init__.py
│   │   ├── knowledge_base.py # PDF searching/extraction logic
│   │   ├── openai_service.py
│   │   └── redis_service.py
│   ├── utils/             # Utility functions (e.g., formatting, config, logging setup)
│   │   └── __init__.py
│   └── main.py            # Application entry point (Bolt app setup, ASGI integration)
├── data/                  # Folder for knowledge base PDFs (mounted/configured, gitignored)
│   └── company_docs/      # Example sub-folder
├── tests/                 # Unit/Integration tests
│   ├── __init__.py
│   ├── handlers/
│   │   └── __init__.py
│   │   └── test_ask_command.py # Example test file
│   └── services/
│       └── __init__.py
│       └── test_redis_service.py # Example test file
├── .env.example           # Example environment variables
├── .gitignore
├── Dockerfile             # Container definition
├── requirements.txt       # Python production dependencies
├── requirements-dev.txt   # Python development/testing dependencies (pytest, black, flake8, etc.)
├── pyproject.toml         # Tool configuration (black, isort, flake8, mypy, pytest)
└── README.md              # Project overview and setup instructions
```
*(Added `requirements-dev.txt` and `pyproject.toml`)*

## 8. Testing Strategy (Opinionated & Specific)

Acknowledging the PRD's flexibility for MVP, this architecture mandates minimal unit testing for core stability and maintainability.

*   **Required Test Types (MVP):**
    *   **Unit Tests:** Mandatory for core service logic (`services/`) and complex utility functions (`utils/`). Focus on testing business logic, data transformations, and edge cases.
*   **Frameworks/Libraries:**
    *   `pytest` (`~8.x`)
    *   `pytest-asyncio` (`~0.23.x`) for testing `async` functions.
    *   `pytest-mock` or built-in `unittest.mock` for isolating components and mocking external dependencies (Slack API, OpenAI API, Redis calls, filesystem access).
*   **Code Coverage Requirement (MVP):**
    *   Target **>= 70%** line coverage for modules within `app/services/`.
    *   This requirement is enforced manually or via local tooling for MVP. CI enforcement is recommended post-MVP.
*   **Testing Standards:**
    *   **Pattern:** Use the Arrange-Act-Assert (AAA) pattern for structuring unit tests.
    *   **Isolation:** Unit tests MUST mock external dependencies (network calls, filesystem, database) to test components in isolation.
    *   **Test Location:** Store test files in the `tests/` directory, mirroring the `app/` structure (e.g., `tests/services/test_redis_service.py` tests `app/services/redis_service.py`).
    *   **Naming:** Test files prefixed with `test_`. Test functions prefixed with `test_`. Test classes prefixed with `Test`.

## 9. Core AI Agent Rules (for `ai/rules.md`)

1.  Adhere strictly to PEP 8 guidelines, using `black` for formatting and `isort` for imports (configs in `pyproject.toml`). Validate with `flake8`.
2.  Add Google Style docstrings to all new public functions, methods, and classes, explaining purpose, args (`Args:`), returns (`Returns:`), and potential errors (`Raises:`).
3.  Implement type hints for all function signatures and check using `mypy` (config in `pyproject.toml`).
4.  Place unit tests (`test_*.py`) in the `tests/` directory mirroring the `app/` structure. Use `pytest` and mock external dependencies (Redis, OpenAI, Slack API, filesystem). Aim for >70% coverage on service modules.
5.  Handle errors gracefully: Log technical details using the `logging` module; return user-friendly Block Kit messages for Slack command failures. Do not expose implementation details in user-facing errors.
6.  Use `async`/`await` for all I/O operations (Slack Bolt calls, Redis, OpenAI). Offload potentially blocking CPU-bound code (like complex PDF processing) using `asyncio.to_thread` if necessary. Call `await ack()` immediately in command handlers.
7.  Read configuration (API keys, Redis details, paths) strictly from environment variables via `os.getenv()`. Do not hardcode secrets.

## 10. Security Considerations

*   **Credentials Management:** All sensitive keys (Slack Bot Token, Slack Signing Secret, OpenAI API Key) and connection details (Redis Password, Host, Port) MUST be loaded exclusively from environment variables. An `.env.example` file will list required variables, but the `.env` file itself MUST be included in `.gitignore`.
*   **Slack Request Verification:** Slack Bolt automatically handles request signature verification using the `SLACK_SIGNING_SECRET` to ensure requests originate from Slack. This MUST NOT be disabled.
*   **Redis Security:** The Redis instance MUST be configured to require password authentication (`requirepass` in Redis config). The `REDIS_PASSWORD` environment variable MUST be set. Avoid exposing Redis to the public internet if possible; use private networking or VPCs if deployed in the cloud.
*   **Input Sanitization:** Basic sanitization should be applied to the `<question>` text from the `/ask` command before using it in logs, cache keys (normalization helps here), or potentially complex PDF search logic. For MVP, this primarily involves stripping excessive whitespace. Avoid constructing shell commands or database queries directly from user input. Block Kit helps mitigate injection risks in responses.
*   **PDF Data Security:** The `/data` directory containing PDFs is assumed to be within the secure context of the Docker container or mounted from a secure host location. Access controls on the host/volume are outside the application's direct control but are important. The application itself does not expose PDF content directly via any API.
*   **Dependency Security:** Regularly update dependencies (`requirements.txt`, `requirements-dev.txt`) and consider using tools like `pip-audit` or GitHub Dependabot to check for known vulnerabilities (Post-MVP activity).
*   **Rate Limiting:** While Slack handles command rate limiting, consider application-level rate limiting if abuse becomes an issue (Post-MVP). Be mindful of OpenAI API rate limits and implement retries with backoff (`OpenAI Service`).

## 11. Architectural Decisions (ADRs)

*   **ADR-001: Architectural Style - Monolith**
    *   **Context:** Need to build an MVP Slack bot with core features (command handling, PDF search, caching, OpenAI query). Target scale is moderate (~100 concurrent users). Team size is small/AI-driven.
    *   **Decision:** Adopt a monolithic architecture within a single Docker container.
    *   **Rationale:** Simplifies development, deployment, and infrastructure management for the MVP scope. Bolt framework naturally fits this model. Sufficient for target scale with async processing. Microservices would add unnecessary complexity at this stage.
*   **ADR-002: PDF Text Extraction Library - PyMuPDF**
    *   **Context:** Need to extract text content from PDF files reliably and efficiently for the knowledge base. PRD mentioned `PyMuPDF`. Deep research compared `PyMuPDF`, `pypdf`, `pdfminer.six`.
    *   **Decision:** Use `PyMuPDF`.
    *   **Rationale:** Research indicates `PyMuPDF` offers a good balance of performance (speed), accuracy, and robustness compared to alternatives, aligning with PRD suggestion and research findings.
*   **ADR-003: Asynchronous Task Handling - Slack Bolt + asyncio**
    *   **Context:** Slack commands require acknowledgment within 3 seconds, while core logic (PDF search, OpenAI call) takes longer. Need an async mechanism.
    *   **Decision:** Utilize Slack Bolt's native integration with Python's `asyncio`. Call `await ack()` immediately, then perform long-running tasks using `await` for I/O or `asyncio.to_thread` for CPU-bound work if needed.
    *   **Rationale:** Leverages built-in framework capabilities, avoiding the need for external task queues (like Celery) for MVP complexity. Matches common Bolt patterns identified in research.
*   **ADR-004: Caching Strategy - Normalized Key Hash + Redis TTL**
    *   **Context:** Need to cache OpenAI responses for frequently asked questions to reduce latency and cost. Cache keys need to handle minor variations in question phrasing.
    *   **Decision:** Normalize the question text (lowercase, remove punctuation, collapse whitespace), hash the result (SHA-256) for the Redis key, and store the OpenAI answer with a configurable TTL (e.g., 24 hours).
    *   **Rationale:** Simple, effective strategy for MVP. Normalization provides some resilience to minor phrasing differences. Hashing provides a consistent key format. TTL ensures cache freshness. Semantic caching via embeddings deemed too complex for MVP (as per research).
*   **ADR-005: Code Quality Tooling - black, isort, flake8, mypy**
    *   **Context:** Need to ensure consistent code quality, style, and type safety for maintainability, especially in an AI-assisted development workflow.
    *   **Decision:** Mandate the use of `black` (formatter), `isort` (imports), `flake8` (linter), and `mypy` (type checker), configured via `pyproject.toml`.
    *   **Rationale:** These tools represent current Python best practices identified in research. Enforcing them improves code consistency, reduces trivial errors, and aids collaboration/AI agent interaction.

## 12. Glossary

*   **ADR:** Architectural Decision Record. A document capturing an important architectural decision, its context, and consequences.
*   **ASGI:** Asynchronous Server Gateway Interface. A standard interface between async-capable Python web servers, frameworks, and applications.
*   **Block Kit:** Slack's UI framework for creating rich and interactive messages.
*   **Bolt (Slack Bolt):** Slack's official Python framework for building Slack apps.
*   **Cache Key Normalization:** The process of transforming a raw user question into a standardized format (e.g., lowercase, no punctuation) before using it as (or hashing it into) a cache key.
*   **MVP:** Minimum Viable Product. The version of a new product which allows a team to collect the maximum amount of validated learning about customers with the least effort.
*   **PRD:** Product Requirements Document. Document outlining the features, requirements, and goals of a product.
*   **PyMuPDF:** Python binding for the MuPDF library, used for PDF processing.
*   **RAG:** Retrieval-Augmented Generation. An AI technique combining information retrieval (like searching documents) with text generation models.
*   **TTL:** Time-To-Live. A mechanism that limits the lifespan of data in a cache or network.
*   **Uvicorn:** A lightning-fast ASGI server implementation, using uvloop and httptools.
