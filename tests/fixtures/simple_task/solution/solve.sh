#!/bin/bash
set -e

# /workspace may not pre-exist
mkdir -p /workspace

# Create solution file
cat > /workspace/solution.py << 'EOF'
print(2 + 2)
EOF

echo "Solution created successfully"
