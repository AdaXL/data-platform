#!/bin/bash

# This script is used for deploying the data platform application.

# Set environment variables
export $(cat ../configs/.env.example | xargs)

# Build the Docker images
docker-compose build

# Run database migrations
docker-compose run web python manage.py migrate

# Start the application
docker-compose up -d

# Print deployment status
echo "Deployment completed successfully!"