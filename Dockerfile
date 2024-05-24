# Use an official Python runtime as a parent image
FROM python:3.10-slim

RUN apt-get update && apt-get install -y gosu;

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY main.py /app
COPY utils.py /app
COPY requirements.txt /app
COPY config.ini-sample /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt;

# Entrypoint
COPY entrypoint.sh /app
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT [ "/app/entrypoint.sh" ]
