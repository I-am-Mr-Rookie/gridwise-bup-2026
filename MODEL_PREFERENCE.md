# Project Runtime Model Preference

- Preferred application LLM: `gpt-5.6-luna`.
- Preferred reasoning-effort order: `high`, `xhigh`, `medium`, then `max`.
- Use the first supported combination in that order and verify it through the Merge gateway before deployment.
- Verified on 2026-09-18: `gpt-5.6-luna` with `high` returned the correct SAMPLE-01 directive interpretation using strict JSON schema.
