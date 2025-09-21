from summarizer.service import summarize

snippets = [
    {"node_id": "example.py:add", "code": "def add(a, b):\n    return a + b"}
]

resp = summarize("Explain this function", snippets)
print(resp.json(indent=2))
