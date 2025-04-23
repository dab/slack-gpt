## Deep Research Report for Slack GPT-Assistant PRD

### 1. PDF Text Extraction and Basic RAG Search

*   **Summary:**
    *   **Library Comparison:** `PyMuPDF` (Fitz) is consistently highlighted as a high-performance and accurate library for text extraction, often outperforming `pdfminer.six` in speed and `pypdf` (formerly PyPDF2) in robustness and feature set (like preserving layout). `pdfminer.six` is also accurate but can be slower and more complex. `pypdf` is simpler but less capable for complex layouts or accurate extraction. For MVP, `PyMuPDF` seems a strong choice as specified in the PRD, balancing speed and accuracy.
    *   **Search Strategy (MVP):** Simple keyword matching (e.g., TF-IDF, basic string matching on extracted text chunks) is feasible for MVP but has limitations (synonyms, context). Basic embedding lookups (using libraries like `sentence-transformers` with pre-trained models like `all-MiniLM-L6-v2`) offer better semantic relevance but add complexity (model loading, vector storage/search - potentially overkill for MVP unless accuracy is paramount). A hybrid approach (keyword search first, then embedding if no good keyword match) is possible but adds complexity. For MVP, focusing on robust text extraction (`PyMuPDF`), intelligent chunking (splitting text by paragraphs or sections), and simple keyword search seems appropriate, aligning with the PRD's suggestion but acknowledging its limitations.
*   **Suggested PRD Implications/Clarifications:**
    *   Story 1.5: Re-affirm the choice of `PyMuPDF` based on performance findings.
    *   Story 1.5: Explicitly state that the "basic search/retrieval logic" for MVP will be keyword-based (e.g., TF-IDF or similar) on text chunks, and that embedding lookup is a specific "Future Epic Enhancement". This manages expectations for MVP relevance accuracy.
    *   Add a note under "Knowledge Base" functional requirements about potential limitations of keyword search for relevance.
*   **Specific Architecture Implications:**
    *   Confirm `PyMuPDF` dependency.
    *   Design the `knowledge_base.py` service to efficiently chunk PDF text (e.g., by paragraph or a fixed token size with overlap) to provide context for keyword searching.
    *   Keyword search implementation needs to be efficient enough not to significantly delay the asynchronous response.

### 2. Asynchronous Task Handling in Slack Bolt

*   **Summary:** The 3-second acknowledgment limit for Slack commands is strict. Slack Bolt for Python provides mechanisms to handle this. The standard pattern is:
    1.  Register a "lazy listener" function for the command.
    2.  Inside the listener, immediately call `ack()` to send the HTTP 200 OK response to Slack *before* starting any long-running work (PDF search, OpenAI call).
    3.  Execute the long-running task asynchronously (e.g., using Python's `asyncio`, `threading`, or a background task queue like Celery if complexity grows).
    4.  Use the `respond()` or `say()` utility functions (available via the context `ctx` or client) or the `response_url` provided in the command payload to send the final result back to the user asynchronously. Using `respond()` is generally simpler within Bolt. Issues arise if any processing happens *before* `ack()`, potentially delaying it beyond 3 seconds.
*   **Suggested PRD Implications/Clarifications:**
    *   Story 1.6: Explicitly mention the requirement to call `ack()` *immediately* upon receiving the command within the handler *before* initiating PDF search, caching, or OpenAI calls.
    *   Story 1.6: Clarify that the asynchronous task execution should use Python's built-in async capabilities (`asyncio` with Bolt's async support) for the MVP, deferring external task queues unless proven necessary.
*   **Specific Architecture Implications:**
    *   Ensure the `/ask` command handler in `ask_command.py` is an `async def` function.
    *   The first line (or very close to it) within the handler must be `await ack()`.
    *   Subsequent operations (PDF search, cache check, OpenAI call, response formatting) must be performed after the `ack()` call, potentially using `await` for I/O-bound operations within the same async function or offloading CPU-bound tasks if necessary (though PDF processing might be I/O bound depending on `PyMuPDF`).
    *   Use `await respond(...)` or `await say(...)` to send the final answer.

### 3. Effective Caching Strategy

*   **Summary:**
    *   **Normalization:** Simple normalization (lowercase, remove punctuation, sort words) is a baseline. More advanced techniques include stemming/lemmatization or using phonetic algorithms (like Soundex, Metaphone) but can reduce precision. Hashing the normalized question (e.g., SHA-256) provides a consistent key format.
    *   **Semantic Caching:** For better hit rates on differently worded but semantically similar questions, embedding-based caching is an option. Store the question embedding alongside the answer. When a new question arrives, find the nearest neighbor embedding in the cache; if similarity is above a threshold, return the cached answer. This adds significant complexity (vector database or search index needed within Redis or separately) and is likely beyond MVP scope.
    *   **Redis Patterns:** Using simple `GET`/`SET` with TTL (as suggested in PRD) is standard for key-value caching. Hashing the normalized question provides a good key. Storing structured data (like question, answer, timestamp) can be done using JSON strings or Redis Hashes (`HSET`/`HGETALL`).
