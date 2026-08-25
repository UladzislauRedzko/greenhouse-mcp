#!/usr/bin/env python3
"""
Simple test script to verify the Greenhouse MCP server is working.
This tests that the server can be imported and initialized.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def check_import():
    """Test that we can import the MCP server."""
    try:
        from src.greenhouse_mcp import mcp

        _ = mcp
        print("✅ Successfully imported MCP server")
        return True
    except ImportError as e:
        print(f"❌ Failed to import MCP server: {e}")
        return False


def check_tools_registered():
    """Test that tools are registered."""
    try:
        import asyncio

        from src.greenhouse_mcp import mcp

        async def check_tools():
            tools = await mcp.list_tools()
            return tools

        # Run async function
        tools = asyncio.run(check_tools())

        print(f"✅ Found {len(tools)} tools registered:")

        expected_tools = [
            "list_jobs",
            "get_job",
            "list_candidates",
            "get_candidate",
            "create_candidate",
            "update_candidate",
            "list_applications",
            "list_all_applications",
            "sourcing_report",
            "get_application",
            "advance_application",
            "reject_application",
            "add_note_to_candidate",
            "add_note_to_application",
            "list_departments",
            "list_offices",
            "list_users",
        ]

        # Get tool names from the registered tools
        tool_names = [
            tool.name if hasattr(tool, "name") else str(tool) for tool in tools
        ]

        for name in tool_names:
            print(f"   - {name}")

        missing_tools = [t for t in expected_tools if t not in tool_names]

        if missing_tools:
            print(f"⚠️  Missing expected tools: {missing_tools}")
            return False

        return True
    except Exception as e:
        print(f"❌ Failed to list tools: {e}")
        return False


def check_env():
    """Test environment variable configuration."""
    client_id = os.getenv("GREENHOUSE_CLIENT_ID")
    client_secret = os.getenv("GREENHOUSE_CLIENT_SECRET")
    access_token = os.getenv("GREENHOUSE_ACCESS_TOKEN")

    if client_id and client_secret:
        print(f"✅ GREENHOUSE_CLIENT_ID is set (length: {len(client_id)} chars)")
        print(
            f"✅ GREENHOUSE_CLIENT_SECRET is set (length: {len(client_secret)} chars)"
        )
        return True
    elif access_token:
        print(f"✅ GREENHOUSE_ACCESS_TOKEN is set (length: {len(access_token)} chars)")
        return True
    else:
        print("⚠️  Greenhouse Harvest v3 credentials are not set")
        print(
            "   Set GREENHOUSE_CLIENT_ID and GREENHOUSE_CLIENT_SECRET "
            "in .env or environment"
        )
        return None  # Warning, not failure


def main():
    """Run all tests."""
    print("Testing Greenhouse MCP Server...\n")

    results = []

    # Test imports
    results.append(check_import())

    # Test tools
    if results[-1]:  # Only test tools if import succeeded
        results.append(check_tools_registered())

    # Test environment
    env_result = check_env()
    if env_result is not None:
        results.append(env_result)

    print("\n" + "=" * 50)

    if all(results):
        print("✅ All tests passed! Server is ready to use.")
        print("\nTo run the server:")
        print("  fastmcp run src.greenhouse_mcp:mcp")
        print("\nOr with Python:")
        print("  python -m src.greenhouse_mcp")
        return 0
    elif any(r is False for r in results):
        print("❌ Some tests failed. Please check the errors above.")
        return 1
    else:
        print("⚠️  Server is functional but needs configuration.")
        print(
            "Please set GREENHOUSE_CLIENT_ID and GREENHOUSE_CLIENT_SECRET "
            "in your .env file."
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())
