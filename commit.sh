#!/usr/bin/env bash
set -e

# move the generated files to temporary directory
mv -v generated /tmp/generated

# switch to generated branch
git checkout generated

# set up git
git config user.name "actions@github.com"
git config user.email "GitHub Actions"

# clean up
# git rm -rf --ignore-unmatch *
rm -rf *
mv -v /tmp/generated/* .

# commit
git add --all

if [ -z "$SCHEDULED_ACTION" ]; then
  git commit -m "Update generated files: $GITHUB_SHA"
else
  git commit -m "Update generated files (scheduled)"
fi

git push origin generated
