#!/bin/bash

echo "🚀 This script will initialize a local Git repository and push it to GitHub."
echo "------------------------------------------------------------------------"

# Ask for the remote repository URL
echo "Please go to GitHub and create a new, EMPTY repository."
read -p "Paste the HTTPS or SSH URL for your new GitHub repository here: " GIT_URL

if [ -z "$GIT_URL" ]; then
    echo "❌ Repository URL cannot be empty. Aborting."
    exit 1
fi

# Check if git is initialized
if [ -d ".git" ]; then
    echo "✔️ A .git directory already exists."
else
    echo "-> Initializing a new Git repository..."
    git init
fi

echo "-> Staging all files for the first commit..."
git add .

echo "-> Creating the initial commit..."
git commit -m "feat: Initial commit of Vanna-LGX at Stage S2"

echo "-> Setting the branch name to 'main'..."
git branch -M main

echo "-> Adding the remote origin URL..."
# Check if remote origin already exists
if git remote | grep -q "origin"; then
    git remote set-url origin "$GIT_URL"
    echo "   (Updated existing remote 'origin')"
else
    git remote add origin "$GIT_URL"
    echo "   (Added new remote 'origin')"
fi

echo "-> Pushing the initial commit to GitHub..."
git push -u origin main

echo ""
echo "✅ All done! Your repository should now be available on GitHub at:"
echo "$GIT_URL"
echo "------------------------------------------------------------------------"
