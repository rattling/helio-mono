"""Tests for Telegram handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes

from services.adapters.telegram import handlers


@pytest.fixture
def mock_update():
    """Create a mock Telegram Update."""
    update = MagicMock(spec=Update)
    update.message = AsyncMock(spec=Message)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.first_name = "John"
    update.effective_user.id = 12345
    update.effective_user.username = "john"
    update.effective_chat = MagicMock(spec=Chat)
    update.effective_chat.id = 98765
    return update


@pytest.fixture
def mock_context():
    """Create a mock context."""
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    return context


@pytest.fixture
def mock_query_service():
    """Create a mock query service."""
    service = AsyncMock()
    handlers.query_service = service
    return service


@pytest.mark.asyncio
async def test_start_command(mock_update, mock_context):
    """Test /start command."""
    await handlers.start_command(mock_update, mock_context)
    
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "Welcome to Helionyx" in call_args
    assert "John" in call_args


@pytest.mark.asyncio
async def test_help_command(mock_update, mock_context):
    """Test /help command."""
    await handlers.help_command(mock_update, mock_context)
    
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "Available Commands" in call_args
    assert "/todos" in call_args


@pytest.mark.asyncio
async def test_todos_command_empty(mock_update, mock_context, mock_query_service):
    """Test /todos command with no todos."""
    mock_query_service.get_todos.return_value = []
    
    await handlers.todos_command(mock_update, mock_context)
    
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "No todos found" in call_args


@pytest.mark.asyncio
async def test_todos_command_with_filter(mock_update, mock_context, mock_query_service):
    """Test /todos command with status filter."""
    mock_context.args = ["pending"]
    mock_query_service.get_todos.return_value = [
        {"title": "Test todo", "status": "pending", "priority": "medium"}
    ]
    
    await handlers.todos_command(mock_update, mock_context)
    
    mock_query_service.get_todos.assert_called_once_with(status="pending")
    mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_todos_command_invalid_status(mock_update, mock_context, mock_query_service):
    """Test /todos command with invalid status."""
    mock_context.args = ["invalid_status"]
    
    await handlers.todos_command(mock_update, mock_context)
    
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "Invalid status" in call_args


@pytest.mark.asyncio
async def test_stats_command(mock_update, mock_context, mock_query_service):
    """Test /stats command."""
    # get_stats is a sync method, not async
    mock_query_service.get_stats = MagicMock(return_value={
        'todos': 5,
        'notes': 3,
        'tracks': 2,
        'total_objects': 10,
    })
    
    await handlers.stats_command(mock_update, mock_context)
    
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "Statistics" in call_args
    assert "5" in call_args  # todos count
