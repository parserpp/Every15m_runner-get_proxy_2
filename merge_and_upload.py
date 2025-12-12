#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
from getproxy.github_api import get_content, update_content, create_file

def parse_json_lines(content):
    """Parse JSON lines into a list of objects"""
    proxies = []
    for line in content.strip().split('\n'):
        line = line.strip()
        if line:
            try:
                proxies.append(json.loads(line))
            except:
                pass
    return proxies

def parse_ip_port_text(content):
    """Parse IP:PORT format into list"""
    proxies = []
    for line in content.strip().split('\n'):
        line = line.strip()
        if line and ':' in line:
            host, port = line.rsplit(':', 1)
            try:
                proxies.append({
                    "host": host,
                    "port": int(port),
                    "type": "http" if port not in ['443', '8443'] else "https"
                })
            except:
                pass
    return proxies

def merge_proxies(existing_proxies, new_proxies):
    """Merge proxy lists, removing duplicates"""
    merged = {}
    all_proxies = existing_proxies + new_proxies

    for proxy in all_proxies:
        # Create unique key based on host, port, and type
        key = f"{proxy.get('host')}:{proxy.get('port')}:{proxy.get('type', 'http')}"

        # Keep the proxy with more complete information
        if key not in merged or len(json.dumps(proxy)) > len(json.dumps(merged[key])):
            merged[key] = proxy

    return list(merged.values())

def generate_proxyinfo_json(proxies):
    """Generate proxyinfo.json (JSON lines format)"""
    lines = []
    for proxy in proxies:
        lines.append(json.dumps(proxy))
    return '\n'.join(lines) + '\n'

def generate_proxyinfo_txt(proxies):
    """Generate proxyinfo.txt (IP:PORT format)"""
    lines = []
    for proxy in proxies:
        host = proxy.get('host')
        port = proxy.get('port')
        if host and port:
            lines.append(f"{host}:{port}")
    return '\n'.join(lines) + '\n'

def generate_db_json(proxies):
    """Generate db.json (grouped by type and anonymity)"""
    db = {}
    for proxy in proxies:
        proxy_type = proxy.get('type', 'http')
        anonymity = proxy.get('anonymity', 'transparent')
        key = f"{proxy_type}_{anonymity}"

        # Create a copy without export_address for db.json
        proxy_copy = {k: v for k, v in proxy.items() if k != 'export_address'}

        if key not in db:
            db[key] = []
        db[key].append(proxy_copy)

    return json.dumps(db, indent=2)

def merge_and_upload(token):
    """
    Download existing data from ip_ports, merge with new data, and upload
    """
    print("[*] Starting merge and upload process...")

    # Download existing data from ip_ports
    print("[*] Downloading existing data from ip_ports...")
    try:
        existing_json = get_content("parserpp", "ip_ports", "/proxyinfo.json", token)
        existing_txt = get_content("parserpp", "ip_ports", "/proxyinfo.txt", token)
        existing_db = get_content("parserpp", "ip_ports", "/db.json", token)
        print("[✓] Downloaded existing data")
    except Exception as e:
        print(f"[-] Warning: Could not download existing data: {e}")
        print("    Will create new files from scratch")
        existing_json = ""
        existing_txt = ""
        existing_db = "{}"

    # Parse existing data
    existing_proxies = parse_json_lines(existing_json)
    print(f"[*] Found {len(existing_proxies)} existing proxies")

    # Read new data from proxy.list.out
    if not os.path.exists('proxy.list.out'):
        print("[-] Error: proxy.list.out not found")
        return False

    with open('proxy.list.out', 'r') as f:
        new_json = f.read()

    new_proxies = parse_json_lines(new_json)
    print(f"[*] Found {len(new_proxies)} new proxies")

    # Merge proxies
    merged_proxies = merge_proxies(existing_proxies, new_proxies)
    print(f"[✓] Merged to {len(merged_proxies)} unique proxies")

    # Generate output files
    print("[*] Generating output files...")
    proxyinfo_json = generate_proxyinfo_json(merged_proxies)
    proxyinfo_txt = generate_proxyinfo_txt(merged_proxies)
    db_json = generate_db_json(merged_proxies)

    # Upload files to ip_ports
    print("[*] Uploading proxyinfo.json...")
    try:
        success, status = upload_or_create(
            "parserpp", "ip_ports", "/proxyinfo.json", token,
            proxyinfo_json, "GitHubAction: Merge and update proxy list"
        )
        print(f"[✓] {status} proxyinfo.json")
    except Exception as e:
        print(f"[-] Failed to upload proxyinfo.json: {e}")
        return False

    print("[*] Uploading proxyinfo.txt...")
    try:
        success, status = upload_or_create(
            "parserpp", "ip_ports", "/proxyinfo.txt", token,
            proxyinfo_txt, "GitHubAction: Merge and update proxy list"
        )
        print(f"[✓] {status} proxyinfo.txt")
    except Exception as e:
        print(f"[-] Failed to upload proxyinfo.txt: {e}")
        return False

    print("[*] Uploading db.json...")
    try:
        success, status = upload_or_create(
            "parserpp", "ip_ports", "/db.json", token,
            db_json, "GitHubAction: Merge and update proxy list"
        )
        print(f"[✓] {status} db.json")
    except Exception as e:
        print(f"[-] Failed to upload db.json: {e}")
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
        print(f"[-] Warning: Failed to delete local files: {e}")

    print("[*] All tasks completed successfully!")
    return True

def upload_or_create(owner, repo, path, token, content, commit_msg):
    """Try to update file, if it doesn't exist, create it"""
    try:
        update_content(owner, repo, path, _token=token, _content_not_base64=content, _commit_msg=commit_msg)
        return True, "Updated"
    except Exception as e:
        error_msg = str(e)
        if "'sha'" in error_msg or "Not Found" in error_msg or "does not exist" in error_msg:
            try:
                create_file(owner, repo, path, _token=token, _content_not_base64=content, _commit_msg=commit_msg)
                return True, "Created"
            except Exception as e2:
                return False, f"Failed to create: {e2}"
        else:
            return False, f"Failed to update: {error_msg}"

if __name__ == "__main__":
    token = os.getenv('GTOKEN') or os.getenv('GITHUB_TOKEN')
    if not token:
        print("[-] Error: No GitHub token found")
        sys.exit(1)

    success = merge_and_upload(token)
    sys.exit(0 if success else 1)