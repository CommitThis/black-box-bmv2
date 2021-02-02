#! /usr/bin/env bash

#   Launch Waiter
#   =============
#   Launching the BM in a docker container has a chicken and egg problem
#   * Simple switch can't bind to interfaces that don't exist yet
#   * We can't bind interfaces until the container has started
#   This means that the initial docker exec can not be the switch program has
#   we haven't had time to bind the interfaces it needs.


RUNNING=1
LAUNCH=0
CMD=""
FILE=/ports

stop() {
    echo Stop
    RUNNING=0
    kill -TERM "$child" 2>/dev/null
}

run() {
    CMD=`cat $FILE`
    echo Run \"$CMD\"
    LAUNCH=1
}

trap stop SIGINT
trap stop SIGTERM
trap run SIGUSR1

echo "Executor waiting for signal (SIGUSR1)"
while [[ "$RUNNING" == "1" ]]; do
    if [[ "$LAUNCH" == "1" ]]; then
        $CMD &
        child=$!
        wait "$child"
        break
    fi
    sleep 1
done

