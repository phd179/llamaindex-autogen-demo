**Overview**
A multi-agent application that leverages agents to solve specific tasks. Also, this solution has RAG based capablities when using the keyword 'rag' in the prompt. 

# Tech Stack
- **LM Studio**
- **LlamaIndex**
- **Autogen**
- **ChainlitUI**

**Prerequisites:**
1. Download & install LM Studio to your non-work machine 
    a. using LM Studio, the Developer tab on the left, start the Server, then load any model that you have downloaded
    b. update the variable named, default_llm_model in app.py with the name of the model loaded in LM Studio.  


**Setup the project**
1. Within the codebase, there is a file called template_list.py in the agent_templates folder. Update agent1_template and agent2_template with instructions on how you want these two agents to interact. For example, you could have one agent generate code and another execute that code.

2. In the rag-docs folder, add some documents that you want to query against. These documents will be vectorized at runtime if you use RAG. 

3. The default chat is a round-robin approach between the two agents, leveraging the model chosen in LM Studio. The agents will converse to come up with a solution to the task provided in the prompt. 

4. If you want to use RAG, when you chat with the agent, include the keyword 'rag' in the task. This will vectorize the documents in realtime(might take a couple of minutes) 


 