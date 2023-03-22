#!/bin/bash

set -xvf

# clean up from previous runs
rm -f ./results/*
rm storycheck.log

clear

# start app
python3 app.py