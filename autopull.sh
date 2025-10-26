#!/bin/bash
while true; do
    git fetch origin
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u})

    if [ $LOCAL != $REMOTE ]; then
        echo "Changes detected, pulling updates..."
        git pull origin main
        # Optionally, you can add commands to restart services or notify users here
    else
        echo "No changes detected."
    fi

    sleep 120  # Wait for 2 minutes before checking again
done