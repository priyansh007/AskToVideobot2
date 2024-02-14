import streamlit as st
from langchain.llms.bedrock import Bedrock
from langchain.chains import ConversationChain
from langchain.schema import HumanMessage,SystemMessage,AIMessage
import boto3
from langchain.chains import LLMChain
from langchain.llms.bedrock import Bedrock
from langchain.prompts import PromptTemplate
def llm_bot(modelId):
    bedrock_client = boto3.client(
            service_name = "bedrock-runtime",
            region_name="us-east-1"
        )

    llm = Bedrock(model_id=modelId,
                  client=bedrock_client,
                    model_kwargs={"temperature":0.8,
                                  "max_tokens_to_sample": 1000}
                    )
    return llm
      
def conversation_bot(file_name,
                     transcribe,
                     query,
                     modelId = "anthropic.claude-v2"):
        
        llm = llm_bot(modelId)
        if file_name not in st.session_state:
            st.session_state[file_name]=[
                SystemMessage(content= """You are a Scrum bot assitant who understands meeting transcribe 
                              and reply to user as scrum master or project manager, If answer is not related to 
                              transcribe you can answer as normal chat bot. 
                              You can use following transcribe for answering the question: """+str(transcribe))
            ]

        st.session_state[file_name].append(HumanMessage(content=query))
        llm_chain = ConversationChain(verbose=True, llm=llm)
        answer=llm_chain(st.session_state[file_name])['response']
        st.session_state[file_name].append(AIMessage(content=answer))
        return answer

def summarizer_bot(transcribe,
                   modelId = "anthropic.claude-v2"):
    llm = llm_bot(modelId)
    template="""You are a Scrum bot who has knowledge of all scrum ceremonies and best practices.
    Your job is to find To-Do task, Roadblockers and Action Item from the transcribe of a meeting. 
    If Assignee is mentioned in transcribe please incluse name as well. 
    At the end of your answer please include the summary of meeting. 
    Transcribe is {transcribe}"""
        

    prompt = PromptTemplate(
        input_variables=["transcribe"],
        template=template
        )
    bedrock_chain = LLMChain(llm=llm, prompt=prompt)
    response=bedrock_chain({'transcribe':transcribe})
    return response['text']