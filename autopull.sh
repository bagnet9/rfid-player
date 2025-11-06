#!/bin/bash
    # Usage: ./autopull.sh [no_rerun]

    NO_RERUN=false
    if [ "$1" = "no_rerun" ]; then
        NO_RERUN=true
    fi

    check_and_pull() {
        git fetch origin
        LOCAL=$(git rev-parse @)
        REMOTE=$(git rev-parse @{u})

        if [ "$LOCAL" != "$REMOTE" ]; then
            echo "Changes detected, pulling updates..."
            git pull origin main
            # Optionally, add commands to restart services or notify users here
        else
            echo "No changes detected."
        fi
    }

    if [ "$NO_RERUN" = true ]; then
        check_and_pull
        exit 0
    fi

    while true; do
        check_and_pull
        sleep 120  # Wait for 2 minutes before checking again
    done