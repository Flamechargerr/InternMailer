#!/usr/bin/env python3
"""
Cloud Deployment for Background Scraper
Deploys the background scraper to cloud services for 24/7 operation
"""

import os
import json
import subprocess
import sys
from datetime import datetime

def create_heroku_deployment():
    """Create Heroku deployment"""
    print("🚀 Creating Heroku deployment...")
    
    # Create Procfile
    procfile = "worker: python background_scraper.py --continuous --interval 30"
    with open('Procfile', 'w') as f:
        f.write(procfile)
    
    # Create runtime.txt
    runtime = "python-3.9.18"
    with open('runtime.txt', 'w') as f:
        f.write(runtime)
    
    # Create app.json
    app_config = {
        "name": "background-email-scraper",
        "description": "Background email scraper running 24/7",
        "repository": "https://github.com/yourusername/background-scraper",
        "env": {
            "PYTHONUNBUFFERED": "1"
        },
        "formation": {
            "worker": {
                "quantity": 1,
                "size": "basic"
            }
        }
    }
    
    with open('app.json', 'w') as f:
        json.dump(app_config, f, indent=2)
    
    # Create deployment script
    deploy_script = """#!/bin/bash
# Heroku deployment script

echo "🚀 Deploying to Heroku..."

# Create Heroku app
heroku create background-email-scraper

# Add buildpack
heroku buildpacks:set heroku/python

# Deploy
git add .
git commit -m "Deploy background scraper"
git push heroku main

# Start worker
heroku ps:scale worker=1

echo "✅ Deployed to Heroku!"
echo "📊 Check logs: heroku logs --tail"
"""
    
    with open('deploy_heroku.sh', 'w') as f:
        f.write(deploy_script)
    
    print("✅ Heroku deployment files created:")
    print("   - Procfile")
    print("   - runtime.txt")
    print("   - app.json")
    print("   - deploy_heroku.sh")
    print("📋 To deploy: bash deploy_heroku.sh")

def create_railway_deployment():
    """Create Railway deployment"""
    print("🚂 Creating Railway deployment...")
    
    # Create railway.json
    railway_config = {
        "$schema": "https://railway.app/railway.schema.json",
        "build": {
            "builder": "NIXPACKS"
        },
        "deploy": {
            "startCommand": "python background_scraper.py --continuous --interval 30",
            "restartPolicyType": "ON_FAILURE",
            "restartPolicyMaxRetries": 10
        }
    }
    
    with open('railway.json', 'w') as f:
        json.dump(railway_config, f, indent=2)
    
    # Create deployment script
    deploy_script = """#!/bin/bash
# Railway deployment script

echo "🚂 Deploying to Railway..."

# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Deploy
railway up

echo "✅ Deployed to Railway!"
echo "📊 Check logs: railway logs"
"""
    
    with open('deploy_railway.sh', 'w') as f:
        f.write(deploy_script)
    
    print("✅ Railway deployment files created:")
    print("   - railway.json")
    print("   - deploy_railway.sh")
    print("📋 To deploy: bash deploy_railway.sh")

def create_render_deployment():
    """Create Render deployment"""
    print("🎨 Creating Render deployment...")
    
    # Create render.yaml
    render_config = {
        "services": [
            {
                "type": "worker",
                "name": "background-email-scraper",
                "env": "python",
                "buildCommand": "pip install -r requirements.txt",
                "startCommand": "python background_scraper.py --continuous --interval 30",
                "plan": "free"
            }
        ]
    }
    
    with open('render.yaml', 'w') as f:
        json.dump(render_config, f, indent=2)
    
    # Create deployment script
    deploy_script = """#!/bin/bash
# Render deployment script

echo "🎨 Deploying to Render..."

# Install Render CLI
curl -s https://render.com/download-cli/linux | bash

# Deploy
render deploy

echo "✅ Deployed to Render!"
echo "📊 Check logs in Render dashboard"
"""
    
    with open('deploy_render.sh', 'w') as f:
        f.write(deploy_script)
    
    print("✅ Render deployment files created:")
    print("   - render.yaml")
    print("   - deploy_render.sh")
    print("📋 To deploy: bash deploy_render.sh")

