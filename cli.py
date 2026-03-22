import json
from dotenv import load_dotenv
from llm_provider import LLMProviderFactory, MockProvider
from config import SYSTEM_PROMPT, get_provider_name

# Run with: python cli.py
# Load environment variables from .env file
load_dotenv()

print("🤖 Dobby Textile Design Assistant started (type 'exit' to quit)")
print(f"   Using provider: {get_provider_name()}\n")

# Initialize provider once before the loop
try:
    provider_name = get_provider_name()
    provider = LLMProviderFactory.get_provider(provider_name)
except Exception as e:
    print(f"Warning: Failed to initialize provider '{provider_name}': {e}")
    print("Falling back to MockProvider.")
    provider = MockProvider()

messages = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

def format_reply(reply: str) -> str:
    """Format the reply for human-readable output if it's valid JSON."""
    try:
        data = json.loads(reply)
        if isinstance(data, dict) and "design" in data:
            design = data.get("design", {})
            colors = data.get("colors", [])
            technical = data.get("technical", {})
            
            design_str = f"{design.get('designSize', 'Unknown')} | {design.get('weave', 'Unknown')} | {design.get('designStyle', 'Unknown')}"
            colors_str = ", ".join([f"{c.get('name', 'Unknown')} ({c.get('percentage', 0)}%)" for c in colors])
            technical_str = f"{technical.get('yarnCount', 'Unknown')} yarn | {technical.get('construction', 'Unknown')} | {technical.get('gsm', 'Unknown')} GSM"
            
            return f"Design: {design_str}\nColors: {colors_str}\nTechnical: {technical_str}"
        else:
            return reply
    except json.JSONDecodeError:
        return reply

while True:
    user_input = input("You: ")
    
    if user_input.lower() == "exit":
        print("Goodbye 👋")
        break
    
    messages.append({"role": "user", "content": user_input})
    
    try:
        reply = provider.get_response(messages)
        formatted_reply = format_reply(reply)
        print("Bot:", formatted_reply, "\n")
        messages.append({"role": "assistant", "content": reply})
    except Exception as e:
        print(f"Error getting response: {e}")
        print("Continuing conversation...\n")
        # Do not append the failed turn to messages