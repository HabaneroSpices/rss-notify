#!/bin/sh
#
set -e
set -x

DOCKER_USER=app
DOCKER_GROUP=app
USER_ID=${PUID:-0}
GROUP_ID=${PGID:-0}

echo -e "\tUsing $USER_ID:$GROUP_ID"

if ! mkdir -p /user; then
  echo "Cannot create /user directory"
  exit 1
fi

FILE=/user/config.ini
if ! test -f "${FILE}"; then
  echo "No ${FILE} found in /app - Trying to create it now..."
  
  if ! cp "/app/config.ini-sample" "${FILE}"; then
    echo "Could not create ${FILE}"
    exit 1
  else 
    echo "Created ${FILE}"
  fi
fi

FILE=/user/notified_entries.db
if ! test -f "${FILE}"; then
  echo "No ${FILE} found in /app - Trying to create it now..."

  if ! echo "" | tee "${FILE}"; then
    echo "Could not create ${FILE}"
    exit 1
  else 
    echo "Created ${FILE}"
  fi
fi

# Set permissions on user files, if enabled.
if [ "$SKIP_PERM_CHECK" != "true" ]; then
	chown -vR $USER_ID:$GROUP_ID /user
	chmod -vR ug+rwx /user
fi

exec python main.py "${@}"
