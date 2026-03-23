# maivn-shared

Shared contracts, models, utilities, and logging primitives for the Maivn platform.

## Overview

`maivn-shared` is the public shared package used by the Maivn SDK and service repos. It provides
the shared domain entities, configuration models, serialization helpers, event contracts, and
logging abstractions that need to stay consistent across the platform.

**Key Design Principles:**

- ✅ Environment-agnostic (no environment variable access)
- ✅ Immutable configuration objects
- ✅ Type-safe Pydantic models
- ✅ Proper dependency inversion
- ✅ Zero external service dependencies

## Installation

```bash
# Using uv (recommended)
uv add maivn-shared

# Using pip
pip install maivn-shared
```

## Architecture

```
maivn-shared/
├── domain/          # Pure business entities (no external dependencies)
│   └── entities/    # Pydantic models for tasks, tools, sessions, etc.
├── core/            # Application services
│   ├── config/      # Configuration management
│   ├── data/        # Data utilities (UUID generation)
│   └── http/        # HTTP client
└── infrastructure/  # Factories and adapters
    └── factories/   # Object creation logic
```

### Domain Layer

Pure business entities with no external dependencies:

- **Tasks**: Planning-time task models (`Task`, `TaskList`, `TaskToolCall`)
- **Tools**: Tool specifications and execution models (`ToolSpec`, `ToolExecutionCall`)
- **Sessions**: Session request/response models
- **Messages**: LangChain message wrappers
- **Dependencies**: Tool dependency models (agent, tool, data, user)
- **Status**: Lifecycle status enumeration

### Core Layer

Application services and utilities:

- **ConfigManager**: Factory for creating HTTPConfig and ServerConfig
- **HTTPClient**: Unified HTTP client with proper error handling
- **UUID utilities**: Deterministic and random UUID generation
- **ArgumentResolver**: Resolves TaskReferences, DataReferences, and ArgValues in task arguments
- **MessageFilter**: Filters messages and events for client consumption
- **constants**: Shared non-sensitive constants (timeouts, separators, etc.)

### Infrastructure Layer

Factories and adapters:

- **TaskExecutionCallFactory**: Creates TaskExecutionCall instances from tasks

## Usage Examples

### Configuration Management

```python
from maivn_shared.core import config

# Get HTTP configuration with defaults
http_config = config.get_http_config()

# Override specific values
http_config = config.get_http_config(
    timeout=30.0,
    max_retries=5
)

# Get server configuration
server_config = config.get_server_config(
    base_url="https://api.example.com"
)
```

### HTTP Client

```python
from maivn_shared.core import HTTPClient

client = HTTPClient(timeout=10.0)

# Make POST request
response = client.post(
    "https://api.example.com/endpoint",
    payload={"key": "value"}
)

# Make GET request
response = client.get("https://api.example.com/data")
```

### Task Models

```python
from maivn_shared.domain.entities import (
    Task,
    TaskList,
    TaskToolCall,
    ArgValue,
    TaskReference,
    Status
)

# Create a task
task = Task(
    index=0,
    status=Status.PENDING,
    tool_call=TaskToolCall(
        name="search_web",
        args={"query": ArgValue(value="python tutorial")}
    )
)

# Create task list
task_list = TaskList(items=[task])

# Check dependencies
deps = task.get_dependency_indices()
can_run = task.can_start(completed_task_indices=set())
```

### Task Execution Calls

```python
from maivn_shared import ToolSpec
from maivn_shared.domain.entities import Task, TaskList
from maivn_shared.infrastructure.factories import TaskExecutionCallFactory

# Define available tools
tools = [
    ToolSpec(
        tool_id="tool_1",
        agent_id="agent_1",
        name="search_web",
        description="Search the web",
        args_schema={"query": {"type": "string"}}
    )
]

# Create factory
factory = TaskExecutionCallFactory(tools=tools)

# Build execution call from task
execution_call = factory.build(task)

# Build from entire task list
call_list = factory.build_from_tasklist(task_list)
```

### Argument Resolution

```python
from maivn_shared import ArgumentResolver, TaskReference, DataReference, ArgValue

# Create resolver
resolver = ArgumentResolver()

# Resolve TaskReference
result = resolver.resolve(
    TaskReference(task_index=0),
    task_results={0: "search results"}
)
# Result: "search results"

# Resolve DataReference
result = resolver.resolve(
    DataReference(key_name="user_id"),
    private_data={"user_id": "user_123"}
)
# Result: "user_123"

# Resolve nested structure
args = {
    "query": TaskReference(task_index=0),
    "limit": 10,
    "user": DataReference(key_name="user_id")
}
resolved = resolver.resolve(
    args,
    task_results={0: "python tutorial"},
    private_data={"user_id": "user_123"}
)
# Result: {"query": "python tutorial", "limit": 10, "user": "user_123"}

# Convenience function for resolving all args
from maivn_shared import resolve_arguments
resolved_args = resolve_arguments(
    args,
    task_results={0: "value"},
    private_data={"key": "value"}
)
```

