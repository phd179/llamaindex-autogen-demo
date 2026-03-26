# Welcome to the LlamaIndex + AutoGen Demo 🤖🦙

This app lets two AI agents collaborate to solve any task you give them — powered by a locally-running LLM via **LM Studio**.

## Getting Started 🚀

1. Make sure **LM Studio** is running and a model is loaded (Developer → Start Server).
2. Type a task in the chat box and watch the agents work together.

## RAG Mode 📄

Prefix your message with **rag** to query your own documents instead of using the multi-agent pipeline.

> Example: `rag what does the report say about Q3 revenue?`

Documents are loaded from the `rag-docs/` folder. Drop any `.txt`, `.pdf`, or `.md` files there before starting the app.

## Customizing the Agents 🛠️

Edit `agent_templates/template_list.py` to change what each agent does.
The default setup is a **code-writer** (agent1) paired with a **code-reviewer** (agent2).

## Useful Links 🔗

- [LM Studio](https://lmstudio.ai/)
- [LlamaIndex Docs](https://docs.llamaindex.ai/)
- [AutoGen Docs](https://microsoft.github.io/autogen/)
- [Chainlit Docs](https://docs.chainlit.io/)
