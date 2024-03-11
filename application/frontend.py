import streamlit as st
from pathlib import Path
import source
import os
from video import video_file
from conversation_bot import conversation_bot
from conversation_bot import summarizer_bot

def show_dropdown(bucket_file_list):
    options = [item for item in bucket_file_list if ".txt" in item]
    default = st.session_state.get("selected_option", options[0])
    selected_option = st.sidebar.selectbox("Select previously uploaded files", options, index=options.index(default))
    if selected_option != default:
        st.session_state.chat_history = []
    st.session_state["selected_option"] = selected_option
    return selected_option

def show_dropdown_models(modelmap):
    options = [item for item in modelmap.keys()]
    default = st.session_state.get("selected_option_model", options[0])
    selected_option = st.sidebar.selectbox("Select LLM model", options, index=options.index(default))
    if selected_option != default:
        st.session_state.chat_history = []
    st.session_state["selected_option_model"] = selected_option
    return modelmap[selected_option]

def show_video(selected_option, 
               local_folder, 
               bucket_file_list):
    file_name = selected_option.replace(".txt","")
    video_file = [item for item in bucket_file_list if item.startswith(file_name) and not item.endswith('.txt')]
    if len(video_file) != 0:
        video_local_path = "./"+os.path.join(local_folder, video_file[0])
        if not os.path.exists(video_local_path):
            source.download_from_s3(video_file[0], video_local_path, s3_bucket)
        with open(video_local_path, "rb") as file:
            bytes = file.read()
            try:
                st.video(bytes)
            except:
                st.audio(bytes)
    else:
        transcribe_local_path = "./"+os.path.join(local_folder, selected_option)
        if not os.path.exists(transcribe_local_path):
            source.download_from_s3(selected_option, transcribe_local_path, s3_bucket)
        with open(transcribe_local_path, "rb") as file:
            bytes = file.read()
        txt_content = bytes.decode('utf-8')
        st.text_area("Transcribe",value=txt_content, height=200, max_chars=None)

def handle_upload_functionality(uploaded_video_file, 
                                uploaded_file,
                                bucket_file_list):
    bytes = uploaded_file.read()
                
    if uploaded_video_file.file_extension == "mp4":
        st.video(bytes)
        with open(uploaded_video_file.local_file_path, "wb") as file:
            file.write(bytes)
    elif uploaded_video_file.file_extension in ["mp3", "wav", "flac", "ogg", "amr"]:
        st.audio(bytes)
        with open(uploaded_video_file.local_file_path, "wb") as file:
            file.write(bytes)
    elif uploaded_video_file.file_extension == "txt":
        txt_content = bytes.decode('utf-8')
        st.text_area("Transcribe",value=txt_content, height=200, max_chars=None)
        with open(uploaded_video_file.local_file_path, "w") as file:
            file.write(txt_content)
    else:
        st.warning(f"Unsupported file format: {uploaded_video_file.file_extension}")
    
    
    if uploaded_video_file.s3_file_path not in bucket_file_list:
        with st.spinner("Uploading..."):
            source.upload_to_s3(uploaded_video_file.local_file_path, 
                                uploaded_video_file.s3_file_path, 
                                s3_bucket)
    
    if (uploaded_video_file.transcribe_s3_path not in bucket_file_list 
        and uploaded_video_file.file_extension != "txt"):                    
        with st.spinner("Transcribing..."):
            source.invoke_transcribe(path="s3://"+os.path.join(s3_bucket,uploaded_video_file.s3_file_path),
                                    job_name=user_folder+"_"+uploaded_video_file.input_video_file_name[0:-4],
                                    format=uploaded_video_file.file_extension, 
                                    output_bucket=s3_bucket, 
                                    output_key=uploaded_video_file.transcribe_s3_path)
        st.success('''Great news! Your task has been scheduled. 
                   Feel free to check back in a few minutes—around the same time it takes to watch your input video. 
                   You can find them under the 'Q&A' or 'Summarize' options. Happy exploring!!!''')
    elif(uploaded_video_file.file_extension == "txt"):
        st.success("File Uploaded Successfully and Available to Analyze!!")
    else:
        st.warning(f"Our record shows that File already exists with our system. (Please use other sections for analyse or change the name of file.) ")
        
    
def ask_LLM(content, modelId, selected_option):
    chat_history = st.session_state.get("chat_history", [])
    

    with st.form(key='user_input_form'):
        user_query = st.text_input("Enter your query:")
        submit_button = st.form_submit_button(label='Ask to AI')

    # Button to trigger the ask_llm function
    if submit_button:
        
        with st.spinner("Analyzing..."):
            llm_response = conversation_bot(selected_option, 
                                            content,
                                            user_query,
                                            modelId)
        chat_history.append({"user": user_query, "llm": llm_response})
        st.session_state.chat_history = chat_history
        st.text_area("Answer:",value=llm_response, height=500, max_chars=None)

        if len(chat_history)!=0:
            with st.expander('History'):
                chat_container = st.container(border=False,height=600)
                with chat_container:
                        st.subheader("Chat History")
                        for entry in chat_history:
                            st.markdown(f"User: {entry['user']}")
                            st.markdown(f"AI Bot: {entry['llm']}")
                            st.text("-----------"*5) 
            

