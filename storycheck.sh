# File: storycheck.sh
#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Load .env.local for ALCHEMY_API_KEY
[ -f "$DIR/.env.local" ] && source "$DIR/.env.local"

# Validate ALCHEMY_API_KEY
if [ -z "$ALCHEMY_API_KEY" ] || [ "$ALCHEMY_API_KEY" = "YOUR_ALCHEMY_API_KEY" ]; then
    echo "Error: ALCHEMY_API_KEY is unset or invalid. Set it in $DIR/.env.local."
    exit 1
fi

source ~/.bashrc
export PATH="$HOME/.foundry/bin:$PATH"
set -xv

# Use output-dir from args (default: results)
OUTPUT_DIR="${2:-results}"
ls -al "$DIR/$OUTPUT_DIR"
rm -rf "$DIR/$OUTPUT_DIR/"
rm -f "$DIR/storycheck.log"

cd "$DIR/interpreter/browser/mock_wallet/"
pnpm build
cd -

uv run python3 "$DIR/app.py" "$1" --output-dir "$DIR/$OUTPUT_DIR"