import anthropic

# Replace this with your actual API key, or set it as an environment variable

client = anthropic.Anthropic()

try:
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",  # Make sure this model is available in your account
        max_tokens=50,
        messages=[
            {"role": "user", "content": "Hello Claude, are you working?"}
        ]
    )
    print("✅ API Key is valid. Claude responded:")
    print(response.content[0].text)

except anthropic.AuthenticationError as e:
    print("❌ Invalid API key. Authentication failed.")
    print(e)

except Exception as e:
    print("⚠️ An error occurred:")
    print(e)    