def create_docker_deployment():
    """Create Docker deployment"""
    print("🐳 Creating Docker deployment...")
    
    # Create Dockerfile
    dockerfile = """FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data logs

# Run the scraper
CMD ["python", "background_scraper.py", "--continuous", "--interval", "30"]
"""
    
    with open('Dockerfile.cloud', 'w') as f:
        f.write(dockerfile)
    
    # Create docker-compose for cloud
    docker_compose = """version: '3.8'

services:
  background-scraper:
    build:
      context: .
      dockerfile: Dockerfile.cloud
    container_name: background-email-scraper
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    networks:
      - scraper-network

networks:
  scraper-network:
    driver: bridge
"""
    
    with open('docker-compose.cloud.yml', 'w') as f:
        f.write(docker_compose)
    
    # Create deployment script
    deploy_script = """#!/bin/bash
# Docker deployment script

echo "🐳 Building and running Docker container..."

# Build image
docker build -f Dockerfile.cloud -t background-email-scraper .

# Run container
docker-compose -f docker-compose.cloud.yml up -d

echo "✅ Docker deployment complete!"
echo "📊 Check logs: docker-compose -f docker-compose.cloud.yml logs -f"
"""
    
    with open('deploy_docker.sh', 'w') as f:
        f.write(deploy_script)
    
    print("✅ Docker deployment files created:")
    print("   - Dockerfile.cloud")
    print("   - docker-compose.cloud.yml")
    print("   - deploy_docker.sh")
    print("📋 To deploy: bash deploy_docker.sh")

def create_github_actions():
    """Create GitHub Actions for automated deployment"""
    print("🔧 Creating GitHub Actions...")
    
    # Create .github/workflows directory
    os.makedirs('.github/workflows', exist_ok=True)
    
    # Create deployment workflow
    workflow = """name: Deploy Background Scraper

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run background scraper
      run: |
        python background_scraper.py --session
        echo "✅ Background scraper completed"
    
    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: scraped-emails
        path: |
          background_scraped_emails.csv
          background_scraper_stats.json
          background_scraper.log
"""
    
    with open('.github/workflows/deploy.yml', 'w') as f:
        f.write(workflow)
    
    print("✅ GitHub Actions created:")
    print("   - .github/workflows/deploy.yml")
    print("📋 Push to GitHub to trigger automated deployment")

def create_requirements_file():
    """Create requirements.txt for cloud deployment"""
    requirements = """pandas>=1.5.0
schedule>=1.2.0
requests>=2.28.0
numpy>=1.21.0
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    
    print("✅ Created requirements.txt")

def show_deployment_options():
    """Show available deployment options"""
    print("\n🌐 CLOUD DEPLOYMENT OPTIONS")
    print("=" * 50)
    print("1. Heroku (Free tier available)")
    print("   - Easy deployment")
    print("   - Free tier with limitations")
    print("   - Good for testing")
    
    print("\n2. Railway (Free tier available)")
    print("   - Modern platform")
    print("   - Good free tier")
    print("   - Easy deployment")
    
    print("\n3. Render (Free tier available)")
    print("   - Reliable platform")
    print("   - Good documentation")
    print("   - Free tier available")
    
    print("\n4. Docker (Local/Cloud)")
    print("   - Portable deployment")
    print("   - Can run anywhere")
    print("   - Full control")
    
    print("\n5. GitHub Actions (Automated)")
    print("   - Automated runs")
    print("   - Free for public repos")
    print("   - Scheduled execution")

def main():
    """Main function"""
    print("🌐 CLOUD DEPLOYMENT FOR BACKGROUND SCRAPER")
    print("=" * 50)
    
    # Create requirements file
    create_requirements_file()
    
    while True:
        print("\n📋 Choose deployment option:")
        print("1. Create Heroku deployment")
        print("2. Create Railway deployment")
        print("3. Create Render deployment")
        print("4. Create Docker deployment")
        print("5. Create GitHub Actions")
        print("6. Show deployment options")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == '1':
            create_heroku_deployment()
        elif choice == '2':
            create_railway_deployment()
        elif choice == '3':
            create_render_deployment()
        elif choice == '4':
            create_docker_deployment()
        elif choice == '5':
            create_github_actions()
        elif choice == '6':
            show_deployment_options()
        elif choice == '7':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 