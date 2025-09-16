# Use the official Python image as a base
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Tell Cloud Run to listen on this port
ENV PORT 8080

# Expose the port
EXPOSE 8080

# Run the application
CMD ["python", "main.py"]