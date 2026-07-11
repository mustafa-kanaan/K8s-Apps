FROM python:3.11-slim
WORKDIR /app
COPY requirment.txt .
RUN pip install --no-cache-dir -r requirment.txt
COPY app.py .
EXPOSE 8080
CMD [ "python3" , "app.py" ]