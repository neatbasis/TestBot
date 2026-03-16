# seem_bot

`seem_bot` is the modularized version of `examples/seem_bot.py`.

## Run from source tree

From repository root:

```bash
python -m seem_bot.cli
```

## Run via installed console script

After editable install:

```bash
pip install -e .[dev]
seem-bot
```

## Environment variables (optional)

- `SEEM_BOT_MODEL` or `OLLAMA_MODEL` (default: `llama3.2:3b`)
- `OLLAMA_BASE_URL` (default: `http://localhost:11434`)
- `X_OLLAMA_KEY` (optional)

If Ollama is unavailable, the renderer returns an offline fallback response.
