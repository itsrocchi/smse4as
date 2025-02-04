# Use an official Python runtime as a parent image
FROM python:3.10
 
# Set the working directory in the container to /app
WORKDIR /executor
 
# Copy the current directory contents into the container at /app
COPY . /executor
 
# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
 
# Run app.py when the container launches
CMD ["python", "executor.py"]     