#! /usr/bin/env bash

IGNORE_DIFF_ON="README.md CONTRIBUTING.md Makefile .gitignore .github/*"

# Fetch all tags
git fetch --tags

last_tagged_commit=`git tag --list | sort -V | grep -v ipp | tail -1`
echo ".gitlab-ci/has-functional-changes.sh : avec git tag --list last_tagged_commit=$last_tagged_commit"

# Check if any file that has not be listed in IGNORE_DIFF_ON has changed since the last tag was published.
if git diff-index --name-only --exit-code $last_tagged_commit -- . `echo " $IGNORE_DIFF_ON" | sed 's/ / :(exclude)/g'`
then
  echo "No functional changes detected."
  exit 1
else
  echo "The functional files above were changed."
fi
