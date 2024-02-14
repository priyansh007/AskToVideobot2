class video_file():
    def __init__(self, 
                 input_video_file_name,
                 transcribe_file,
                 file_extension,
                 local_file_path,
                 s3_file_path,
                 transcribe_local_path,
                 transcribe_s3_path):
        self.input_video_file_name = input_video_file_name
        self.transcribe_file = transcribe_file
        self.file_extension = file_extension
        self.local_file_path = local_file_path
        self.s3_file_path = s3_file_path
        self.transcribe_local_path = transcribe_local_path
        self.transcribe_s3_path = transcribe_s3_path