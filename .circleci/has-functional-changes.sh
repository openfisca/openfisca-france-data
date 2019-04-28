#! /usr/bin/env bash

IGNORE_FILES="README.md CONTRIBUTING.md Makefile .gitignore LICENSE* .circleci/* .github/* tests/*"
EXCLUDE_DIFF=$(echo " $IGNORE_FILES" | sed 's/ / :(exclude)/g')

# --first-parent ensures we don't follow tags not published in master through an unlikely intermediary merge commit
LAST_TAGGED_COMMIT=$(git describe --tags --abbrev=0 --first-parent)

# Check if any file that has not be listed in IGNORE_DIFF_ON has changed since the last tag was published.
# shellcheck disable=SC2086
if git diff-index --name-only --exit-code "$LAST_TAGGED_COMMIT" -- . $EXCLUDE_DIFF
then
    echo "No functional changes detected."
    exit 1
else echo "The functional files above were changed."
fi