### Message Filtering

```python
from maivn_shared import MessageFilter, HumanMessage, AIMessage, SystemMessage

messages = [
    HumanMessage(content="Hello"),
    SystemMessage(content="System prompt"),
    AIMessage(content="Hi there!")
]

# Filter for client messages only (human + AI)
filtered = MessageFilter.filter_client_messages(messages)
# Result: [HumanMessage(...), AIMessage(...)]

# Filter by specific types
filtered = MessageFilter.filter_messages_by_type(
    messages,
    allowed_types={"human", "system"}
)

# Filter event data
event = {
    "results": ["result1"],
    "messages": [...],
    "metadata": {...},
    "_internal": {...}  # filtered out
}
filtered_event = MessageFilter.filter_update_event(event)
```

### Constants

```python
from maivn_shared import constants

# Use shared constants
timeout = constants.DEFAULT_TASK_TIMEOUT_SECONDS
separator = constants.INPUT_SEPARATOR
# Note: MOCK_USER_ID moved to maivn-server (environment-specific)
```

### Logging

```python
from maivn_shared import get_logger

# Initialize with file logging (first call only)
logger = get_logger(log_file_path="/path/to/logs/agent_execution.log")

# Or initialize with console-only logging
logger = get_logger()  # No file logging, only console output

# Use logger
logger.log_session_start(
    session_id="session_123",
    assistant_id="assistant_1",
    thread_id="thread_1"
)

logger.log_task_execution(
    phase="completed",
    task_idx=0,
    tool_name="search_web",
    result={"results": [...]}
)

logger.log_session_end(session_id="session_123")
```

## API Reference

### Core Exports

```python
from maivn_shared import (
    # Utilities
    ArgumentResolver,
    resolve_arguments,
    MessageFilter,
    constants,

    # Configuration
    ArgsSchema,
    HTTPConfig,
    ServerConfig,

    # Session
    SessionResponse,

    # Tools
    ToolExecutionCall,
    ToolSpec,
    ToolType,

    # Logging
    MaivnLogger,
    get_logger,
    get_optional_logger,
)
```

### Domain Entities

```python
from maivn_shared.domain.entities import (
    # Tasks
    Task,
    TaskList,
    TaskToolCall,
    TaskResult,
    ArgValue,
    DataReference,
    TaskReference,

    # Tools
    ToolSpec,
    ToolType,
    ToolExecutionCall,
    ToolExecutionCallList,

    # Sessions
    SessionRequest,
    SessionResponse,
    SessionStartupResponse,

    # Messages
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,

    # Dependencies
    BaseDependency,
    AgentDependency,
    ToolDependency,
    DataDependency,
    InterruptDependency,

    # Status
    Status,
)
```

### Core Services

```python
from maivn_shared.core import (
    ArgumentResolver,    # Argument resolution utility
    resolve_arguments,   # Convenience function for arg resolution
    MessageFilter,       # Message/event filtering
    constants,           # Shared constants module
    config,              # Global ConfigManager instance
    ConfigManager,       # Configuration factory
    HTTPClient,          # HTTP client
    HTTPClientError,     # Base HTTP exception
    create_uuid,         # UUID generation
)
```

### Infrastructure

```python
from maivn_shared.infrastructure.factories import (
    TaskExecutionCallFactory,
)
```

## Configuration

`maivn-shared` is intentionally environment-agnostic and does not read deployment-specific
environment variables or configuration files. Applications should inject those values explicitly.

## Development

### Requirements

- Python 3.10+
- langchain-core >= 0.3.76

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
pyright
```

## Releases

- `CI` runs on pull requests and pushes to `main`.
- `Publish PyPI` runs on version tags that match `v*`.
- Configure PyPI Trusted Publishing for this repository before the first release.
- See [`DEPLOYMENT.md`](DEPLOYMENT.md) for the full GitHub and PyPI release procedure.

## License

See LICENSE file in the repository root.

## Related Packages

- **maivn**: Public SDK that depends on `maivn-shared`
- **maivn-internal-shared**: Private service-only shared code
- **maivn-server** / **maivn-agents**: Service repos that consume these contracts
