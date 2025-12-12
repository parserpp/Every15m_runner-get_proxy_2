#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
from getproxy.github_api import update_content, delete_file

def upload_and_cleanup(token):
    """
    Upload proxy.list and proxy.list.out to ip_ports repository,
    then delete local files
    """
    print("[*] Starting upload and cleanup...")

    # Upload proxy.list to ip_ports as proxy.list (or proxyinfo.json?)
    if os.path.exists('proxy.list'):
        print("[*] Uploading proxy.list to ip_ports/proxy.list...")
        try:
            with open('proxy.list', 'r', encoding='utf-8') as f:
                content = f.read()
            update_content(
                "parserpp",
                "ip_ports",
                "/proxy.list",
                _token=token,
                _content_not_base64=content,
                _commit_msg="GitHubAction: Update proxy list"
            )
            print("[✓] Successfully uploaded proxy.list")
        except Exception as e:
            print(f"[-] Failed to upload proxy.list: {e}")
            return False

    # Upload proxy.list.out to ip_ports as proxy.list.out
    if os.path.exists('proxy.list.out'):
        print("[*] Uploading proxy.list.out to ip_ports/proxy.list.out...")
        try:
            with open('proxy.list.out', 'r', encoding='utf-8') as f:
                content = f.read()
            update_content(
                "parserpp",
                "ip_ports",
                "/proxy.list.out",
                _token=token,
                _content_not_base64=content,
                _commit_msg="GitHubAction: Update proxy list output"
            )
            print("[✓] Successfully uploaded proxy.list.out")
        except Exception as e:
            print(f"[-] Failed to upload proxy.list.out: {e}")
            return False

    # Clean up local files
    print("[*] Cleaning up local files...")
    try:
        if os.path.exists('proxy.list'):
            os.remove('proxy.list')
            print("[✓] Deleted proxy.list")
        if os.path.exists('proxy.list.out'):
            os.remove('proxy.list.out')
            print("[✓] Deleted proxy.list.out")
    except Exception as e:
        print(f"[-] Failed to delete local files: {e}")
        return False

    print("[*] All tasks completed successfully!")
    return True

if __name__ == "__main__":
    token = os.getenv('GTOKEN') or os.getenv('GITHUB_TOKEN')
    if not token:
        print("[-] Error: No GitHub token found in GTOKEN or GITHUB_TOKEN environment variable")
        sys.exit(1)

    success = upload_and_cleanup(token)
    sys.exit(0 if success else 1)