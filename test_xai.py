#!/usr/bin/env python3
"""Test XAI connection"""

import os
import openai
from dotenv import load_dotenv

load_dotenv()

print('XAI_API_KEY present:', 'XAI_API_KEY' in os.environ)
xai_key = os.getenv("XAI_API_KEY")
print('XAI_API_KEY value (first 10 chars):', xai_key[:10] if xai_key else 'None')

print('Testing XAI connection directly...')

try:
    client = openai.OpenAI(
        api_key=xai_key,
        base_url="https://api.x.ai/v1"
    )
    
    response = client.chat.completions.create(
        model="grok-3-mini",
        messages=[
            {"role": "user", "content": "Hello, can you respond with just 'test successful'?"}
        ],
        max_tokens=10
    )
    
    print('✅ XAI connection successful!')
    print('Response:', response.choices[0].message.content)
    
except Exception as e:
    print('❌ XAI connection failed:', str(e))
    import traceback
    traceback.print_exc()
