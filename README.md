# GridWise

Minimal Python 3.11 implementation for the BUP CSE Fest 2026 online preliminary.

## Read first

- Current progress and exact next step: [STATUS.md](STATUS.md)
- Runtime model preference and verification: [MODEL_PREFERENCE.md](MODEL_PREFERENCE.md)
- Build runbook: [../GPT-5.6-Sol-GridWise-Runbook.html](../GPT-5.6-Sol-GridWise-Runbook.html)
- Canonical problem statement: [../BUP_CSE_FEST_2026_Participant_Docs/BUP_CSE_FEST_2026_Preliminary_Problem_Statement_GridWise_LLM.pdf](../BUP_CSE_FEST_2026_Participant_Docs/BUP_CSE_FEST_2026_Preliminary_Problem_Statement_GridWise_LLM.pdf)
- Public cases: [../BUP_CSE_FEST_2026_Participant_Docs/BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json](../BUP_CSE_FEST_2026_Participant_Docs/BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json)

## Local commands

```powershell
uv venv --python 3.11 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
Copy-Item .env.example .env  # then set MERGE_API_KEY locally
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Verified gateway details

- Base URL: `https://api-gateway.merge.dev/v1/openai`
- Runtime choice: `gpt-5.6-luna`, effort `high`
- Strict structured output works. Every object in `response_format` must set `additionalProperties: false`; `uniqueItems` is rejected and must be enforced locally.
- Never commit `.env` or print the API key.
