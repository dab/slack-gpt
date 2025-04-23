# Slack GPT-Assistant - MVP Epic & User Story Backlog
_Generated on: 2025-04-23_

This backlog represents the Minimum Viable Product (MVP) features, sequenced logically based on dependencies identified in the PRD and Architecture Document.

---

### Epic 0: Initial Environment & Manual Setup

**Goal:** Prepare the necessary external accounts, local environment, and initial configurations required before development can begin or the application can be run for the first time. (Corresponds to Arch Doc Section 4 & PRD Story 0)

*   **Story 0.1: Obtain External Credentials**
    *   As a Project Setup User, I need to create a Slack App, configure `/ask` and `/help` slash commands, set permissions, and obtain the Bot Token and Signing Secret so that the application can interact with Slack securely.
    *   As a Project Setup User, I need to create an OpenAI account and obtain an API key so that the application can query the AI model.
    *   As a Project Setup User, I need to provision a Redis instance (e.g., local Docker, cloud) and obtain its connection details (Host, Port, Password) so that the application can use it for caching.
*   **Story 0.2: Set Up Local Repository & Environment File**
    *   As a Project Setup User, I need to clone the project's Git repository so that I have the initial codebase.
    *   As a Project Setup User, I need to copy `.env.example` to `.env` and populate it with the credentials obtained in Story 0.1 (Slack, OpenAI, Redis) and define the `PDF_DATA_DIR` path so that the application can access necessary configurations and secrets at runtime.
*   **Story 0.3: Populate Knowledge Base Directory**
    *   As a Project Setup User, I need to create the directory specified by `PDF_DATA_DIR` in the `.env` file and place the relevant PDF documents into it so that the application has a knowledge base to query.
*   **Story 0.4: Verify Initial Docker Build & Run Capability**
    *   As a Project Setup User, I need to be able to build the initial Docker image using `docker build` and run a basic container (even if it does little initially) sourcing the `.env` file and mounting the data directory so that the basic containerization setup is verified. (Depends on Story 1.1 providing the initial Dockerfile)
*   **Story 0.5: Configure Slack Request URL**
    *   As a Project Setup User, I need to configure the Slack App's Request URL for Slash Commands to point to the application's public endpoint (using `ngrok` for local testing or the deployment URL) so that Slack can send commands to the running application.

---

### Epic 1: Project Foundation & Configuration

**Goal:** Establish the basic project structure, core dependencies, configuration loading mechanism, and initial application scaffolding.

*   **Story 1.1: Initialize Project Structure & Basic Bolt App**
    *   As a Developer, I want the standard project directory structure (`app/`, `tests/`, etc.) created so that code is organized logically.
    *   As a Developer, I want an initial `requirements.txt` (with `slack-bolt`, `python-dotenv`, `uvicorn`) and `requirements-dev.txt` (with `pytest`, `black`, `isort`, `flake8`, `mypy`) set up so that dependencies are managed.
    *   As a Developer, I want a basic `app/main.py` with a Slack Bolt app instance initialized so that the application has an entry point.
    *   As a Developer, I want an initial `Dockerfile` created that can build an image and run the basic Bolt app using `uvicorn` so that containerization is possible from the start.
    *   As a Developer, I want an `.env.example` file created listing all required environment variables (`SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, `OPENAI_API_KEY`, `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `PDF_DATA_DIR`) so that users know what configuration is needed.
    *   As a Developer, I want tool configurations (`black`, `isort`, `flake8`, `mypy`, `pytest`) added to `pyproject.toml` so that code quality standards are defined.
*   **Story 1.2: Implement Configuration Loading**
    *   As a Developer, I want the application to load configuration values (Slack tokens, OpenAI key, Redis details, PDF path) securely from environment variables (using `python-dotenv` for local `.env` loading) so that secrets are not hardcoded and configuration is flexible.
