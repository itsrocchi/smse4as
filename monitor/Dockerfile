# Use an official Python runtime as a parent image
FROM python:3.10
 
# Set the working directory in the container to /app
WORKDIR /monitor
 
# Copy the current directory contents into the container at /app
COPY . /monitor
 
# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirementss.txt
 
# Run app.py when the container launches
CMD ["python", "sensors.py"]            