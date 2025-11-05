# Use an official Python runtime as a parent image
FROM python:3.10-slim as build

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies, if needed
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev cron \
    && rm -rf /var/lib/apt/lists/*

# Copy the application's requirements file to the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# copy source
COPY . .


# Create cron file running sync_bounties.py at minute 0 of every hour
RUN echo "0 * * * * root python /app/sync_bounties.py >> /var/log/cron.log 2>&1" > /etc/cron.d/sync_bounties \
    && chmod 0644 /etc/cron.d/sync_bounties \
    && crontab /etc/cron.d/sync_bounties


# The following environment variables must be provided at runtime:
# - DATABASE_PASSWORD: PostgreSQL database password
# - HTTP_PROVIDER: HTTP provider URL for Web3 interaction; for example, https://eth-sepolia.g.alchemy.com/v2/your-api-key (or metamask, or any other provider)
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

# Command to run cron (in background) and then launch gunicorn
CMD bash -c "cron && exec gunicorn --bind 0.0.0.0:5000 --access-logfile - --error-logfile - --log-level info app:app"
