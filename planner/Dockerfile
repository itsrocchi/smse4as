# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory in the container to /app
WORKDIR /planner
 
# Copy the current directory contents into the container at /app
COPY . /planner

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
 
# Esegui lo script di attesa per RabbitMQ prima di avviare il planner
CMD ["python", "planner.py"]  