def show_main_dashboard(modelmap,
                        s3_bucket="speech-to-text-meetsummarizar",
                        local_folder = "SpeechToText",
                        user_folder = "defaultUser"):
   
    os.makedirs(local_folder, exist_ok=True)
    temp_path = os.path.join(local_folder,user_folder)
    os.makedirs(temp_path, exist_ok=True)
    bucket_file_list = source.list_files_in_folder(s3_bucket, user_folder)
    st.title("VideoInsightBot")   
    option_selected = st.sidebar.selectbox("Select an option", ["Upload a Meeting", "Q&A with Meeting", "Summarize the Meeting"])
    

    # Display descriptions in the sidebar
    if option_selected == "Upload a Meeting":
        st.write("Upload meeting recordings, It can be Audio/Video or Text files.")
        uploaded_file = st.file_uploader("Choose a video file or txt file", type=["mp4", "mp3", "wav", "flac","ogg","amr","webm", "txt"])
        if uploaded_file is not None:
            source.delete_files_in_folder(temp_path)
            file_extension = Path(uploaded_file.name).suffix.lower()[1:]
            
            if file_extension not in ["mp4", "mp3", "wav", "flac","ogg","amr","webm", "txt"]:
                st.error("Unsupported file format. Please upload an mp3 | mp4 | wav | flac | ogg | amr | webm | txt file.")
            else:
                filename = uploaded_file.name
                txt_filename = filename.replace(file_extension, "txt")
                file_path = os.path.join(temp_path,filename)
                bucket_file_path=os.path.join(user_folder,filename)
                transcribe_s3_path = os.path.join(user_folder,txt_filename)
                transcribe_local_path = os.path.join(temp_path,txt_filename)
                uploaded_video_file = video_file(filename,
                                        txt_filename,
                                        file_extension,
                                        local_file_path=file_path,
                                        s3_file_path=bucket_file_path,
                                        transcribe_local_path=transcribe_local_path,
                                        transcribe_s3_path=transcribe_s3_path)
                handle_upload_functionality(uploaded_video_file, 
                                            uploaded_file,
                                            bucket_file_list)
    elif option_selected == "Q&A with Meeting":
        st.write("You can ask questions to uploaded meeting files, \nwe use transcription of video to retrieve the answers!.")
        try:
            
            selected_option = show_dropdown(bucket_file_list)
            show_video(selected_option, 
                       local_folder, 
                       bucket_file_list)
            transcribe_local_path = "./"+os.path.join(local_folder, selected_option)
            modelId = show_dropdown_models(modelmap)
            if not os.path.exists(transcribe_local_path):
                source.download_from_s3(selected_option, transcribe_local_path, s3_bucket)
            content = source.read_transcribe(transcribe_local_path)
            ask_LLM(content, modelId, selected_option)
        except:
            st.text_area("Message",value="There has been some issue! Try again!", height=50, max_chars=None)
    else:
        try:
            st.write("You can summarize the meeting using this option.")
            selected_option = show_dropdown(bucket_file_list)
            show_video(selected_option, 
                       local_folder, 
                       bucket_file_list)
            transcribe_local_path = "./"+os.path.join(local_folder, selected_option)
            modelId = show_dropdown_models(modelmap)
            summary_filename = selected_option.replace(".txt", "_"+modelId+"_summary.txt")
            summary_file_local_path = os.path.join(local_folder, summary_filename)

            if os.path.exists(summary_file_local_path):
                with open(summary_file_local_path, "r") as content:
                    summary = content.read()
            else:
                with st.spinner("Summarizing..."):
                    if not os.path.exists(transcribe_local_path):
                        source.download_from_s3(selected_option, transcribe_local_path, s3_bucket)
                    content = source.read_transcribe(transcribe_local_path)
                    summary = summarizer_bot(content,modelId)
                with open(summary_file_local_path, "w") as file:
                    file.write(summary)
            st.subheader("Summary:")
            st.text_area("Details are from Large Language Model named Claudev3",value=summary, height=500, max_chars=None)
        except Exception as e:
            print(e)
            st.text_area("Message",value="There has been some issue! Try again!", height=50, max_chars=None)


if __name__ == "__main__":  
    # model_map = {"Claude Instant": "anthropic.claude-instant-v1",
    #              "Claude V1": "anthropic.claude-v1", 
    #              "Claude V2": "anthropic.claude-v2",
    #              "Claude V2.1": "anthropic.claude-v2:1",
    #              "Claude V3": "anthropic.claude-3-sonnet-20240229-v1:0"}
    
    model_map = {"Claude Instant": "anthropic.claude-instant-v1",
                 "Claude V3": "anthropic.claude-3-sonnet-20240229-v1:0"}
    s3_bucket="speech-to-text-meetsummarizar"
    local_folder = "SpeechToText"
    user_folder = "defaultUser"
      

    show_main_dashboard(model_map,
                        s3_bucket,
                        local_folder,
                        user_folder
                        )
