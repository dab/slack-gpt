# Slack GPT-Assistant

## Project Overview
Slack GPT-Assistant is a Slack bot designed to answer questions by leveraging OpenAI's GPT models and a local PDF-based knowledge base. It processes `/ask` commands to provide responses based on cached data (using Redis) and on-demand queries to the OpenAI API (gpt-4o-mini). The design ensures fast responses with immediate acknowledgment, while performing longer operations asynchronously.

## Prerequisites
- Python 3.11+
- Docker
- ngrok (for local development)
- A Redis instance (local or remote)
- Slack App credentials (Bot Token, Signing Secret)
- OpenAI API Key

## Environment Variables
Ensure that your `.env` file (copied from `.env.example`) is properly populated with the following variables:
- `SLACK_BOT_TOKEN`
- `SLACK_SIGNING_SECRET`
- `OPENAI_API_KEY`
- `REDIS_HOST`
- `REDIS_PORT`
- `REDIS_PASSWORD`
- `PDF_DATA_DIR` (e.g., `./data/company_docs`)
- `MAX_CONTEXT_TOKENS`: Maximum number of tokens to use for context selection in the knowledge base (default: 7000). Set in your `.env` file if you want to override the default.

## Setup Instructions
1. **Clone the Repository:**
   ```bash
   git clone <repository_url>
   cd slack-gpt-assistant
   ```
2. **Configure Environment Variables:**
   - Copy the template file:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` to provide your Slack, OpenAI, and Redis credentials, and specify the path to your PDF documents.
3. **Prepare PDF Documents:**
   Place all required PDF documents into the directory specified by `PDF_DATA_DIR`.

## Build Instructions
Build the Docker image with the following command:
```bash
docker build -t slack-gpt-assistant .
```

## Run Instructions
Run the Docker container:
```bash
docker run -p 3000:3000 --env-file .env -v $(pwd)/data:/app/data slack-gpt-assistant
```
Explanation:
- `-p 3000:3000`: Maps the container's port 3000 to the host.
- `--env-file .env`: Loads environment variables.
- `-v $(pwd)/data:/app/data`: Mounts your local `data` directory (containing PDFs) into the container.

## Slack App Configuration
1. **Expose Local Server:**
   Use ngrok to expose your local server:
   ```bash
   ngrok http 3000
   ```
2. **Configure Request URL:**
   In your Slack App settings, set the Request URL for slash commands (e.g., `/ask` and `/help`) to the ngrok URL (e.g., `https://<ngrok-id>.ngrok.io/slack/events`).

## Usage
- **/ask <question>**: Ask the bot a question. The bot acknowledges immediately, then provides an answer asynchronously based on a search of PDF documents and OpenAI API results.
- **/help**: Displays help information outlining how to use the bot.

## Features
- **Slack Command Handling:** Responds to `/ask` and `/help` commands in Slack.
- **PDF Knowledge Base:** Extracts text from PDFs using PyMuPDF for contextual responses.
- **Redis Caching:** Caches Q&A pairs to improve performance.
- **OpenAI Integration:** Uses gpt-4o-mini to generate responses.
- **Asynchronous Processing:** Provides immediate command acknowledgment with asynchronous detailed responses.
- **Logging & Error Handling:** Logs significant events and gracefully handles errors.

## Project Architecture
For a high-level overview of the project's architecture, refer to the [Architecture Document](./ai/arch.md). The app is built as a monolithic Docker container with dedicated services for handling Slack events, PDF data extraction, OpenAI API interactions, and Redis caching.

## Redis Setup
For local development, you can run a Redis server using Docker. For example, execute the following command:
```bash
docker run --name slack-redis -p 6379:6379 -d redis:6.2-alpine
```
Then, update your `.env` file with the following settings:
- `REDIS_HOST=localhost`
- `REDIS_PORT=6379`
- (Optional) Set `REDIS_PASSWORD` if your Redis instance requires authentication.

## Development
Install development dependencies:
```bash
pip install -r requirements-dev.txt
```
Format, lint, and test your code:
```bash
black .
isort .
flake8 .
mypy .
pytest
```

## Dependencies

- `tiktoken` (for token counting, used in KnowledgeBaseService context selection)

## License
[MIT](LICENSE) 