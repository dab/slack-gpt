import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.handlers.ask_command import handle_ask_command

@pytest.mark.asyncio
@patch('app.handlers.ask_command.RedisService')
@patch('app.handlers.ask_command.KnowledgeBaseService')
@patch('app.handlers.ask_command.OpenAIService')
async def test_handle_ask_command_valid_question(mock_openai, mock_kb, mock_redis):
    ack = AsyncMock()
    respond = AsyncMock()
    logger = MagicMock()
    command = {'user_id': 'U123', 'text': 'What is AI?'}

    # Simulate cache miss and OpenAI answer
    mock_redis.return_value.get_value = AsyncMock(return_value=None)
    mock_redis.return_value.set_value = AsyncMock()
    mock_kb.return_value.find_relevant_context = AsyncMock(return_value='context')
    mock_openai.return_value.get_answer = AsyncMock(return_value='AI is artificial intelligence.')

    await handle_ask_command(ack, command, respond, logger)

    ack.assert_awaited_once()
    respond.assert_awaited()
    # Check that the response includes the question and answer
    blocks = respond.call_args[1]['blocks']
    assert any('You asked:' in block['text']['text'] for block in blocks if block['type'] == 'section')
    assert any('AI is artificial intelligence.' in block['text']['text'] for block in blocks if block['type'] == 'section')
    # Check that logger.info was called with user_id and question
    log_messages = [call[0][0] for call in logger.info.call_args_list]
    assert any('/ask command received' in msg and 'user_id=U123' in msg and 'question=What is AI?' in msg for msg in log_messages)

@pytest.mark.asyncio
@patch('app.handlers.ask_command.RedisService')
async def test_handle_ask_command_empty_question(mock_redis):
    ack = AsyncMock()
    respond = AsyncMock()
    logger = MagicMock()
    command = {'user_id': 'U123', 'text': ''}

    await handle_ask_command(ack, command, respond, logger)

    ack.assert_awaited_once()
    respond.assert_awaited_once()
    blocks = respond.call_args[1]['blocks']
    assert any('Usage:' in block['text']['text'] for block in blocks if block['type'] == 'section')

@pytest.mark.asyncio
@patch('app.handlers.ask_command.RedisService')
async def test_handle_ask_command_cache_hit(mock_redis):
    ack = AsyncMock()
    respond = AsyncMock()
    logger = MagicMock()
    command = {'user_id': 'U123', 'text': 'Cached Q?'}

    mock_redis.return_value.get_value = AsyncMock(return_value='Cached answer.')

    await handle_ask_command(ack, command, respond, logger)

    ack.assert_awaited_once()
    respond.assert_awaited_once()
    blocks = respond.call_args[1]['blocks']
    assert any('You asked:' in block['text']['text'] for block in blocks if block['type'] == 'section')
    assert any('Cached answer.' in block['text']['text'] for block in blocks if block['type'] == 'section')

@pytest.mark.asyncio
@patch('app.handlers.ask_command.RedisService')
@patch('app.handlers.ask_command.KnowledgeBaseService')
@patch('app.handlers.ask_command.OpenAIService')
async def test_handle_ask_command_no_answer(mock_openai, mock_kb, mock_redis):
    ack = AsyncMock()
    respond = AsyncMock()
    logger = MagicMock()
    command = {'user_id': 'U123', 'text': 'Unknown Q?'}

    mock_redis.return_value.get_value = AsyncMock(return_value=None)
    mock_kb.return_value.find_relevant_context = AsyncMock(return_value='context')
    mock_openai.return_value.get_answer = AsyncMock(return_value=None)

    await handle_ask_command(ack, command, respond, logger)

    ack.assert_awaited_once()
    respond.assert_awaited_once()
    blocks = respond.call_args[1]['blocks']
    assert any("couldn't find an answer" in block['text']['text'] for block in blocks if block['type'] == 'section')
    assert any('You asked:' in block['text']['text'] for block in blocks if block['type'] == 'section') 