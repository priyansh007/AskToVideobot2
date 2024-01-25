import boto3
from langchain.chains import LLMChain
from langchain.llms.bedrock import Bedrock
from langchain.prompts import PromptTemplate
import json
import os
def download_from_s3(key, local_file, bucket="speech-to-text-meetsummarizar"):
    s3_client = boto3.client("s3")
    s3_client.download_file(bucket, key, local_file)

def upload_to_s3(local_file, key, bucket="speech-to-text-meetsummarizar"):
    s3_client = boto3.client("s3")
    s3_client.upload_file(local_file, bucket, key)

def list_files_in_folder(bucket, folder_name):
    s3_client = boto3.client("s3")
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=folder_name)
    file_names = [obj['Key'] for obj in response.get('Contents', [])]
    return file_names

def invoke_transcribe(path,job_name,format, output_bucket, output_key):
    client = boto3.client('transcribe')
    _ = client.start_transcription_job(
    TranscriptionJobName=job_name,
    MediaFormat=format,
    Media={
        'MediaFileUri': path
    },
    OutputBucketName=output_bucket,
    OutputKey=output_key,
    IdentifyMultipleLanguages=True)

def read_transcribe(transcribe_local_path):
    try:
        with open(transcribe_local_path, "r") as content:
            obj = json.loads(content.read())
            content = obj["results"]["transcripts"][0]["transcript"]
        return content
    except (json.JSONDecodeError, FileNotFoundError):
        with open(transcribe_local_path, "r") as content:
            return content.read()

def delete_files_in_folder(folder_path):
    try:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting file '{file_path}': {e}")
        print(f"All files in folder '{folder_path}' deleted successfully.")
    except Exception as e:
        print(f"Error deleting files in folder '{folder_path}': {e}")

def llm_bot(content,
            isChatBot=False,
            query="",
            modelId = "anthropic.claude-v2"):
        
        bedrock_client = boto3.client(
            service_name = "bedrock-runtime",
            region_name="us-east-1"
        )

        llm = Bedrock(model_id=modelId,
                    client=bedrock_client,
                    model_kwargs={"temperature":0.9}
                    )
        if isChatBot:
            template = "You are a Scrum master/Project Manager bot who has knowledge of all scrum ceremonies and best practices. Using this meeting transcribe context: {transcribe}, answer this question: {query}"
        else:
            template="You are a scrum master bot who has knowledge of all scrum ceremonies and best practices. Your job is to find To-Do task, Roadblockers and Action Item from the transcribe of a meeting. If Assignee is mentioned in transcribe please incluse name as well. At the end of your answer please include the summary of meeting. Transcribe is {transcribe}"
        

        prompt = PromptTemplate(
            input_variables=["transcribe","query"],
            template=template
            )
        
        bedrock_chain = LLMChain(llm=llm, prompt=prompt)

        response=bedrock_chain({'transcribe':content, 'query': query})
        return response['text']