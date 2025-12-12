#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
from getproxy.github_api import update_content, create_file, getSha

def upload_or_create_file(owner, repo, path, token, content, commit_msg):
    """
    Try to update file, if it doesn't exist, create it
    """
    try:
        # Try to update existing file
        update_content(owner, repo, path, _token=token, _content_not_base64=content, _commit_msg=commit_msg)
        return True, "Updated"
    except Exception as e:
        error_msg = str(e)
        if "'sha'" in error_msg or "Not Found" in error_msg or "does not exist" in error_msg:
            # File doesn't exist, try to create it
            try:
                create_file(owner, repo, path, _token=token, _content_not_base64=content, _commit_msg=commit_msg)
                return True, "Created"
            except Exception as e2:
                return False, f"Failed to create: {e2}"
        else:
            return False, f"Failed to update: {error_msg}"

def upload_and_cleanup(token):
    """
    Upload proxy.list and proxy.list.out to ip_ports repository,
    then delete local files
    """
    print("[*] Starting upload and cleanup...")

    # Upload proxy.list to ip_ports as proxy.list
    if os.path.exists('proxy.list'):
        print("[*] Uploading proxy.list to ip_ports/proxy.list...")
        try:
            with open('proxy.list', 'r', encoding='utf-8') as f:
                content = f.read()

            success, status = upload_or_create_file(
                "parserpp",
                "ip_ports",
                "/proxy.list",
                token,
                content,
                "GitHubAction: Update proxy list"
            )

            if success:
                print(f"[✓] Successfully {status} proxy.list")
            else:
                print(f"[-] Failed to upload proxy.list: {status}")
                return False
        except Exception as e:
            print(f"[-] Failed to upload proxy.list: {e}")
            return False

    # Upload proxy.list.out to ip_ports as proxy.list.out
    if os.path.exists('proxy.list.out'):
        print("[*] Uploading proxy.list.out to ip_ports/proxy.list.out...")
        try:
            with open('proxy.list.out', 'r', encoding='utf-8') as f:
                content = f.read()

            success, status = upload_or_create_file(
                "parserpp",
                "ip_ports",
                "/proxy.list.out",
                token,
                content,
                "GitHubAction: Update proxy list output"
            )

            if success:
                print(f"[✓] Successfully {status} proxy.list.out")
            else:
                print(f"[-] Failed to upload proxy.list.out: {status}")
                return False
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