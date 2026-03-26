# LlamaIndex + AutoGen Demo

A multi-agent chat application where two AI agents collaborate to solve tasks.
It also supports **RAG** (Retrieval-Augmented Generation) for querying your own documents,
all powered by a locally-running LLM served through **LM Studio**.

## Tech Stack

| Tool | Purpose |
|------|---------|
| [LM Studio](https://lmstudio.ai/) | Serves open-source LLMs locally via an OpenAI-compatible API |
| [AutoGen](https://microsoft.github.io/autogen/) | Orchestrates the multi-agent conversation |
| [LlamaIndex](https://docs.llamaindex.ai/) | Handles document ingestion, embedding, and RAG querying |
| [Chainlit](https://docs.chainlit.io/) | Provides the chat UI |

---

## Prerequisites

1. **Python 3.11 or 3.12** installed.
2. **[Poetry](https://python-poetry.org/docs/#installation)** installed for dependency management.
3. **LM Studio** installed on your machine.
   - Open LM Studio, go to the **Developer** tab, and start the local server.
   - Download and load a model (e.g. `meta-llama-3-8b-instruct`).

---

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd llamaindex-autogen-demo
```

### 2. Install Python dependencies

```bash
poetry install
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set `LLM_MODEL` to the exact model name shown in LM Studio,
and `LM_STUDIO_BASE_URL` if your server runs on a different address.

### 4. Customize the agent prompts

Open `agent_templates/template_list.py` and update `agent1_template` and
`agent2_template` with system-message instructions suited to your use case.

The default setup pairs a **code-writer** with a **code-reviewer**.

### 5. (Optional) Add documents for RAG

Drop `.txt`, `.pdf`, or `.md` files into the `rag-docs/` folder.
These will be embedded the first time you send a message that starts with `rag`.

---

## Running the App

```bash
poetry run chainlit run app.py -w
```

The `-w` flag enables auto-reload on file changes.
Open your browser at [http://localhost:8000](http://localhost:8000).

---

## Usage

### Multi-agent mode (default)

Type any task in the chat and the two agents will collaborate in a round-robin
conversation to produce a solution.

### RAG mode

Prefix your message with **rag** to query documents in `rag-docs/` instead:

```
rag summarise the key points of the attached report
```

> **Note:** The first RAG request triggers document embedding, which may take a
> couple of minutes depending on the number and size of your documents. The
> resulting index is cached in `storage/` for subsequent runs.

---

## Project Structure

```
.
├── agent_templates/
│   └── template_list.py   # Edit agent system-message prompts here
├── custom_agents/
│   ├── customAssistantAgent.py   # Chainlit-aware AutoGen AssistantAgent
│   └── customUserProxyAgent.py  # Chainlit-aware AutoGen UserProxyAgent
├── rag-docs/              # Place your documents here for RAG
├── workspace/             # AutoGen code-execution sandbox (git-ignored)
├── storage/               # LlamaIndex persisted vector store (git-ignored)
├── app.py                 # Main application entry point
├── chainlit.md            # Chainlit welcome-screen content
├── .env.example           # Example environment variables (copy to .env)
└── pyproject.toml         # Python dependencies (managed by Poetry)
```
