import boto3
import json
import os
import shutil

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

def delete_folder(folder_path):
    try:
        shutil.rmtree(folder_path)
    except Exception as e:
        print(f"Error deleting folder '{folder_path}': {e}")
            