# Slack GPT-Assistant PRD

## Status: Draft

## Intro

This document outlines the requirements for the Minimum Viable Product (MVP) of the Slack GPT-Assistant. The goal is to create a Slack bot that leverages OpenAI's GPT models and a local knowledge base (PDF documents) to answer support team questions directly within Slack, aiming to reduce repetitive work and improve response times. The bot will integrate via a slash command (`/ask`), utilize Redis for caching, and run in a containerized environment.

## Goals and Context

- **Project Objectives**:
    - Develop a Slack bot that answers user questions based on provided PDF documents using OpenAI.
    - Implement caching via Redis to improve response time for frequent questions.
    - Provide a simple setup and deployment process using Docker.
- **Measurable Outcomes**:
    - Reduce time spent by support staff answering repetitive questions.
    - Provide consistent answers based on the knowledge base.
- **Success Criteria (MVP Focus)**:
    - Achieve a target percentage of user questions successfully answered by the bot based on the provided PDF knowledge base (Target TBD, requires baseline measurement).
- **Key Performance Indicators (KPIs)**:
    - Number of `/ask` requests processed.
    - Cache hit ratio (Redis).
    - Count of "answer found" vs. "answer not found" responses.
    - OpenAI API call latency and error rates.
    - Bot response time (acknowledgment and final answer).

## Features and Requirements

**Functional Requirements:**

1.  **Slash Command (`/ask`)**:
    *   The bot MUST respond to the `/ask <question>` slash command in Slack.
    *   The bot MUST immediately acknowledge the command receipt within Slack's 3-second limit.
    *   The bot MUST parse the `<question>` text provided by the user.
    *   If no `<question>` is provided, the bot MUST respond with usage instructions.
    *   The bot MUST search the configured PDF knowledge base for relevant context related to the `<question>`.
    *   The bot MUST check the Redis cache for a similar question before calling the OpenAI API.
    *   If a cached answer exists, the bot MUST return it.
    *   If no cached answer exists, the bot MUST query the OpenAI API (`gpt-4o-mini`) using the `<question>` and potentially relevant context retrieved from PDFs.
    *   The bot MUST cache the question-answer pair in Redis after a successful OpenAI response.
    *   The final answer MUST be sent as an asynchronous message to the channel where the command was invoked.
2.  **Slash Command (`/help`)**:
    *   The bot MUST respond to the `/help` slash command.
    *   The response MUST explain the bot's purpose and how to use the `/ask` command.
3.  **Knowledge Base**:
    *   The bot MUST read PDF documents from a specified local directory (`./data/`).
    *   The bot MUST extract text content from these PDFs to use as context for answering questions.
4.  **Caching**:
    *   The bot MUST use Redis to cache question-answer pairs.
    *   The cache key SHOULD be based on the user's question text (consider normalization).
    *   Cache entries SHOULD have a Time-To-Live (TTL) (e.g., 24 hours).
5.  **Error Handling**:
    *   If the OpenAI API call fails, the bot MUST respond with a user-friendly error message ("Sorry, I'm having trouble connecting to my brain...") and log the technical error.
    *   If Redis is unavailable, the bot SHOULD attempt to function without caching (log the error) or return an error ("Sorry, I'm experiencing technical difficulties...") if Redis is critical for context.
    *   If the bot cannot find a relevant answer in the PDFs or from OpenAI, it MUST respond with a specific message ("I couldn't find a specific answer...").
    *   Malformed `/ask` commands MUST trigger a helpful usage message.
6.  **Analytics (Logging)**:
    *   The bot MUST log the following events (e.g., to console/stdout):
        *   Received `/ask` request (with question hash/ID).
        *   Cache hit/miss.
        *   PDF search performed.
        *   OpenAI API call initiated/completed/failed.
        *   Answer sent (success/failure/not_found).
        *   Redis connection errors.

**Non-Functional Requirements:**

1.  **Performance**:
    *   Slash command acknowledgment MUST occur within 3 seconds.
    *   Final asynchronous response time for uncached requests SHOULD target under 10 seconds.
    *   Cached responses SHOULD target sub-second response times (after acknowledgment).
2.  **Scalability**:
    *   The MVP architecture SHOULD be able to handle approximately 100 concurrent users/requests.
