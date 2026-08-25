#!/bin/bash

# Setup script for MCPD deployment of Greenhouse MCP Server

echo "🌱 Greenhouse MCP Server - MCPD Setup"
echo "======================================"
echo ""

# Check if MCPD is installed
if ! command -v mcpd &> /dev/null; then
    echo "❌ MCPD is not installed."
    echo "Please install it first: npm install -g @modelcontextprotocol/mcpd"
    exit 1
fi

# Check for OAuth credentials
if [ -z "$GREENHOUSE_CLIENT_ID" ] || [ -z "$GREENHOUSE_CLIENT_SECRET" ]; then
    echo "⚠️  GREENHOUSE_CLIENT_ID or GREENHOUSE_CLIENT_SECRET is not set in environment."
    echo "Please set them before running the server:"
    echo "  export GREENHOUSE_CLIENT_ID='your_client_id_here'"
    echo "  export GREENHOUSE_CLIENT_SECRET='your_client_secret_here'"
    echo ""
fi

# Add server to MCPD
echo "📦 Adding greenhouse-mcp to MCPD..."
mcpd add greenhouse-mcp

# Configure environment variables
echo "🔧 Configuring environment variables..."
if [ ! -z "$GREENHOUSE_CLIENT_ID" ]; then
    mcpd config args set greenhouse-mcp --env GREENHOUSE_CLIENT_ID="$GREENHOUSE_CLIENT_ID"
    echo "✅ GREENHOUSE_CLIENT_ID configured"
fi

if [ ! -z "$GREENHOUSE_CLIENT_SECRET" ]; then
    mcpd config args set greenhouse-mcp --env GREENHOUSE_CLIENT_SECRET="$GREENHOUSE_CLIENT_SECRET"
    echo "✅ GREENHOUSE_CLIENT_SECRET configured"
fi

if [ ! -z "$GREENHOUSE_USER_ID" ]; then
    mcpd config args set greenhouse-mcp --env GREENHOUSE_USER_ID="$GREENHOUSE_USER_ID"
    echo "✅ GREENHOUSE_USER_ID configured"
fi

# Optional: Set base URL if different from default
if [ ! -z "$GREENHOUSE_BASE_URL" ]; then
    mcpd config args set greenhouse-mcp --env GREENHOUSE_BASE_URL="$GREENHOUSE_BASE_URL"
    echo "✅ GREENHOUSE_BASE_URL configured"
fi

if [ ! -z "$GREENHOUSE_AUTH_URL" ]; then
    mcpd config args set greenhouse-mcp --env GREENHOUSE_AUTH_URL="$GREENHOUSE_AUTH_URL"
    echo "✅ GREENHOUSE_AUTH_URL configured"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the MCPD daemon:"
echo "  mcpd daemon"
echo ""
echo "API documentation will be available at:"
echo "  http://localhost:8090/docs"
echo ""
echo "To use with Claude Desktop, add to your config:"
echo '  {
    "mcpServers": {
      "greenhouse": {
        "url": "http://localhost:8090/greenhouse-mcp"
      }
    }
  }'
