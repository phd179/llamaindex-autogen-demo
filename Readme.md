This solution comprises 
# Tech Stack
- **LM Studio**
- **LlamaIndex**
- **RAG**
- **Autogen**

Setup the project
1. in the custom_agents folder, update agent1_template and agent2_template with instructions on how you want these two agents to interact. For example, you could have one agent generate code and another execute that code.

2. In the rag-docs folder, add some documents that you want to query against
3. If you want to use RAG, when you chat with the agent, include the word 'rag' in the task. This will : 
    - create a vector store locally on your machine from the documents provided
    - 