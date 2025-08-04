#!/bin/bash

source ~/.bashrc
export PATH="$HOME/.foundry/bin:$PATH"
set -xv

ls -al results
rm -rf results/
rm storycheck.log
clear

cd interpreter/browser/mock_wallet/
pnpm build
cd -

uv run python3 app.py "$@"