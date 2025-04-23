# Slack GPT-Assistant

A Slack bot that answers questions using OpenAI's GPT models and a local knowledge base of PDF documents.

## Features

- Responds to `/ask` commands in Slack
- Searches PDF documents for relevant context
- Uses OpenAI's GPT models to generate answers
- Caches responses in Redis for improved performance
- Provides help via `/help` command

## Prerequisites

- Python 3.11+
- Docker (for containerized deployment)
- Slack API credentials (Bot Token and Signing Secret)
- OpenAI API Key
- Redis instance

## Setup

1. Clone this repository:
   ```
   git clone <repository_url>
   cd slack-gpt
   ```

2. Copy the example environment file and edit it with your credentials:
   ```
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

3. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. Place your PDF documents in the `data` directory.

## Running Locally

```
python -m app.main
```

For local development, you may need to use a tool like ngrok to expose your local server to the internet:

```
ngrok http 3000
```

Then, update your Slack app configuration with the ngrok URL.

## Docker Deployment

Build the Docker image:

```
docker build -t slack-gpt .
```

Run the container:

```
docker run -p 3000:3000 --env-file .env -v $(pwd)/data:/app/data slack-gpt
```

## Development

Install development dependencies:

```
pip install -r requirements-dev.txt
```

Format and lint code:

```
black .
isort .
flake8 .
mypy .
```

Run tests:

```
pytest
```

## License

[MIT](LICENSE) 