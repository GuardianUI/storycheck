#!/bin/bash

set -xv

ls -al results
# clean up from previous runs
rm -rf results/

rm storycheck.log

# clear

# start app
python3 app.py
