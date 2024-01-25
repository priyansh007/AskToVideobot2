import streamlit as st
from pathlib import Path
import source
import os

def show_dropdown(bucket_file_list):
    options = [item for item in bucket_file_list if ".txt" in item]
    default = st.session_state.get("selected_option", options[0])
    selected_option = st.selectbox("Select Transcribe files", options, index=options.index(default))
    if selected_option != default:
        st.session_state.chat_history = []
    st.session_state["selected_option"] = selected_option
    return selected_option

def show_dropdown_models(modelmap):
    options = [item for item in modelmap.keys()]
    default = st.session_state.get("selected_option_model", options[0])
    selected_option = st.selectbox("Select LLM model", options, index=options.index(default))
    st.session_state["selected_option_model"] = selected_option
    return modelmap[selected_option]

def show_video(transcribe_local_path,selected_option):
    video_local_path = transcribe_local_path.replace(".txt", ".mp4")
    video_cloud_path = selected_option.replace(".txt", ".mp4")
    if not os.path.exists(video_local_path):
        source.download_from_s3(video_cloud_path, video_local_path, s3_bucket)
    with open(video_local_path, "rb") as file:
        bytes = file.read()
        st.video(bytes)
    
    
def ask_LLM(content, modelId):
    chat_history = st.session_state.get("chat_history", [])
    with st.form(key='user_input_form'):
        user_query = st.text_input("Enter your query:")
        submit_button = st.form_submit_button(label='Ask LLM')

    # Button to trigger the ask_llm function
    if submit_button:
        with st.spinner("Analyzing..."):
            llm_response = source.llm_bot(content,isChatBot=True,query=user_query, modelId = modelId)
        chat_history.append({"user": user_query, "llm": llm_response})
        st.session_state.chat_history = chat_history
        st.text_area("Answer:",value=llm_response, height=500, max_chars=None)
        st.subheader("Chat History")
        for entry in chat_history:
            st.markdown(f"User: {entry['user']}")
            st.markdown(f"LLM: {entry['llm']}")
            st.text("-----------"*5)     

def show_main_dashboard(modelmap,s3_bucket="speech-to-text-meetsummarizar",
                        output_folder = "SpeechToText",
                        user_folder = "defaultUser2"):
   
    os.makedirs(output_folder, exist_ok=True)
    temp_path = os.path.join(output_folder,user_folder)
    os.makedirs(temp_path, exist_ok=True)
    bucket_file_list = source.list_files_in_folder(s3_bucket, user_folder)
    st.title("ScrumBot")   
    
    options = ["Upload", "Analyze","Summarize"]
    default_option_index = 0 
    option_selected = st.radio("Select an action", options, index=default_option_index)

    if option_selected == "Upload":
        uploaded_file = st.file_uploader("Choose a video file or txt file", type=["mp4", "mp3", "wav", "flac","ogg","amr","webm", "txt"])
        if uploaded_file is not None:
            source.delete_files_in_folder(temp_path)
            file_extension = Path(uploaded_file.name).suffix.lower()[1:]
            if file_extension not in ["mp4", "mp3", "wav", "flac","ogg","amr","webm", "txt"]:
                st.error("Unsupported file format. Please upload an mp3 | mp4 | wav | flac | ogg | amr | webm | txt file.")
            else:
                filename = uploaded_file.name
                txt_filename = filename[0:-4]+".txt"
                
                
                bytes = uploaded_file.read()
                st.video(bytes)
                file_path = os.path.join(temp_path,filename)
                with open(file_path, "wb") as file:
                    file.write(bytes)
                bucket_file_path=os.path.join(user_folder,filename)
                
                if bucket_file_path not in bucket_file_list:
                    with st.spinner("Uploading..."):
                        source.upload_to_s3(file_path, bucket_file_path, s3_bucket)
                if os.path.join(user_folder,txt_filename) not in bucket_file_list:
                    with st.spinner("Transcribing..."):
                        source.invoke_transcribe(path="s3://"+os.path.join(s3_bucket,bucket_file_path),
                                                job_name=user_folder+"_"+filename[0:-4],
                                                format=file_extension, 
                                                output_bucket=s3_bucket, 
                                                output_key=os.path.join(user_folder,txt_filename))
                    st.text_area("Message",value="Job has been scheduled please check Analyze or Summarize option after few minutes!!", height=50, max_chars=None)
                else:
                    st.text_area("Message",value="Our record shows that file is already uploaded to S3", height=50, max_chars=None)
                
                

    elif option_selected == "Analyze":
        try:
            
            selected_option = show_dropdown(bucket_file_list)
            transcribe_local_path = "./"+os.path.join(output_folder, selected_option)
            show_video(transcribe_local_path,selected_option)
            modelId = show_dropdown_models(modelmap)
            
            
            if not os.path.exists(transcribe_local_path):
                source.download_from_s3(selected_option, transcribe_local_path, s3_bucket)
            content = source.read_transcribe(transcribe_local_path)
            ask_LLM(content, modelId)
        except:
            st.text_area("Message",value="No files Found, wait for some more time", height=50, max_chars=None)
    else:
        try:
            selected_option = show_dropdown(bucket_file_list)
            transcribe_local_path = "./"+os.path.join(output_folder, selected_option)
            show_video(transcribe_local_path,selected_option)
            modelId = show_dropdown_models(modelmap)
            summary_filename = selected_option.replace(".txt", "_"+modelId+"_summary.txt")
            summary_file_local_path = os.path.join(output_folder, summary_filename)

            if os.path.exists(summary_file_local_path):
                with open(summary_file_local_path, "r") as content:
                    summary = content.read()
            else:
                with st.spinner("Summarizing..."):
                    if not os.path.exists(transcribe_local_path):
                        source.download_from_s3(selected_option, transcribe_local_path, s3_bucket)
                    content = source.read_transcribe(transcribe_local_path)
                    summary = source.llm_bot(content,modelId)
                with open(summary_file_local_path, "w") as file:
                    file.write(summary)
            st.subheader("Summary:")
            st.text_area("Details are from Claude LLM",value=summary, height=500, max_chars=None)
        except:
            st.text_area("Message",value="No files Found, wait for some more time", height=50, max_chars=None)


if __name__ == "__main__":  
    model_map = {"Claude Instant": "anthropic.claude-instant-v1",
                 "Claude V1": "anthropic.claude-v1", 
                 "Claude V2": "anthropic.claude-v2",
                 "Claude V2.1": "anthropic.claude-v2:1",}
    s3_bucket="speech-to-text-meetsummarizar"
    output_folder = "SpeechToText"
    user_folder = "defaultUser"
      

    show_main_dashboard(model_map,
                        s3_bucket,
                        output_folder,
                        user_folder
                        )

#1. User authorization 
#2. show video