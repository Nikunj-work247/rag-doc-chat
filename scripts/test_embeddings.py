import os
from concurrent.futures import ThreadPoolExecutor, wait

import requests
from dotenv import load_dotenv

load_dotenv()
from docchat.config import settings

URL = "https://integrate.api.nvidia.com/v1/embeddings"

CANDIDATES = [
    "nvidia/nemotron-3-embed-1b",
    "nvidia/nemotron-3.5-embed-1b",
    "nvidia/nemotron-3.5-embed-8b",
    "nvidia/llama-3.2-nv-embedqa-1b-v2",
    "nvidia/llama-3.2-nemoretriever-300m-embed-v2",
    "nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1",
    "nvidia/nv-embedqa-e5-v5",
    "nvidia/nv-embed-v1",
    "nvidia/embed-qa-4",
    "baai/bge-m3",
]


def test(model_id: str):
    try:
        r = requests.post(
            URL,
            headers={"Authorization": f"Bearer {settings.nvidia_api_key}"},
            json={
                "model": model_id,
                "input": ["hello world"],
                "input_type": "query",
                "encoding_format": "float",
            },
            timeout=40,
        )
        if r.ok:
            dim = len(r.json()["data"][0]["embedding"])
            return model_id, "OK", f"dimension={dim}"
        return model_id, "FAIL", f"{r.status_code} {r.text[:110]!r}"
    except Exception as e:
        return model_id, "FAIL", str(e)[:110]


pool = ThreadPoolExecutor(max_workers=len(CANDIDATES))
futures = [pool.submit(test, m) for m in CANDIDATES]
done, not_done = wait(futures, timeout=60)

print()
for f in sorted(done, key=lambda f: f.result()[0]):
    mid, status, info = f.result()
    print(f"{status:5} {mid}\n      {info}")
if not_done:
    print(f"\n{len(not_done)} model(s) did not answer within 60s")
os._exit(0)