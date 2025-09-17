# Use a separate stage for building the dependencies
FROM python:3.9-slim as builder

# Set the working directory
WORKDIR /app

# Copy and install dependencies without cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Use a lean base image for the final runtime
FROM python:3.9-slim

# Copy only the installed packages and code from the builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /app /app

# Set the working directory and expose the port
WORKDIR /app
EXPOSE 8080

# Run the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
