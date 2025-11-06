if [ -z "$1" ]; then
  echo "Usage: $0 <minutes>"
  exit 1
fi
MINUTES=$1
while true; do
  # Fetch the latest changes from the remote repository
  git fetch origin

  # Check if there are any changes
  if ! git diff --quiet origin/master; then
    echo "Changes detected, pulling latest code..."
    git pull origin master
  else
    echo "No changes detected."
  fi

  # Wait for the specified number of minutes before checking again
  sleep $((MINUTES * 60))
done
