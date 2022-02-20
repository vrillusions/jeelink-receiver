#!/bin/bash

set -e

# Changes to virtualenv and then starts jeelink receiver
#source $HOME/.virtualenvs/jeelink-receiver/bin/activate
cd $HOME/code/jeelink-receiver
./garage_door_status.py

exit 0