*   **Story 1.3: Implement Basic Logging Setup**
    *   As a Developer, I want a basic logging configuration (using Python's `logging` module) set up in `app/utils/` or `app/main.py` to output formatted logs to stdout/stderr so that application events can be monitored, especially within Docker.

---

### Epic 2: Core Service Implementation

**Goal:** Implement the backend services responsible for interacting with external systems (Redis, OpenAI) and processing the knowledge base (PDFs).

*   **Story 2.1: Implement Redis Service**
    *   As a Developer, I want to create `app/services/redis_service.py` with a `RedisService` class that handles connecting to the Redis instance specified in the configuration.
    *   As a Developer, I want the `RedisService` to provide methods for setting a value with a TTL (`setex`) and getting a value (`get`) based on a provided key.
    *   As a Developer, I want the `RedisService` to handle potential connection errors gracefully (e.g., log errors) so that the application can potentially continue or report issues clearly.
    *   As a Developer, I want to add `redis` to `requirements.txt`.
    *   As a Developer, I want to add basic unit tests (`tests/services/test_redis_service.py`) for the `RedisService` methods, mocking the actual Redis connection.
*   **Story 2.2: Implement OpenAI Service**
    *   As a Developer, I want to create `app/services/openai_service.py` with an `OpenAIService` class that initializes the OpenAI client using the API key from the configuration.
    *   As a Developer, I want the `OpenAIService` to provide an asynchronous method (`get_answer`) that takes a user question and relevant context string, formats a prompt for `gpt-4o-mini`, calls the API, and returns the generated answer.
    *   As a Developer, I want the `OpenAIService` to implement basic error handling for OpenAI API calls (e.g., log errors, return a specific error indicator) so that failures can be managed by the calling handler.
    *   As a Developer, I want to add `openai` to `requirements.txt`.
    *   As a Developer, I want to add basic unit tests (`tests/services/test_openai_service.py`) for the `OpenAIService`, mocking the OpenAI API call.
*   **Story 2.3: Implement Knowledge Base Service (PDF Processing)**
    *   As a Developer, I want to create `app/services/knowledge_base.py` with a `KnowledgeBaseService` class.
    *   As a Developer, I want the `KnowledgeBaseService` to be able to scan the directory specified by `PDF_DATA_DIR` and identify PDF files.
    *   As a Developer, I want the `KnowledgeBaseService` to implement a method (`extract_text_from_pdf`) to extract plain text content from a given PDF file using `PyMuPDF`.
    *   As a Developer, I want the `KnowledgeBaseService` to implement a basic asynchronous method (`find_relevant_context`) that takes a user question, extracts text from all PDFs (potentially caching extracted text in memory for the app's lifetime), and performs a simple keyword search (or similar basic MVP approach) to find text chunks relevant to the question, returning a consolidated context string.
    *   As a Developer, I want the `KnowledgeBaseService` to handle errors during file access or PDF processing gracefully (e.g., log errors, skip problematic files).
    *   As a Developer, I want to add `PyMuPDF` to `requirements.txt`.
    *   As a Developer, I want to add basic unit tests (`tests/services/test_knowledge_base.py`) for the service, mocking filesystem access and `PyMuPDF` calls.

---

### Epic 3: Slack Command Implementation & Integration

**Goal:** Implement the user-facing Slack slash commands (`/ask`, `/help`), integrating the core services, handling user interaction flows, and providing formatted responses.

*   **Story 3.1: Implement `/help` Command Handler**
    *   As a Developer, I want to create `app/handlers/help_command.py` and register a handler function for the `/help` slash command in `app/main.py`.
    *   As a Developer, I want the `/help` handler to respond synchronously with a clear message (using Slack Block Kit) explaining the bot's purpose and how to use the `/ask` command.
*   **Story 3.2: Implement `/ask` Command Handler - Core Flow & Orchestration**
    *   As a Developer, I want to create `app/handlers/ask_command.py` and register an asynchronous handler function for the `/ask` command in `app/main.py`.
    *   As a Developer, I want the `/ask` handler to immediately call `await ack()` to meet Slack's 3-second requirement.
    *   As a Developer, I want the handler to parse the `<question>` text from the command payload. If no question is provided, it should respond asynchronously with usage instructions (using Block Kit).
    *   As a Developer, I want the handler to normalize the question text (e.g., lowercase, remove punctuation) and generate a cache key (e.g., SHA-256 hash as per Arch Doc).
    *   As a Developer, I want the handler to call the `RedisService` to check if a cached answer exists for the key. If yes, format it using Block Kit and send it as an asynchronous response.
    *   As a Developer, if there's a cache miss, I want the handler to call the `KnowledgeBaseService` (`find_relevant_context`) to get context relevant to the raw question.
    *   As a Developer, if there's a cache miss, I want the handler to call the `OpenAIService` (`get_answer`) with the question and retrieved context.
    *   As a Developer, upon receiving a successful answer from OpenAI, I want the handler to call the `RedisService` to cache the answer using the normalized key and a configured TTL (e.g., 24 hours).
    *   As a Developer, I want the handler to format the final answer (from cache or OpenAI) using Block Kit and send it as an asynchronous response to the user/channel.
*   **Story 3.3: Implement `/ask` Command Handler - Error Handling & Not Found**
    *   As a Developer, I want the `/ask` handler to gracefully handle errors from the `KnowledgeBaseService`, `RedisService`, and `OpenAIService` calls.
    *   As a Developer, if Redis is unavailable during a cache check, the flow should continue to the knowledge base/OpenAI step (logging the Redis error). If Redis fails during caching the result, the answer should still be sent to the user (logging the error).
    *   As a Developer, if the `OpenAIService` call fails, the handler must send a user-friendly error message ("Sorry, I'm having trouble connecting to my brain...") using Block Kit and log the technical error.
    *   As a Developer, if the `KnowledgeBaseService` fails significantly or if the `OpenAIService` indicates no relevant answer could be generated based on the context, the handler must send a specific "I couldn't find a specific answer..." message using Block Kit.
*   **Story 3.4: Implement Analytics Logging Points**
    *   As a Developer, I want to integrate logging calls within the `/ask` and `/help` handlers and the core services (`Redis`, `OpenAI`, `KnowledgeBase`) at the key points specified in PRD Functional Requirement #6 (e.g., command received, cache hit/miss, PDF search, OpenAI call start/end/fail, answer sent, Redis errors).
    *   As a Developer, I want logs to include relevant context (like a request ID or hashed question) but avoid logging sensitive data directly.

---

### Epic 4: Deployment & Documentation Refinement

**Goal:** Optimize the container build process and finalize user-facing documentation for setup and usage.

*   **Story 4.1: Optimize Dockerfile**
    *   As a Developer, I want to review and optimize the `Dockerfile` for potentially smaller image size and faster build times (e.g., using multi-stage builds, optimizing layer caching, specifying non-root user).
    *   As a Developer, I want to ensure the `Dockerfile` correctly exposes the port used by `uvicorn` (e.g., 3000).
*   **Story 4.2: Finalize README Documentation**
    *   As a Developer, I want to update the `README.md` file to include comprehensive and accurate instructions covering:
        *   Project overview.
        *   Prerequisites (Python version, Docker, ngrok for local dev).
        *   Detailed setup steps (cloning, `.env` creation/population based on `.env.example`, PDF data placement).
        *   How to build the Docker image (`docker build ...`).
        *   How to run the Docker container (`docker run ...` including port mapping, `.env` sourcing, and volume mounting for data).
        *   How to configure the Slack App Request URL (mentioning `ngrok` for local testing).
        *   How to use the `/ask` and `/help` commands.

---

### Epic N: Future Enhancements (Beyond MVP)

**Goal:** Capture potential future features and improvements identified but not included in the MVP scope.

*   **Story N.1: Advanced RAG Implementation** (Placeholder)
*   **Story N.2: Conversation Memory** (Placeholder)
*   **Story N.3: User Feedback Mechanism** (Placeholder)
*   **Story N.4: Expanded Document Support** (Placeholder)
*   **Story N.5: Automated Testing Suite Expansion** (Placeholder)
*   **Story N.6: CI/CD Pipeline** (Placeholder)
