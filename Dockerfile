FROM python:3.11.7 as app
WORKDIR /application
COPY /application/ /application/
RUN pip install --upgrade pip 
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit","run","frontend.py","--server.port","8501","--server.address", "0.0.0.0"]