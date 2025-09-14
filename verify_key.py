from anthropic import Anthropic # type: ignore
import sys

def verify_key(api_key):
    print("\nTesting API key...")
    print(f"Key format: {api_key[:12]}...")  # Show just the beginning
    
    if not api_key.startswith('sk-ant-'):
        print("Error: API key should start with 'sk-ant-'")
        return False
        
    try:
        # Initialize client
        client = Anthropic(api_key=api_key)
        
        # Make a simple test request
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=10,
            messages=[{
                "role": "user",
                "content": "Say hello"
            }]
        )
        
        print("Success! API key is valid.")
        print(f"Test response: {response.content}")
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    # Get API key from command line
    print("Please paste your API key (it should start with 'sk-ant-'):")
    api_key = input().strip()
    
    verify_key(api_key)