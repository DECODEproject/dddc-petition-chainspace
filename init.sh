#!/usr/bin/env bash

sudo unlink /app/contracts
sudo ln -sf ${PWD}/contracts /app/contracts

python3 -m venv .petition-chainspace
. ./.petition-chainspace/bin/activate
pip install --upgrade pip
pip install -e .

deactivate

virtualenve .petition-chainspace-py2
. ./.petition-chainspace-py2/bin/activate
pip install --upgrade pip
pip install -e .
pip install configparser pathlib

echo "If you are on OSX you will maybe need to install a custom version of zenroom with osx lib in it"
echo "(in virtual env) pip install ../zenroom-py/dist/zenroom-0.1.3.tar.gz "

