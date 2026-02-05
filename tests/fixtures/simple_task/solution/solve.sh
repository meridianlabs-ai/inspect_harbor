#!/bin/bash
set -e

# Create solution file
cat > /workspace/solution.py << 'EOF'
print(2 + 2)
EOF

echo "Solution created successfully"
