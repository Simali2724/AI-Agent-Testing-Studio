# Change an API key

The Studio judge and the chatbot being tested have separate keys. Changing the judge key does not change the chatbot's model provider.

## Easiest option: change the judge on screen

Open Studio, select **Evaluate**, then **Choose your judge**. Open **Model and key**, enter the provider's model ID and API key, and select that judge. For a running evaluation, use **Apply judges to active run**. Keys entered here apply to that run; they are not written into the project `.env` or copied into reports.

## Save the Studio judge key locally

Edit `.env` in the Studio project root. On this PC it is `D:\AI-Agent-Testing-Studio\.env`.

| Setting                | Meaning                                       |
| ---------------------- | --------------------------------------------- |
| `STUDIO_JUDGE_API_KEY` | The selected judge provider's API key         |
| `STUDIO_JUDGE_MODEL`   | A model ID available to your provider account |
| `STUDIO_JUDGE_URL`     | The endpoint for that same judge provider     |

Keep the provider, model and endpoint consistent. Use the on-screen provider choices if you are unsure of an endpoint. Restart the Studio backend after editing `.env`, when no evaluation is active. Explicit on-screen judge selections override saved defaults. An environment variable already set in the launching terminal also takes precedence over `.env`; update or remove that old value if the change does not appear.

An optional `STUDIO_JUDGE_ENV_FILE` can point to a separate local credentials file. `STUDIO_JUDGE_KEY_NAME` chooses its key variable (default `GOOGLE_API_KEY`). A nonempty `STUDIO_JUDGE_API_KEY` takes priority. Most users can use the main `.env` and leave this advanced option unused.

## Change the Reliance chatbot's provider key

Edit `D:\reliance-project\backend\.env`, then restart the Reliance backend. Its source reads these names:

| Provider              | Key variable        | Model variable                 |
| --------------------- | ------------------- | ------------------------------ |
| Gemini / hosted Gemma | `GOOGLE_API_KEY`    | `GEMINI_MODEL` / `GEMMA_MODEL` |
| OpenAI                | `OPENAI_API_KEY`    | `OPENAI_MODEL`                 |
| Claude                | `ANTHROPIC_API_KEY` | `CLAUDE_MODEL`                 |
| Local Ollama          | No provider API key | `OLLAMA_MODEL`                 |

For Reliance, use `GOOGLE_API_KEY` for Gemini, not `GEMINI_API_KEY`. Set the requested provider in the chatbot as well; adding a key alone does not change an explicitly selected provider. Another chatbot may use a different configuration file; follow that chatbot's `.env.example`.

In Studio, a bot card's **Advanced connection settings → API key** authenticates requests to that chatbot's API. It does not update the cloud key inside the chatbot server.

Do not edit the Python source to rotate a key. Keep real keys in local `.env` files or password fields; `.env.example` contains placeholders and is safe to share.

## Where the testing code lives

| Mode                                                                       | Main files                                           |
| -------------------------------------------------------------------------- | ---------------------------------------------------- |
| Black-box: tests responses through chat/API                                | `app/assurance/black.py`, `app/blackbox/runner.py`   |
| Gray-box: uses supplied instructions, knowledge and traces to guide checks | `app/assurance/gray.py`, `app/studio/gray-v1.json`   |
| White-box: isolated read-only source scanning                              | `app/assurance/white.py`, `app/assurance/sandbox.py` |

The local files and the GitHub `master` branch use the same paths.
