# FastAPI Real-Time Communication Demo

A comprehensive FastAPI application demonstrating real-time communication using both Server-Sent Events (SSE) and WebSockets.

## Features

- **WebSocket Chat**: Bidirectional real-time chat with room support
- **Server-Sent Events**: One-way streaming for notifications, data feeds, and time updates
- **Interactive Demo**: HTML interface to test all real-time features
- **Docker Support**: Containerized application with docker-compose
- **Modern Python**: Built with Python 3.13 and uv package manager

## Quick Start

### Using Docker (Recommended)
```bash
# Clone the repository
git clone <your-repo-url>
cd hello-uvicorn

# Start with docker-compose
docker-compose up --build
```

### Local Development
```bash
# Clone the repository
git clone <your-repo-url>
cd hello-uvicorn

# Create virtual environment and install dependencies
uv venv
uv sync

# Run the application
uv run uvicorn main:app --reload
```

## Usage

1. Start the application (see Quick Start above)
2. Open your browser to `http://localhost:8000`
3. Visit `http://localhost:8000/demo` for the interactive demo
4. Test the different real-time communication features:
   - WebSocket chat with multiple rooms
   - Server-sent events for notifications
   - Real-time data feeds
   - Time streaming

## API Endpoints

### WebSocket Endpoints
- `/ws/chat/{room_id}` - Real-time chat with room support
- `/ws/echo` - Simple echo WebSocket for testing

### Server-Sent Events
- `/events/stream` - Basic time updates
- `/events/notifications` - System notifications
- `/events/data-feed` - Simulated real-time data (stock prices)
- `/events/chat/{room_id}` - Chat-like SSE stream (read-only)

### HTTP Endpoints
- `/` - Basic API endpoint
- `/demo` - Interactive demo page
- `/docs` - FastAPI automatic documentation
- `/redoc` - Alternative API documentation

## Technology Stack

- **FastAPI** - Modern Python web framework
- **uvicorn** - ASGI server
- **WebSockets** - Bidirectional real-time communication
- **Server-Sent Events** - One-way streaming
- **Docker** - Containerization
- **uv** - Fast Python package manager

## License

MIT License - see LICENSE for details.