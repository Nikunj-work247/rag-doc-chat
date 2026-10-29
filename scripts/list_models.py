from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings
from dotenv import load_dotenv

load_dotenv()

print("=== CHAT MODELS ===")
for m in sorted(ChatNVIDIA.get_available_models(), key=lambda x: x.id):
    print(f"{m.id:70} tools={getattr(m, 'supports_tools', '?')} thinking={getattr(m, 'supports_thinking', '?')}")

print("\n=== EMBEDDING MODELS ===")
for m in sorted(NVIDIAEmbeddings.get_available_models(), key=lambda x: x.id):
    print(m.id)