*   **Suggested PRD Implications/Clarifications:**
    *   FR4: Specify the normalization strategy for cache keys for MVP: "Cache key SHOULD be based on a normalized version of the user's question text (e.g., lowercased, punctuation removed, whitespace collapsed) and potentially hashed."
    *   Add "Semantic Caching using embeddings" to the "Future Epic Enhancements" list.
*   **Specific Architecture Implications:**
    *   Implement a robust normalization function in `app/utils` or within `redis_service.py`.
    *   Use standard Redis `SETEX` (Set with Expiry) or `SET` + `EXPIRE` for simplicity.
    *   Consider storing a hash of the normalized question as the key.

### 4. Scalability Considerations for MVP (~100 Concurrent Users)

*   **Summary:** 100 concurrent users is a moderate load. Potential bottlenecks:
    *   **Slack Bolt:** Python's GIL can limit true CPU parallelism. However, Bolt uses `asyncio`, making it suitable for I/O-bound tasks (network calls to Slack, OpenAI, Redis). Ensure the server/container has sufficient resources (CPU/memory). Bolt's default web server might need tuning or replacement with a more robust ASGI server (like Uvicorn or Hypercorn) behind a reverse proxy (like Nginx) for production.
    *   **OpenAI API:** Rate limits and latency. Implement retries with exponential backoff. Use connection pooling if using persistent clients.
    *   **Redis:** Generally very fast, but network latency and connection limits can be factors. Use connection pooling (`redis-py` has built-in support). Ensure Redis instance has adequate resources.
    *   **PDF Processing (`PyMuPDF`):** Can be CPU or I/O intensive depending on PDF complexity and size. If CPU-bound, it could block the `asyncio` event loop. Consider running PDF processing in a separate thread or process pool executor (`run_in_executor`) if it proves to be a bottleneck during testing. Pre-processing PDFs (extracting text on startup or via a background job) could mitigate runtime load but increases startup time/complexity.
    *   **Resource Limits:** Container memory/CPU limits need to be adequate.
*   **Suggested PRD Implications/Clarifications:**
    *   NFR 2: Add a note: "Performance under load should be validated through basic load testing post-MVP or during refinement."
    *   Story 2.1 (Dockerfile Optimization): Add "Consider using a production-grade ASGI server like Uvicorn within the container."
    *   Story 1.5 / 1.6: Add a note about potentially needing to offload CPU-intensive PDF processing from the main event loop if performance testing reveals issues. Consider adding "Pre-processing of PDFs" to Future Epics.
*   **Specific Architecture Implications:**
    *   Use `redis-py`'s connection pooling.
    *   Implement robust error handling and retries for OpenAI API calls.
    *   Structure the `knowledge_base.py` service to be mindful of potential blocking; use `asyncio.to_thread` or `loop.run_in_executor` for potentially long-running synchronous `PyMuPDF` operations if they block the event loop significantly.
    *   Configure the Docker container with appropriate resource requests/limits.
    *   Plan to use Uvicorn or similar to run the Bolt app within Docker.

### 5. Python Project Standards & AI Directives

*   **Summary:**
    *   **Standard Tools:** The combination of `black` (uncompromising code formatter), `isort` (import sorter), `flake8` (linter for style and errors - often with plugins like `flake8-bugbear`), and `mypy` (static type checker) is a very common and recommended setup for modern Python projects. `pylint` is an alternative/complement to `flake8` but can be noisier.
    *   **Configuration:** Configuring these tools via `pyproject.toml` is the modern standard, consolidating settings in one place.
    *   **Style Guides:** PEP 8 is the fundamental baseline. `black` enforces a strict subset of PEP 8. Google Python Style Guide is another comprehensive option. Consistency is key.
    *   **AI Directives:** For AI agents:
        *   "Follow PEP 8 guidelines."
        *   "Format code using `black`."
        *   "Sort imports using `isort`."
        *   "Add type hints compliant with `mypy`."
        *   "Write docstrings for all public modules, classes, functions, and methods using Google style."
        *   "Log errors appropriately; don't just print them."
        *   "Use f-strings for string formatting."
        *   "Handle potential exceptions explicitly."
        *   "Keep functions small and focused."
*   **Suggested PRD Implications/Clarifications:**
    *   Add a new Non-Functional Requirement: **"Code Quality"**: "Code MUST adhere to PEP 8 standards. Code formatting MUST be enforced using `black`. Imports MUST be sorted using `isort`. Linting MUST be performed using `flake8`. Static type checking MUST be performed using `mypy`. Configuration for these tools SHOULD reside in `pyproject.toml`."
    *   Story 1.1: Add requirement: "Set up `pyproject.toml` with configurations for `black`, `isort`, `flake8`, and `mypy`."
    *   (Optional) Create a `CONTRIBUTING.md` or section in `README.md` outlining these standards and how to run the checks (potentially using pre-commit hooks).
*   **Specific Architecture Implications:**
    *   Ensure `pyproject.toml` is created and configured early.
    *   Integrate these tools into the development workflow (e.g., IDE integration, pre-commit hooks, CI checks).
    *   The AI Agent (you, in this case) should strictly follow these standards when generating or modifying code.

This research provides valuable context and suggests minor refinements to the PRD and key considerations for the upcoming architecture design.
