#!/bin/bash
# remember to call this as `nohup <script_name> &`

# don't exit on failure
#set -e

while true; do
    # Changes to virtualenv and then starts jeelink receiver
    cd $HOME/code/jeelink-receiver
    #./jeelink-receiver.py &>/dev/null &
    ./jeelink-receiver.py -r &>/dev/null
    sleep 60
done