3.  **Security**:
    *   API keys (Slack, OpenAI) and Redis credentials MUST be managed via environment variables (NOT hardcoded).
    *   Redis instance MUST be configured with password authentication.
    *   Basic input sanitization MUST be applied to user questions.
    *   The PDF data directory MUST be considered a secure location within the deployment environment.
4.  **Deployment**:
    *   The application MUST be containerized using Docker.
    *   A `Dockerfile` MUST be provided.
    *   A `README.md` MUST detail build and run instructions.
    *   An `.env.example` file MUST list required environment variables.

**User Experience Requirements:**

1.  **Response Formatting**: All bot responses (answers, help, errors) MUST use Slack Block Kit for improved readability and formatting (e.g., markdown support).
2.  **Clarity**: Error messages and "not found" responses MUST be clear, user-friendly, and avoid technical jargon.

**Integration Requirements:**

1.  Slack API (via Slack Bolt Python SDK).
2.  OpenAI API (via OpenAI Python client).
3.  Redis (via Redis Python client).
4.  PDF Text Extraction library (e.g., `pymupdf`).

**Testing Requirements:**

-   No specific automated testing requirements (unit, integration, E2E) or coverage targets are mandated for the MVP. Manual testing during development is expected.

## Epic Story List

### Epic 0: Initial Manual Set Up & Configuration

-   **Story 0.1: Obtain Credentials**:
    -   User creates a Slack App, configures Slash Commands (`/ask`, `/help`), enables necessary permissions/scopes, and obtains a Bot Token.
    -   User obtains an OpenAI API Key.
    -   User sets up a Redis instance (local or cloud) and obtains connection details (host, port, password).
-   **Story 0.2: Environment Setup**:
    -   User clones the Git repository.
    -   User creates a `.env` file from `.env.example`.
    -   User populates the `.env` file with the credentials obtained in Story 0.1 and specifies the path to the PDF data directory.
-   **Story 0.3: Knowledge Base Population**:
    -   User places relevant PDF documents into the designated data directory (e.g., `./data/company_docs/`).
-   **Story 0.4: Build & Run Container**:
    -   User builds the Docker image using the provided `Dockerfile`.
    -   User runs the Docker container, ensuring the `.env` file is correctly sourced or variables are passed.
-   **Story 0.5: Configure Slack Request URL**:
    -   User configures the Slack App's Request URL for Slash Commands/Events to point to the running container's public endpoint (using ngrok for local testing or the deployment URL).

### Epic 1: Core Bot Functionality

-   **Story 1.1: Project Setup & Basic App**:
    -   Requirements:
        -   Initialize Python project with proposed directory structure (`app/`, `tests/`, etc.).
        *   Set up `requirements.txt` with initial dependencies (Python, Slack Bolt, python-dotenv).
        *   Implement basic Slack Bolt app in `app/main.py` that can start and respond to a health check or simple command.
        *   Initialize Git repository and commit initial structure.
        *   Create basic `Dockerfile` capable of building and running the initial app.
        *   Create `.env.example`.
-   **Story 1.2: Environment & Configuration Loading**:
    -   Requirements:
        *   Implement loading of environment variables (Slack Token, OpenAI Key, Redis details, PDF path) from `.env` file into the application configuration (e.g., using `python-dotenv`).
        *   Ensure API keys are not exposed in logs or code.
-   **Story 1.3: Redis Service & Caching Logic**:
    -   Requirements:
        *   Add `redis` to `requirements.txt`.
        *   Create `app/services/redis_service.py` to handle connection and basic get/set operations.
        *   Implement caching logic (set with TTL, get) to be used by the `/ask` handler.
        *   Include error handling for Redis connection issues.
-   **Story 1.4: OpenAI Service Integration**:
    -   Requirements:
        *   Add `openai` to `requirements.txt`.
        *   Create `app/services/openai_service.py` to handle interaction with the OpenAI API.
        *   Implement function to call `gpt-4o-mini` model with a given prompt (question + context).
        *   Include error handling for OpenAI API failures.
-   **Story 1.5: PDF Knowledge Base Service**:
    -   Requirements:
        *   Add `pymupdf` (or chosen PDF library) to `requirements.txt`.
        *   Create `app/services/knowledge_base.py`.
        *   Implement function to scan the configured data directory for PDF files.
        *   Implement function to extract text content from a given PDF file.
        *   Implement basic search/retrieval logic to find text chunks relevant to a user's question (simple keyword matching or embedding lookup could be future enhancement).
