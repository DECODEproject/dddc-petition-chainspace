#!/usr/bin/env bash

sudo unlink /app/contracts
sudo ln -sf ${PWD}/contracts /app/contracts

python3 -m venv .petition-chainspace
. ./.petition-chainspace/bin/activate
pip install --upgrade pip
pip install -e .
