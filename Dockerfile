# Use official Python image with version 3.11
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy all project files to container
COPY . .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Run your application
CMD ["python", "app.py"]