-   **Story 1.6: `/ask` Command Handler**:
    -   Requirements:
        *   Create `app/handlers/ask_command.py` and register the `/ask` command handler in `app/main.py`.
        *   Implement immediate acknowledgment response.
        *   Implement asynchronous task execution for the main logic.
        *   Orchestrate the flow: Parse question -> Search PDFs (via `knowledge_base.py`) -> Check Cache (via `redis_service.py`) -> Call OpenAI if needed (via `openai_service.py`) -> Store in Cache -> Format response with Block Kit -> Send asynchronous response.
        *   Handle malformed command (no question provided).
        *   Integrate error handling for failures in downstream services.
        *   Implement "not found" response logic.
-   **Story 1.7: `/help` Command Handler**:
    -   Requirements:
        *   Create `app/handlers/help_command.py` and register the `/help` command handler.
        *   Implement response explaining bot usage using Block Kit.
-   **Story 1.8: Analytics Logging**:
    -   Requirements:
        *   Integrate logging calls (using Python's built-in `logging`) at key points defined in Functional Requirement #6.
        *   Ensure logs are written to stdout/stderr for easy capture by Docker/deployment platform.

### Epic 2: Deployment & Documentation Refinement

-   **Story 2.1: Dockerfile Optimization**:
    -   Requirements:
        *   Review and optimize `Dockerfile` for smaller image size and build speed (e.g., multi-stage builds, efficient layer caching).
        *   Ensure required ports are exposed.
-   **Story 2.2: README Update**:
    -   Requirements:
        *   Update `README.md` with comprehensive setup, configuration, build, run, and deployment instructions based on the implemented stories.
        *   Include details on required environment variables.

### Epic N: Future Epic Enhancements (Beyond MVP Scope)

-   Trained on company-specific knowledge base (advanced embedding/RAG).
-   Multi-channel support (DMs, channels, threads).
-   Integration with ticketing systems.
-   Conversation memory for follow-up questions.
-   User feedback mechanism (`/feedback` command, buttons on responses).
-   Dedicated analytics dashboard (Web UI).
-   More sophisticated PDF chunking and retrieval strategies.
-   Support for other document types (e.g., .txt, .md, .docx).

## Technology Stack

| Technology           | Version         | Description                                      |
| -------------------- | --------------- | ------------------------------------------------ |
| Python               | 3.11 / 3.12     | Backend language                                 |
| Slack Bolt (Python)  | Latest stable   | Slack App framework                              |
| OpenAI (Python)      | Latest stable   | OpenAI API client library                        |
| Redis (Python)       | Latest stable   | Redis client library                             |
| PyMuPDF              | Latest stable   | PDF text extraction library                      |
| Docker               | Latest stable   | Containerization                                 |
| Redis                | 6.x / 7.x       | In-memory cache                                  |
| OpenAI API           | `gpt-4o-mini`   | AI Model for question answering                  |
| python-dotenv        | Latest stable   | Environment variable loading                     |

## Project Structure

```
slack-gpt-assistant/
├── app/                   # Main application source code
│   ├── __init__.py
│   ├── handlers/          # Slack event/command handlers
│   │   ├── __init__.py
│   │   └── ask_command.py
│   │   └── help_command.py
│   ├── services/          # External service interactions
│   │   ├── __init__.py
│   │   ├── knowledge_base.py # PDF searching logic
│   │   ├── openai_service.py
│   │   └── redis_service.py
│   ├── utils/             # Utility functions (e.g., formatting, config)
│   │   └── __init__.py
│   └── main.py            # Application entry point (Bolt app setup)
├── data/                  # Folder for knowledge base PDFs (mounted/configured)
│   └── company_docs/      # Example sub-folder (gitignored or mounted)
├── tests/                 # Unit/Integration tests (Post-MVP?)
│   └── __init__.py
├── .env.example           # Example environment variables
├── .gitignore
├── Dockerfile             # Container definition
├── requirements.txt       # Python dependencies
└── README.md              # Project overview and setup instructions
```

## POST MVP / PRD Features

-   Trained on company-specific knowledge base (advanced RAG)
-   Multi-channel support
-   Ticketing system integration
-   Conversation memory
-   User feedback mechanism
-   Analytics dashboard
-   Advanced PDF/Document processing

## Change Log

| Change        | Story ID | Description     |
| ------------- | -------- | --------------- |
| Initial draft | N/A      | Initial draft PRD | 