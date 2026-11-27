# SKEMANYA Media Manager — AI Development Rules

## Gemini API
- Before changing Gemini API code, consult the `geminiDocs` MCP server (`gemini_search_docs` / `gemini_get_doc`). If unavailable, use https://aistudio.google.com/llms.txt and the official Markdown docs under https://aistudio.google.com/docs/.
- Follow the project skill at `.agents/skills/gemini-api-dev/SKILL.md`.
- Use the official JavaScript SDK `@google/genai`; do not use the legacy `@google/generative-ai` SDK.
- Use `client.interactions.create()` for new Gemini interactions unless a documented feature requires otherwise.
- Check current model availability at https://aistudio.google.com/docs/models before changing model IDs. Do not assume model names remain current.
- Keep `GEMINI_API_KEY` in Cloudflare Worker secrets. Never commit API keys, tokens, or credentials.
- Do not print secrets in logs or expose them to browser code.
- Run tests/build checks before claiming a change works.
