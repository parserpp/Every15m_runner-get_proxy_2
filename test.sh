#!/bin/bash

_token="${{ secrets.GTOKEN }}"
if [ -z "$_token" ]; then
    _token=$(echo ${GITHUB_TOKEN})
fi
echo "token:$_token"

java -jar uploadGithubService-1.1-jar-with-dependencies.jar -owner "parserpp"  -repo "ip_ports" -target-name "proxyinfo.json" -native-file "proxy.list"  -token "${_token}" -commit-messge  "GitHubAction"
