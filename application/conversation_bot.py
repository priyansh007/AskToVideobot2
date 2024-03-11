import streamlit as st
from langchain.llms.bedrock import Bedrock
from langchain.chains import ConversationChain
from langchain.schema import HumanMessage,SystemMessage,AIMessage
import boto3
from langchain.chains import LLMChain
from langchain.llms.bedrock import Bedrock
from langchain.prompts import PromptTemplate
from langchain.chains import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.chat_models import BedrockChat

def llm_bot(modelId):
    bedrock_client = boto3.client(
            service_name = "bedrock-runtime",
            region_name="us-east-1"
        )
    model_kwargs={"temperature":0.8,
                "max_tokens": 1000}
    model = BedrockChat(
        client=bedrock_client,
        model_id=modelId,
        model_kwargs=model_kwargs,
    )
    return model
      
def conversation_bot(file_name,
                     transcribe,
                     query,
                     modelId = "anthropic.claude-v2"):
        
        llm = llm_bot(modelId)
        if file_name not in st.session_state:
            st.session_state[file_name]=[
                SystemMessage(content= """You are a Scrum bot assitant who understands meeting transcribe 
                              and reply to user as scrum master or project manager, If question is not related to 
                              transcribe you can say that question is not related to transcribe instead of answering out of content context. 
                              You can use following meeting transcribe for answering the question: """+str(transcribe))
            ]

        st.session_state[file_name].append(HumanMessage(content=query))
        llm_chain = ConversationChain(verbose=True, llm=llm)
        answer=llm_chain(st.session_state[file_name])['response']
        st.session_state[file_name].append(AIMessage(content=answer))
        return answer

def summarizer_bot(transcribe,
                   modelId = "anthropic.claude-v2"):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.create_documents([transcribe])
    
    chunks_prompt="""
    Please summarize the below speech:
    Speech:`{text}'
    Summary:
    """
    map_prompt_template=PromptTemplate(input_variables=['text'],
                                            template=chunks_prompt)
    
    final_combine_prompt="""You are a Scrum bot who has knowledge of all scrum ceremonies and best practices.
    Your job is to find To-Do task, Roadblockers and Action Item from the transcribe of a meeting. (It is just one transcribe) 
    If Assignee is mentioned in transcribe please incluse name as well. 
    At the end of your answer please Provide a final summary of the meeting. 
    Transcribe: {text}"""


    final_combine_prompt_template=PromptTemplate(input_variables=['text'],
                                                template=final_combine_prompt)
    
    llm = llm_bot(modelId)

    summary_chain = load_summarize_chain(
        llm=llm,
        chain_type='map_reduce',
        map_prompt=map_prompt_template,
        combine_prompt=final_combine_prompt_template,
        verbose=False
    )
    output = summary_chain.run(chunks)
    return output