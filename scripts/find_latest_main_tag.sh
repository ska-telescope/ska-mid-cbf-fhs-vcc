#!/bin/bash

# Used to get latest main commit tag assuming a valid .release file

GITLAB_PROJECT_NUMBER=$1

# Get and parse tag line from .release file
tag_line=$(curl -s https://gitlab.com/api/v4/projects/$GITLAB_PROJECT_NUMBER/repository/files/.release/raw?ref=main | grep "tag")
IFS="=" read tag_key tag_value <<< $(echo $tag_line)

# Empty check and return
if [[ -z $tag_value ]]; then
    exit 1;
else
    echo "$tag_value"
    exit 0;
fi
