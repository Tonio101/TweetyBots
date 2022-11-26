#!/bin/bash

DEBUG=0
IS_SERVICE=1

FLOCK=/usr/bin/flock
LOCK_FILE=/tmp/twitter_bot.lockfile
FLOCK_OPTS="-n"

PYTHON3=/usr/bin/python3

BASE_PATH=$HOME/TweetyBots/FPLUpdateBot/src
MAIN_FNAME=main.py
CONFIG_FNAME=fpl_updates.local.conf
PYTHONPATH=$HOME/TweetyBots/FPLUpdateBot/src

MAIN_FILE=$BASE_PATH/$MAIN_FNAME
MAIN_CONFIG=$BASE_PATH/$CONFIG_FNAME

if [[ $DEBUG -eq 1 ]]; then
    MAIN_ARGS="--config ${MAIN_CONFIG} --debug"
else
    MAIN_ARGS="--config ${MAIN_CONFIG}"
fi

PROG=$PYTHONPATH; $PYTHON3 $MAIN_FILE $MAIN_ARGS

if [[ $DEBUG -eq 1 ]]; then
    echo "${PROG}"
fi

if [[ $IS_SERVICE -eq 1 ]]; then
    $FLOCK $FLOCK_OPTS $LOCK_FILE $PROG
else
    $PROG
fi

