# Mooltiproxy Architecture Documentation

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Component Details](#component-details)
4. [Request Flow](#request-flow)
5. [Configuration System](#configuration-system)
6. [Extension Points](#extension-points)
7. [Security Model](#security-model)

---

## Overview

### Purpose
Mooltiproxy is an HTTP proxy that translates API requests between different formats, primarily designed to expose OpenAI-compatible endpoints while proxying to alternative backends like Hugging Face TGI.

### Key Features
- **API Translation**: Convert request/response formats between different APIs
- **Bearer Token Authentication**: Master key-based access control
- **IP-based Security**: Whitelist, blacklist, and automatic banning
- **Flexible Routing**: Map incoming paths to different backend endpoints
- **Prompt Templates**: Transform chat messages to various prompt formats
- **Extensible Design**: Plugin-style mappers and prompters

### Design Philosophy
- **Minimal Dependencies**: Only 3 Python packages required
- **Configuration-Driven**: Behavior controlled via YAML config
- **Experimentation-Focused**: Quick switching between backends
- **Self-Contained**: No external services required

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Client                               │
│                  (OpenAI SDK, curl, etc.)                   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP Request
                         │ Authorization: Bearer <PROXY_KEY>
                         │ Header: target=<target_name>
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     MOOLTIPROXY                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  ProxyHandler (main.py)                                │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │ │
│  │  │   OPTIONS    │  │   GET/POST   │  │   Security  │  │ │
│  │  │   Handler    │  │   Routing    │  │   (Cerbere) │  │ │
│  │  └──────────────┘  └──────────────┘  └─────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
│                            │                                 │
│  ┌────────────────────────┼────────────────────────────┐    │
│  │  Translation Layer     │                            │    │
│  │  ┌─────────────┐  ┌────▼──────┐  ┌──────────────┐  │    │
│  │  │  Prompters  │  │  Mappers  │  │  Templates   │  │    │
│  │  │  (prompts)  │◄─┤ (request) │◄─┤   (config)   │  │    │
│  │  └─────────────┘  └───────────┘  └──────────────┘  │    │
│  └────────────────────────────────────────────────────┘    │
│                            │                                 │
│  ┌────────────────────────▼────────────────────────────┐    │
│  │  Configuration System (utils.py)                    │    │
│  │  - YAML parsing                                      │    │
│  │  - Validation (voluptuous)                          │    │
│  │  - Environment variable injection                   │    │
│  └────────────────────────────────────────────────────┘    │
└────────────────────────┬────────────────────────────────────┘
                         │ Translated Request
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Target API Backend                         │
│          (OpenAI, TGI, Custom API, etc.)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. main.py - HTTP Server & Request Handler

**Class: ProxyHandler**
- Extends `BaseHTTPRequestHandler`
- Handles HTTP methods: GET, POST, OPTIONS

**Key Methods:**
```python
do_GET()           # Handles GET requests
do_POST()          # Handles POST requests
do_OPTIONS()       # Handles CORS preflight
proxy_request()    # Main request processing logic
forward_request()  # Sends request to target API
answer_client()    # Sends response back to client
error_reply()      # Standardized error responses
```

**Request Processing Flow:**
1. Check IP blacklist
2. Validate bearer token
3. Determine target from header or default
4. Validate path mapping exists
5. Forward request (with optional translation)
6. Receive and translate response
7. Send back to client

**Global Configuration:**
- `G_port`: Server port
- `G_debug`: Debug mode flag
- `G_use_ssl`: SSL/TLS mode
- `G_master_key`: Proxy authentication key
- `G_timeout`: Backend request timeout

### 2. cerbere.py - Security & Access Control

**Class: Cerbere**

**Purpose:** IP-based access control and rate limiting

**Attributes:**
```python
trials: int           # Max failed attempts before ban
blacklist: dict      # Banned IPs
whitelist: dict      # Allowed IPs (exempt from banning)
suspect: dict        # Failed attempt counter per IP
```

**Methods:**
```python
blacklisted(ip: str) -> bool     # Check if IP is banned
whitelisted(ip: str) -> bool     # Check if IP is trusted
watch(ip: str) -> bool           # Track failed attempts, ban if exceeded
```

**Limitation:** Bans are in-memory only (lost on restart)

### 3. mappers.py - Payload Translation

**Purpose:** Convert request/response payloads between API formats

**Built-in Mappers:**

| Function | Direction | Purpose |
|----------|-----------|---------|
| `identity()` | Both | Pass-through (for testing) |
| `textReqOpenAItoTGI()` | Request | OpenAI text → TGI format |
| `textAnsTGItoOpenAI()` | Response | TGI → OpenAI text format |
| `chatReqOpenAItoTGI()` | Request | OpenAI chat → TGI format |
| `chatAnsTGItoOpenAI()` | Response | TGI → OpenAI chat format |

**Mapper Signature:**
```python
def mapper_name(ip: Any, cfg: dict = {}) -> Any:
    """
    ip: Input payload (dict for JSON, str for text)
    cfg: Endpoint configuration from config.yaml
    Returns: Transformed payload
    """
```

**Key Transformations:**
- Parameter name mapping (e.g., `max_tokens` → `max_new_tokens`)
- Value transformations (e.g., temperature normalization)
- Structure changes (e.g., message list → single prompt string)
- Metadata generation (e.g., fake IDs, timestamps)

### 4. prompters.py - Prompt Formatting

**Purpose:** Convert chat message history to formatted prompt strings

**Built-in Prompters:**

**`fromTemplate(messages, cfg)`**
- Generic template-based prompt builder
- Uses templates from `config.yaml`
- Handles system/user/assistant roles
- Returns: `(prompt_string, stop_sequences)`

**`llama2_chat(messages, cfg)`**
- Llama 2 Chat specific format
- Special tokens: `<s>`, `</s>`, `[INST]`, `[/INST]`, `<<SYS>>`, `<</SYS>>`
- Alternating user/assistant pattern
- Returns: `(prompt_string, stop_sequences)`

**Template Structure:**
```yaml
template_name:
  preprompt: ""        # Prefix before everything
  start: ""            # After preprompt and system message
  system: ""           # System message wrapper
  user: ">>QUESTION>>" # User message prefix
  assistant: ">>ANSWER>>" # Assistant message prefix
```

### 5. utils.py - Configuration & Utilities

**Purpose:** Configuration loading, validation, and logging utilities

**Key Functions:**

**Logging:**
```python
error(s)       # Red error messages
warning(s)     # Yellow warnings
info(s)        # Blue informational
success(s)     # Green success
debug(s)       # Gray debug output
alert(s)       # Magenta alerts
fatal(s)       # Bright red fatal errors
```

**Configuration:**
```python
load_config(filename) -> dict
```

**Validation Schema:**
- Uses `voluptuous` for schema validation
- Validates:
  - System settings (port, SSL, debug)
  - Security settings (IP lists, max tries)
  - Target definitions
  - Mapper/prompter function existence
  - Template definitions
  - Cross-references (default target exists)

**Configuration Enrichment:**
1. Loads YAML file
2. Validates against schema
3. Injects environment variables for keys
4. Instantiates templates at endpoint level
5. Returns enriched config dict

---

## Request Flow

### Successful Request Flow

```
1. Client Request Arrives
   ├─ Extract: IP, Authorization, Target header, Path, Body
   │
2. Security Check (Cerbere)
   ├─ Is IP blacklisted? → 403 + error
   ├─ Is Authorization valid? → 403 + increment suspect counter
   │  └─ Too many failures? → Add to blacklist
   │
3. Routing
   ├─ Get target name (from header or default)
   ├─ Target exists? → 404 if not
   ├─ Path mapped? → 404 if not
   │
4. Request Translation (if configured)
   ├─ Content-Type: application/json?
   ├─ "in" mapper configured?
   │  ├─ Parse JSON body
   │  ├─ Apply prompter (if configured)
   │  │  └─ Convert messages → prompt string
   │  ├─ Apply mapper function
   │  │  └─ Transform payload structure
   │  └─ Re-encode as JSON
   │
5. Forward to Target
   ├─ Build target URL (base + mapped path)
   ├─ Build headers (Content-Type + optional API key)
   ├─ Send request (preserve method if configured)
   │  └─ Handle redirects
   ├─ Status != 200? → Return error to client
   │
6. Response Translation (if configured)
   ├─ Content-Type: application/json?
   ├─ "out" mapper configured?
   │  ├─ Parse JSON response
   │  ├─ Apply mapper function
   │  └─ Re-encode as JSON
   │
7. Send Response to Client
   ├─ Set status code (from target)
   ├─ Filter headers (remove problematic ones)
   ├─ Update Content-Length
   ├─ Send body
   │
8. Done
```

### OPTIONS Request (CORS Preflight)

```
1. Client sends OPTIONS
   ├─ Read origin and allowed headers from request
   │
2. Send Yes-Server Response
   ├─ 200 OK
   ├─ Access-Control-Allow-Origin: <origin>
   ├─ Access-Control-Allow-Headers: <requested headers>
   ├─ Access-Control-Allow-Methods: <requested method>
   └─ Content-Length: 0
```

---

## Configuration System

### Configuration File Structure

```yaml
system:
  ssl: bool              # Enable HTTPS
  debug: bool            # Verbose logging
  port: int              # Server port
  timeout: int/float     # Backend timeout
  masterkey: str         # Proxy key (NOT RECOMMENDED)

cerbere:
  max_tries: int         # Failed attempts before ban
  whitelist: [str]       # IP addresses to trust
  blacklist: [str]       # IP addresses to block

targets:
  default: str           # Default target name

  <target_name>:
    url: str             # Backend base URL
    key: str             # API key (NOT RECOMMENDED)
    envkey: str          # Environment variable name for API key
    preserveMethod: bool # Keep HTTP method during redirects

    mapping:
      <path>:            # Can be null, str, or object
        path: str        # Target path (optional)
        in: str          # Request mapper function name
        out: str         # Response mapper function name
        prompter: str    # Prompter function name
        template: str    # Template name to use

templates:
  <template_name>:
    preprompt: str
    start: str
    system: str
    user: str
    assistant: str
```

### Environment Variables

**Required:**
- `MOOLTIPROXY_KEY`: Master proxy authentication key

**Optional (per target):**
- Referenced by `envkey` in target configuration
- Used as API keys for backend services

### Configuration Validation

**Checks performed:**
1. IP addresses match regex pattern
2. Default target exists in targets list
3. Mapper functions exist in `mappers.py`
4. Prompter functions exist in `prompters.py`
5. Template names exist in templates section
6. Environment variables (envkey) are set
7. All required fields present

---

## Extension Points

### Adding a New Mapper

1. **Add function to `mappers.py`:**
```python
def myReqSourceToTarget(ip: Any, cfg: dict = {}) -> Any:
    """Convert SourceAPI request to TargetAPI format"""
    # Your transformation logic
    output_payload = {
        "target_param": ip.get("source_param", "default")
    }
    return output_payload

def myAnsTargetToSource(ip: Any, cfg: dict = {}) -> Any:
    """Convert TargetAPI response to SourceAPI format"""
    # Your transformation logic
    return output_payload
```

2. **Configure in `config.yaml`:**
```yaml
targets:
  my_target:
    mapping:
      /my/endpoint:
        in: myReqSourceToTarget
        out: myAnsTargetToSource
```

### Adding a New Prompter

1. **Add function to `prompters.py`:**
```python
def my_custom_prompter(messages: list[dict], cfg: dict) -> tuple[str, str]:
    """Convert message list to custom prompt format"""
    prompt = ""
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        # Build your prompt format
        prompt += f"<{role}>{content}</{role}>"

    stop_sequences = ["</assistant>"]
    return prompt, stop_sequences
```

2. **Configure in `config.yaml`:**
```yaml
targets:
  my_target:
    mapping:
      /chat/completions:
        prompter: my_custom_prompter
```

### Adding a New Template

**Add to `config.yaml`:**
```yaml
templates:
  MyCustomFormat:
    preprompt: "### SYSTEM INSTRUCTIONS ###\n"
    start: "\n### CONVERSATION START ###\n"
    system: ""
    user: "\n[USER]: "
    assistant: "\n[BOT]: "
```

**Use in endpoint:**
```yaml
mapping:
  /chat/completions:
    template: MyCustomFormat
    prompter: fromTemplate
```

---

## Security Model

### Authentication Layers

**Layer 1: Master Key**
- Required in `Authorization: Bearer <MOOLTIPROXY_KEY>` header
- Single key for all clients
- Recommended: Set via `MOOLTIPROXY_KEY` environment variable
- Not recommended: Hardcode in config file

**Layer 2: IP-based Access Control**
- Whitelist: Trusted IPs (never banned)
- Blacklist: Permanently blocked IPs
- Automatic banning after N failed auth attempts
- Ban duration: Until server restart (no persistence)

**Layer 3: Backend API Keys**
- Optional per-target API keys
- Automatically injected into forwarded requests
- Recommended: Use `envkey` to reference environment variables
- Not recommended: Hardcode in config file

### Threat Model

**Protected Against:**
- ✓ Unauthorized API access (master key required)
- ✓ Brute force attacks (IP banning after N failures)
- ✓ Known malicious IPs (manual blacklist)

**Not Protected Against:**
- ✗ DDoS attacks (no rate limiting per key)
- ✗ Slow-loris attacks (synchronous request handling)
- ✗ SSL/TLS attacks (if SSL used without proper config)
- ✗ Timing attacks (no constant-time comparison)
- ✗ Man-in-the-middle (if SSL not configured)

**Security Recommendations:**
1. Always use HTTPS in production
2. Use strong, random master keys (32+ characters)
3. Store keys in environment variables only
4. Deploy behind a reverse proxy (nginx, Caddy)
5. Use firewall rules for additional IP filtering
6. Monitor logs for suspicious activity
7. Implement rate limiting at reverse proxy level

### CORS Handling

**Behavior:**
- Acts as a "Yes Server" for OPTIONS requests
- Echoes back requested origin and headers
- Does NOT consult backend API for CORS policy
- Allows all methods and headers by default

**Security Implication:**
- Permissive CORS policy
- Fine for internal/development use
- May need tightening for public deployment

---

## Data Flow Examples

### Example 1: OpenAI Chat → TGI Text Generation

**Input (from client):**
```json
POST /chat/completions
Authorization: Bearer <PROXY_KEY>
Header: target=my_tgi_server

{
  "model": "gpt-3.5-turbo",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 100
}
```

**Transformation Steps:**

1. **Prompter** (`llama2_chat` or `fromTemplate`):
   - Converts message list to single prompt string
   - Example output: `"<s>[INST]<<SYS>>You are a helpful assistant<</SYS>>Hello![/INST]"`

2. **Request Mapper** (`chatReqOpenAItoTGI`):
   ```json
   {
     "inputs": "<s>[INST]<<SYS>>You are a helpful assistant<</SYS>>Hello![/INST]",
     "parameters": {
       "max_new_tokens": 100,
       "temperature": 0.7,
       "top_p": 0.95,
       "stop": ["[INST]"],
       ...
     }
   }
   ```

3. **Forwarded to:** `https://my-tgi-server.com/generate`

4. **TGI Response:**
   ```json
   {
     "generated_text": "Hi there! How can I help you today?",
     "details": {
       "finish_reason": "stop_sequence",
       "generated_tokens": 12,
       "prefill": [...]
     }
   }
   ```

5. **Response Mapper** (`chatAnsTGItoOpenAI`):
   ```json
   {
     "id": "chatcmpl-abc123...",
     "object": "chat.completion",
     "created": 1700000000,
     "model": "Unknown",
     "choices": [{
       "index": 0,
       "message": {
         "role": "assistant",
         "content": "Hi there! How can I help you today?"
       },
       "finish_reason": "stop"
     }],
     "usage": {
       "prompt_tokens": 24,
       "completion_tokens": 12,
       "total_tokens": 36
     }
   }
   ```

6. **Sent back to client** (looks like OpenAI response!)

---

## Performance Characteristics

### Latency Breakdown

```
Total Latency = L_proxy + L_network + L_backend

L_proxy = L_auth + L_parse + L_map + L_prompt + L_serialize
  - L_auth: < 1ms (dict lookups)
  - L_parse: 1-5ms (JSON parsing)
  - L_map: 1-10ms (dict operations)
  - L_prompt: 1-20ms (string building)
  - L_serialize: 1-5ms (JSON encoding)
  Total: ~5-40ms overhead

L_network: Round-trip to backend (varies)
L_backend: Backend API processing time (varies)
```

**Typical Overhead:** 10-50ms per request

### Scalability

**Current Architecture:**
- `ThreadingHTTPServer`: One thread per request
- Synchronous request handling
- In-memory state (Cerbere blacklist)

**Limitations:**
- Thread count limited by system resources
- No horizontal scaling (in-memory state)
- No request queueing or backpressure

**Capacity Estimate:**
- Low traffic: < 100 req/sec
- Not designed for production scale

**Scaling Recommendations:**
1. Deploy behind load balancer
2. Use connection pooling
3. Consider async rewrite for higher throughput
4. Move state to Redis/Memcached for multi-instance

---

*Documentation Version: 1.0*
*Last Updated: 2025-11-22*
*Corresponds to Codebase Commit: aa8dc46*
