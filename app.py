from autogen import GroupChat, GroupChatManager
import chainlit as cl
from chainlit.input_widget import Select
from llama_index.core import (
    Settings,
    StorageContext,
    VectorStoreIndex,
    SimpleDirectoryReader,
    load_index_from_storage,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.lmstudio import LMStudio

from agent_templates import template_list
from custom_agents.customAssistantAgent import ChainlitAssistantAgent
from custom_agents.customUserProxyAgent import ChainlitUserProxyAgent

from dotenv import load_dotenv
import os

load_dotenv()

AGENT1_NAME = "agent1"
AGENT2_NAME = "agent2"
MAX_ROUNDS = 5
MAX_CONSECUTIVE_AUTO_REPLY = 5

# Cached LlamaIndex vector store index (loaded on first RAG request)
index = None

LM_STUDIO_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
DEFAULT_LLM_MODEL = os.getenv("LLM_MODEL", "meta-llama-3-8b-instruct")


async def load_index():
    """Load (or build) the LlamaIndex vector store from ./rag-docs."""
    global index
    if index is not None:
        return index
    try:
        storage_context = StorageContext.from_defaults(persist_dir="./storage")
        index = load_index_from_storage(storage_context)
    except (ValueError, FileNotFoundError):
        Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
        documents = SimpleDirectoryReader("./rag-docs").load_data(show_progress=True)
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist()
    return index


@cl.on_chat_start
async def on_chat_start():
    """Initialise agents and store them in the user session."""
    await cl.ChatSettings(
        [
            Select(
                id="Model",
                label="Open Source - Models",
                values=[DEFAULT_LLM_MODEL],
                initial_index=0,
            ),
        ]
    ).send()

    model_config_list = [
        {
            "model": DEFAULT_LLM_MODEL,
            "base_url": LM_STUDIO_URL,
            "tags": ["local"],
            "api_key": "lm-studio",
        },
    ]

    llm_config = {
        "temperature": 0,
        "config_list": model_config_list,
        "timeout": 600,
    }

    llm = LMStudio(
        model_name=DEFAULT_LLM_MODEL,
        base_url=LM_STUDIO_URL,
        temperature=0,
    )

    agent1 = ChainlitAssistantAgent(
        name=AGENT1_NAME,
        llm_config=llm_config,
        max_consecutive_auto_reply=MAX_CONSECUTIVE_AUTO_REPLY,
        system_message=template_list.agent1_template,
    )

    agent2 = ChainlitAssistantAgent(
        name=AGENT2_NAME,
        llm_config=llm_config,
        max_consecutive_auto_reply=MAX_CONSECUTIVE_AUTO_REPLY,
        system_message=template_list.agent2_template,
    )

    user_proxy = ChainlitUserProxyAgent(
        name="user_proxy",
        code_execution_config={
            "work_dir": "workspace",
            "use_docker": False,
        },
        human_input_mode="NEVER",
    )

    cl.user_session.set("user_proxy", user_proxy)
    cl.user_session.set("llm", llm)
    cl.user_session.set("llm_config", llm_config)
    cl.user_session.set(AGENT1_NAME, agent1)
    cl.user_session.set(AGENT2_NAME, agent2)

    await cl.Message(
        content="Hi there! Enter a task to get started. Prefix your message with **rag** to query your documents instead.",
        author="user_proxy",
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Route each user message to either the RAG pipeline or the multi-agent LLM pipeline."""
    CONTEXT = message.content

    user_proxy = cl.user_session.get("user_proxy")
    llm = cl.user_session.get("llm")
    llm_config = cl.user_session.get("llm_config")
    agent1 = cl.user_session.get(AGENT1_NAME)
    agent2 = cl.user_session.get(AGENT2_NAME)

    group_chat = GroupChat(
        agents=[user_proxy, agent2, agent1],
        messages=[],
        max_round=MAX_ROUNDS,
        speaker_selection_method="round_robin",
    )

    manager = GroupChatManager(
        name="chat_manager",
        groupchat=group_chat,
        llm_config=llm_config,
        human_input_mode="NEVER",
        system_message=(
            "Facilitator of the conversation between agents. "
            "Ensure the conversation concludes before the max rounds are reached."
        ),
    )

    if CONTEXT.lower().startswith("rag"):
        loaded_index = await load_index()
        await use_rag(llm, loaded_index, message)
    else:
        await use_llm(group_chat, user_proxy, manager, CONTEXT)


async def use_rag(llm, loaded_index, message: cl.Message):
    """Query the vector index and stream the response back to the user."""
    Settings.llm = llm
    Settings.num_output = 512
    Settings.context_window = 3900

    query_engine = loaded_index.as_query_engine(streaming=True, similarity_top_k=2)
    msg = cl.Message(content="", author="user_proxy")
    res = await cl.make_async(query_engine.query)(message.content)

    for token in res.response_gen:
        await msg.stream_token(token)
    await msg.send()


async def use_llm(group_chat: GroupChat, user_proxy, manager: GroupChatManager, CONTEXT: str):
    """Drive the multi-agent group chat with the user's task."""
    if len(group_chat.messages) == 0:
        task_message = f"Use the task provided by the user: {CONTEXT}"
        await cl.Message(content="").send()
        await cl.make_async(user_proxy.initiate_chat)(
            manager,
            message=task_message,
        )
    elif len(group_chat.messages) < MAX_ROUNDS:
        await cl.make_async(user_proxy.send)(
            manager,
            message=CONTEXT,
        )
    else:
        await cl.make_async(user_proxy.send)(manager, message="exit")


if __name__ == "__main__":
    from chainlit.cli import run_chainlit

    run_chainlit(__file__)