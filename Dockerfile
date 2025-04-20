# Use an official Python runtime as a parent image
FROM python:3.10-slim as build

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies, if needed
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the application's requirements file to the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the container
COPY . .

# Add a comment documenting required environment variables
# The following environment variables must be provided at runtime:
# - DATABASE_PASSWORD: PostgreSQL database password
# - ALCHEMY_API_KEY: Alchemy API key for Web3 interaction
# - CONTRACT_ADDRESS: Ethereum smart contract address
# - ADMIN_EMAIL: Email address to receive contact form submissions
# - SENDER_EMAIL: Email address to send from (must be verified in SES)
# - AWS_REGION: AWS region where SES is configured (default: eu-north-1)
# 
# AWS credentials must be provided in one of these ways:
# 1. Environment variables:
#    - AWS_ACCESS_KEY_ID
#    - AWS_SECRET_ACCESS_KEY
# 2. Mounted AWS credentials file (~/.aws/credentials)
# 3. EC2 instance role if running on AWS

# Expose the port that the app runs on
EXPOSE 5000

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "app:app"]
