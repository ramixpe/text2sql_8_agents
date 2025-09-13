#!/bin/bash
#
# Vanna-LGX Project Structure Correction Script
# This script reorganizes the flat file layout into a proper Python package.
#

echo "🧐 Analyzing current project structure..."

# Check if the structure is already correct
if [ ! -d "core" ] && [ -d "vanna_lgx/core" ]; then
    echo "✅ Your project structure appears to be correct already. No action taken."
    echo "To run the application, use: python -m vanna_lgx.main"
    exit 0
fi

# Check if we're in a completely unexpected state
if [ ! -d "core" ] || [ ! -f "main.py" ]; then
    echo "❌ Error: Cannot find 'core/' directory or 'main.py'."
    echo "Please ensure you are in the correct project root directory."
    exit 1
fi

echo "🚀 Reorganizing into a proper Python package..."

# 1. Create the main package directory.
mkdir -p vanna_lgx

# 2. Move all the source code into the new package directory.
#    The `|| true` prevents the script from failing if a file is already moved.
echo "  -> Moving source code into 'vanna_lgx/'..."
mv config.py vanna_lgx/ || true
mv core vanna_lgx/ || true
mv utils vanna_lgx/ || true
mv main.py vanna_lgx/ || true

# 3. The __init__.py at the root is incorrect. We'll create the correct one
#    inside the package and remove the old one.
echo "  -> Creating correct package initializer..."
touch vanna_lgx/__init__.py
if [ -f "__init__.py" ]; then
    rm __init__.py
fi

# 4. Now that main.py is in the right place, apply the import patch.
echo "  -> Patching 'vanna_lgx/main.py' with correct relative import..."
sed -i '' 's/from vanna_lgx.core.graph import build_s0_graph/from .core.graph import build_s0_graph/' vanna_lgx/main.py

echo ""
echo "✅ Project structure has been corrected!"
echo ""
echo "Your new project structure is now:"
tree -L 2
echo ""
echo "👉 To run your application, please use this command:"
echo "   python -m vanna_lgx.main"
echo ""