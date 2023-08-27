#!/usr/bin/env bash
# Shell script to for github action to run.

set -xe

md5=$(md5sum README.md)

rm -f README.md

python scripts/sync-from-wiki.py "$1" README.md

new_md5=$(md5sum README.md)

echo "Old MD5 sum: ${md5}, new MD5 sum: ${new_md5}"

if [ "$md5" != "$new_md5" ]; then
    git config --global user.email "allan+droidtrickaction@eising.dk"
    git config --global user.name "Update Tricks from Wiki Action"
    git add README.md
    git commit -a -m "Update README.md at $(date)"
    git push origin master
fi
