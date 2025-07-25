#!/bin/bash

# AIRTRACK ENVIRONMENT SETUP SCRIPT
# This script helps set up the environment safely

echo "🚀 Setting up Airtrack environment..."

# Check if .env already exists
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists. Backup created as .env.backup"
    cp .env .env.backup
fi

# Copy example file
if [ -f ".env.example" ]; then
    cp .env.example .env
    echo "✅ Created .env from .env.example"
else
    echo "❌ .env.example not found!"
    exit 1
fi

# Ubuntu specific setup
if [ -f ".env_ubuntu.example" ] && [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [ -f ".env_ubuntu" ]; then
        echo "⚠️  .env_ubuntu file already exists. Backup created as .env_ubuntu.backup"
        cp .env_ubuntu .env_ubuntu.backup
    fi
    cp .env_ubuntu.example .env_ubuntu
    echo "✅ Created .env_ubuntu from .env_ubuntu.example (Linux detected)"
fi

echo ""
echo "🔐 IMPORTANT SECURITY NOTICE:"
echo "Please edit the .env file and set your actual database password!"
echo "Never commit the .env file to version control!"
echo ""
echo "📝 Edit your .env file now:"
echo "   - Set DB_PASSWORD to your actual database password"
echo "   - Update other settings as needed"
echo ""
echo "✨ Setup complete! Your passwords are now secure."
