# Greenhouse MCP Server 🌱

An MCP (Model Context Protocol) server for interacting with the Greenhouse Harvest API v3. This server enables AI agents to manage recruitment workflows through Greenhouse's applicant tracking system.

## Features

The Greenhouse MCP server provides tools for:

### Jobs Management
- `list_jobs` - List all jobs with filtering options
- `get_job` - Get detailed information about a specific job

### Candidate Management
- `list_candidates` - Search and list candidates
- `get_candidate` - Get detailed candidate information
- `create_candidate` - Add new candidates to the system
- `update_candidate` - Update existing candidate information
- `add_note_to_candidate` - Add notes to candidate profiles

### Application Tracking
- `list_applications` - List applications with filtering
- `get_application` - Get detailed application information
- `advance_application` - Move applications through hiring stages
- `reject_application` - Reject applications with reasons
- `add_note_to_application` - Add notes to applications

### Organization Data
- `list_departments` - List all departments
- `list_offices` - List all offices
- `list_users` - List Greenhouse users

## Installation

### Prerequisites
- Python 3.9+
- Greenhouse Harvest v3 OAuth credentials

### Install via pip
```bash
pip install greenhouse-mcp
```

### Install from source
```bash
git clone https://github.com/yourusername/greenhouse-mcp.git
cd greenhouse-mcp
pip install -e .
```

## Configuration

Create a `.env` file in your project root:

```env
GREENHOUSE_CLIENT_ID=your_client_id_here
GREENHOUSE_CLIENT_SECRET=your_client_secret_here

# Optional: Greenhouse user id used for request attribution.
# If omitted, Greenhouse uses the integration service user attached to the OAuth credentials.
GREENHOUSE_USER_ID=

# Optional defaults
GREENHOUSE_BASE_URL=https://harvest.greenhouse.io/v3
GREENHOUSE_AUTH_URL=https://auth.greenhouse.io/token
```

Do not commit `.env`. Client secrets and access tokens must stay local to each machine.

To create credentials in Greenhouse, create a Harvest V3 (OAuth) API credential and enable the scopes needed by this MCP server.

## Usage

### Running Locally with FastMCP

```bash
# Using FastMCP CLI
fastmcp run src.greenhouse_mcp:mcp

# Or with Python directly
python -m src.greenhouse_mcp
```

### Using with Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "greenhouse": {
      "command": "uvx",
      "args": ["greenhouse-mcp"],
      "env": {
        "GREENHOUSE_CLIENT_ID": "your_client_id_here",
        "GREENHOUSE_CLIENT_SECRET": "your_client_secret_here",
        "GREENHOUSE_USER_ID": "optional_user_id_here"
      }
    }
  }
}
```

### Using with MCPD

1. Install MCPD:
```bash
npm install -g @modelcontextprotocol/mcpd
```

2. Add the server to MCPD:
```bash
mcpd add greenhouse-mcp
```

3. Configure environment variables:
```bash
mcpd config args set greenhouse-mcp --env GREENHOUSE_CLIENT_ID=your_client_id_here
mcpd config args set greenhouse-mcp --env GREENHOUSE_CLIENT_SECRET=your_client_secret_here
```

4. Start the MCPD daemon:
```bash
mcpd daemon
```

The server will be available at `http://localhost:8090` with API documentation at `/docs`.

## Example Usage

Once connected to an AI assistant, you can use natural language to interact with Greenhouse:

```
"List all open engineering jobs"
"Show me candidates who applied in the last week"
"Get details for candidate ID 12345"
"Add a note to application 67890 saying 'Strong technical skills, schedule second interview'"
"Advance application 11111 to the next stage"
```

## API Rate Limiting

The server automatically handles Greenhouse API rate limits:
- Maximum 50 requests per 10 seconds
- Automatic retry with exponential backoff on rate limit errors
- Respects `Retry-After` headers

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/greenhouse-mcp.git
cd greenhouse-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Copy environment variables
cp .env.example .env
# Edit .env with your OAuth credentials
```

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black src/

# Lint
ruff check src/
```

## Security Notes

- Never commit your OAuth client secret, access token, or API credentials to version control
- Use environment variables or secure secret management
- The server only accepts connections from localhost by default
- All API requests use HTTPS

## Harvest API v3 Notes

- Authentication uses OAuth 2.0 Client Credentials.
- List endpoints use cursor-based pagination. The MCP tools still accept a `page` argument for compatibility, but the client follows Greenhouse `Link` headers internally.
- v3 read endpoints generally use list endpoints with an `ids` filter for single-record lookups.
- Application reports use `created_at`; v1's `applied_at` field is no longer used.
- Application attribution now exposes `referrer_id` instead of the old nested `credited_to` object.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

MIT License - see LICENSE file for details

## Support

For issues related to:
- This MCP server: Open an issue on GitHub
- Greenhouse API: Consult [Greenhouse Harvest API v3 documentation](https://harvestdocs.greenhouse.io/docs)
- MCP Protocol: Visit [Model Context Protocol docs](https://modelcontextprotocol.io)
- FastMCP: Check [FastMCP documentation](https://github.com/jlowin/fastmcp)
