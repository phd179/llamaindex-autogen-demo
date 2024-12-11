from typing import Dict, Optional, Union

from autogen import Agent, AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider
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
from llama_index.core.query_engine.retriever_query_engine import RetrieverQueryEngine

from dotenv import load_dotenv
import os 


agent1_description = "agent1"
agent2_description = "agent2"
MAX_ROUNDS = 5
MAX_CONSECUTIVE_AUTO_REPLY=5

index = None

async def load_index():
# load index
    try:
        # rebuild storage context
        storage_context = StorageContext.from_defaults(persist_dir="./storage")
        # load index
        index = load_index_from_storage(storage_context)
    except:
        Settings.embed_model = HuggingFaceEmbedding( model_name="BAAI/bge-small-en-v1.5");
        documents = SimpleDirectoryReader("./rag-docs").load_data(show_progress=True)
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist()   

@cl.on_chat_start
async def on_chat_start():    

    """Starts the agents on the task provided by the user."""
    #chat_profile = cl.user_session.get("chat_profile")
    settings = await cl.ChatSettings(
            [
                Select(
                    id="Model",
                    label="Open Source - Models",
                    values=["meta-llama-3-8b-instruct", "gemma-2-2b-it"],
                    initial_index=0,
                ),
                #Switch(id="Streaming", label="OpenAI - Stream Tokens", initial=True),
            ]).send()

    model_config_list = [
    {
        "model": "meta-llama-3-8b-instruct",
        "base_url": "http://localhost:1234/v1",
        "tags": ["local"],
        "api_key": "lm-studio",
    },
    {
        "model": "gemma-2-2b-it",
        "base_url": "http://localhost:1234/v1",
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
    model_name="meta-llama-3-8b-instruct",
    base_url="http://localhost:1234/v1",
    temperature=0,
)
    


    agent1 = ChainlitAssistantAgent(
        name=agent1_description,
        llm_config=llm_config,
        max_consecutive_auto_reply=MAX_CONSECUTIVE_AUTO_REPLY,
        system_message=template_list.agent1_template,
    )

    agent2 = ChainlitAssistantAgent(
        name=agent2_description,
        llm_config=llm_config,
        max_consecutive_auto_reply=MAX_CONSECUTIVE_AUTO_REPLY,
        system_message= template_list.agent2_template,
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
    cl.user_session.set(agent1_description, agent1)
    cl.user_session.set(agent2_description, agent2)

    msg = cl.Message(
        content=f"""Hi there! Enter a task to get started.""",
        # disable_human_feedback=True,
        author="user_proxy",
    )

    await msg.send()

    @cl.on_message
    async def on_message(message):
        CONTEXT = message.content
     
        portfolio_manager = cl.user_session.get(agent1)
        equity_research_analyst = cl.user_session.get(agent2)

        group_chat = GroupChat(
            agents=[user_proxy,  agent2, agent1],
            messages=[],
            max_round=MAX_ROUNDS,
            speaker_selection_method="round_robin",
            #max_retries_for_selecting_speaker=5,
        )

        manager = GroupChatManager(
            name="chat_manager",
            groupchat=group_chat,
            llm_config=llm_config,
            human_input_mode="NEVER",
            system_message="facilitator of the conversation between agents, ensuring the conversation finishes before the max rounds.",
        )
        
        
        if "rag" in CONTEXT:
            await load_index()
            await use_rag(llm, message)
        else:   
            await use_llm(group_chat, user_proxy, manager, CONTEXT)

async def use_rag(llm, message):

    #service_context 
    Settings.llm = llm
    Settings.num_output = 512
    Settings.context_window = 3900
    query_engine = index.as_query_engine(streaming=True, similarity_top_k=2)

    cl.user_session.set("query_engine", query_engine)

    query_engine = cl.user_session.get("query_engine")
    msg = cl.Message(content="", author="user_proxy")   
    res = await cl.make_async(query_engine.query)(message.content)

    for token in res.response_gen:
        await msg.stream_token(token)
    await msg.send()
     

async def use_llm(group_chat, user_proxy, manager, CONTEXT):
    if len(group_chat.messages) == 0:
        message = f"""Use the task provided by user input: {CONTEXT}"""
        await cl.Message(
        content="" #f"""starting agents on user defined task..."""
        ).send()
        await cl.make_async(user_proxy.initiate_chat)(
            manager,
             message=message,
        )
    elif len(group_chat.messages) < MAX_ROUNDS:
        print(group_chat.messages.count)
        await cl.make_async(user_proxy.send)(
            manager,
            message=CONTEXT,
            )
    elif len(group_chat.messages) == MAX_ROUNDS:
        await cl.make_async(user_proxy.send)(manager, message="exit")

if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)