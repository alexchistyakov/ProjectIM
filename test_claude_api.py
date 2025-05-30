#!/usr/bin/env python3
"""
Simple test script to verify Claude API connection and basic functionality
"""

import asyncio
import os
from anthropic import AsyncAnthropic
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_api_connection():
    """Test basic API connection"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("❌ No ANTHROPIC_API_KEY found in environment")
        return False
    
    print(f"✅ API key found (length: {len(api_key)})")
    
    try:
        client = AsyncAnthropic(api_key=api_key)
        
        # Simple test message
        response = await client.messages.create(
            model="claude-3-sonnet-20240229",
            messages=[{"role": "user", "content": "Say 'Hello, API test successful!' if you can read this."}],
            max_tokens=50
        )
        
        print(f"✅ API Response received!")
        print(f"Response type: {type(response)}")
        print(f"Response content: {response.content}")
        
        # Try to access the content
        if hasattr(response, 'content'):
            for content_block in response.content:
                if hasattr(content_block, 'text'):
                    print(f"Text: {content_block.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ API Error: {type(e).__name__}: {str(e)}")
        return False

async def test_tool_use():
    """Test API with tool use"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = AsyncAnthropic(api_key=api_key)
    
    tools = [{
        "name": "test_tool",
        "description": "A test tool that returns a greeting",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name to greet"
                }
            },
            "required": ["name"]
        }
    }]
    
    try:
        response = await client.messages.create(
            model="claude-3-sonnet-20240229",
            messages=[{"role": "user", "content": "Use the test_tool to greet 'World'"}],
            tools=tools,
            max_tokens=200
        )
        
        print("\n✅ Tool use test:")
        print(f"Response type: {type(response)}")
        
        if hasattr(response, 'content'):
            for content_block in response.content:
                print(f"Content block type: {content_block.type if hasattr(content_block, 'type') else 'unknown'}")
                if hasattr(content_block, 'type'):
                    if content_block.type == "text":
                        print(f"Text: {content_block.text}")
                    elif content_block.type == "tool_use":
                        print(f"Tool: {content_block.name}")
                        print(f"Input: {content_block.input}")
        
        return True
        
    except Exception as e:
        print(f"❌ Tool use error: {type(e).__name__}: {str(e)}")
        return False

async def main():
    print("Testing Claude API Connection...\n")
    
    # Test basic connection
    if await test_api_connection():
        print("\n✅ Basic API test passed!")
        
        # Test tool use
        await test_tool_use()
    else:
        print("\n❌ Basic API test failed!")
        print("\nTroubleshooting:")
        print("1. Check that your .env file exists")
        print("2. Verify ANTHROPIC_API_KEY is set correctly")
        print("3. Ensure your API key is valid")

if __name__ == "__main__":
    asyncio.run(main()) 