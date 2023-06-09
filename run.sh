#!/bin/bash

set -xv

ls -al results
# clean up from previous runs
rm -rf results/

rm storycheck.log

clear

# build mock wallet
cd interpreter/browser/mock_wallet/
yarn build
cd -

# start app
python3 app.py "$@"
