# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Set work directory
WORKDIR /app

COPY . /app

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt


COPY . /app


# Define the default command to run the app
CMD ["python", "app.py"]