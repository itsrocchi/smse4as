# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory in the container to /app
WORKDIR /planner

# Copia lo script di attesa nel container
COPY wait-for-it.sh /app/wait-for-it.sh
 
# Copy the current directory contents into the container at /app
COPY . /planner

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Aggiungi permessi di esecuzione allo script
RUN chmod +x /app/wait-for-it.sh
 
# Esegui lo script di attesa per RabbitMQ prima di avviare il planner
CMD /app/wait-for-it.sh rabbitmq:5672 -- python /planner/planner.py
