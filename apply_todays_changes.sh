#!/bin/bash
set -e

echo "Applying today's changes..."

# 1. Update imports and add helper functions
echo "1. Adding imports and normalization function..."
# This will be done in stages

# 2. Add xwOBA data file (already exists from scraping)
if [ ! -f "src/xwoba_data.json" ]; then
  echo "ERROR: src/xwoba_data.json missing - need to re-scrape"
  exit 1
fi

# 3. Update contract data (already done)
if [ ! -f "src/contract_data.json" ]; then
  echo "ERROR: src/contract_data.json missing"
  exit 1
fi

echo "Ready to apply code changes. Proceed? (y/n)"
read -r response
if [[ "$response" != "y" ]]; then
  echo "Aborted"
  exit 1
fi

echo "Creating backup..."
cp src/App.jsx src/App.jsx.backup

echo "All changes will be applied manually via code editor to avoid sed errors."
echo "Opening summary of changes needed..."
