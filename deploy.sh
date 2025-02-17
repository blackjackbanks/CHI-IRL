#!/bin/bash

# Exit on first error
set -e

# Verify dependencies
echo "Checking dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements-vercel.txt

# Run tests (if you have any)
# python3 -m pytest tests/

# Lint code
# flake8 .

# Prepare deployment
echo "Preparing Vercel deployment..."
vercel --prod

# Optional: Run post-deployment checks
# curl https://your-vercel-app.vercel.app/health

echo "Deployment completed successfully!"
