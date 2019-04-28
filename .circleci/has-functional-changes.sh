#! /usr/bin/env bash

IGNORE_DIFF_ON="README.md CONTRIBUTING.md Makefile .gitignore LICENSE* .circleci/* .github/* openfisca_france_data/tests/*"

# --first-parent ensures we don't follow tags not published in master through an unlikely intermediary merge commit
last_tagged_commit="$(git describe --tags --abbrev=0 --first-parent)"

# Check if any file that has not be listed in IGNORE_DIFF_ON has changed since the last tag was published.
if git diff-index --name-only --exit-code "$last_tagged_commit" -- . "$(echo " $IGNORE_DIFF_ON" | sed 's/ / :(exclude)/g')"
then
    echo "No functional changes detected."
    exit 1
else echo "The functional files above were changed."
fi
