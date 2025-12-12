#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from getproxy.github_api import get_content, update_content, create_file
import requests

# Test configuration
TEST_TIMEOUT = 5  # seconds
TEST_URL = "http://httpbin.org/get"
MAX_WORKERS = 50  # Concurrent test threads
MAX_RESPONSE_TIME = 3.0  # Max acceptable response time in seconds

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

def test_proxy(proxy):
    """
    Test a single proxy and return if it's valid
    Returns: (proxy, is_valid)
    """
    host = proxy.get('host')
    port = proxy.get('port')
    proxy_type = proxy.get('type', 'http')

    if not host or not port:
        return proxy, False

    # Build proxy URL
    if proxy_type.lower() == 'https':
        proxy_url = f"https://{host}:{port}"
    else:
        proxy_url = f"http://{host}:{port}"

    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }

    try:
        start_time = time.time()
        response = requests.get(
            TEST_URL,
            proxies=proxies,
            timeout=TEST_TIMEOUT,
            verify=False
        )
        elapsed = time.time() - start_time

        # Check if proxy actually works
        if response.status_code == 200:
            response_json = response.json()

            # Verify the proxy is actually routing through the proxy
            origin = response_json.get('origin', '')
            if host in origin and elapsed <= MAX_RESPONSE_TIME:
                # Add actual response time
                proxy_copy = proxy.copy()
                proxy_copy['response_time'] = round(elapsed, 2)
                return proxy_copy, True

        return proxy, False
    except Exception as e:
        return proxy, False

def validate_proxies(proxies, max_workers=MAX_WORKERS):
    """
    Validate all proxies concurrently
    Returns: list of valid proxies
    """
    valid_proxies = []
    total = len(proxies)
    print(f"[*] Testing {total} proxies with {max_workers} threads...")

    # Disable warnings
    requests.packages.urllib3.disable_warnings()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_proxy = {executor.submit(test_proxy, proxy): proxy for proxy in proxies}

        completed = 0
        for future in as_completed(future_to_proxy):
            proxy, is_valid = future.result()
            completed += 1

            if completed % 10 == 0 or completed == total:
                print(f"[*] Progress: {completed}/{total} ({completed*100//total}%)")

            if is_valid:
                valid_proxies.append(proxy)

    print(f"[✓] Validation complete: {len(valid_proxies)}/{total} proxies passed")
    return valid_proxies

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

def validate_merge_and_upload(token):
    """
    Download existing data from ip_ports, merge with new data,
    validate proxies through testing, and upload only valid ones
    """
    print("[*] Starting validation, merge and upload process...")

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

    # Merge proxies (without validation first to reduce API calls)
    merged_proxies = merge_proxies(existing_proxies, new_proxies)
    print(f"[*] Merged to {len(merged_proxies)} unique proxies")

    # Validate ALL proxies through testing
    print(f"[*] Starting proxy validation (timeout={TEST_TIMEOUT}s, max_response_time={MAX_RESPONSE_TIME}s)...")
    valid_proxies = validate_proxies(merged_proxies, MAX_WORKERS)

    if not valid_proxies:
        print("[-] No valid proxies found. Nothing to upload.")
        return False

    # Generate output files from VALID proxies only
    print("[*] Generating output files from validated proxies...")
    proxyinfo_json = generate_proxyinfo_json(valid_proxies)
    proxyinfo_txt = generate_proxyinfo_txt(valid_proxies)
    db_json = generate_db_json(valid_proxies)

    # Upload files to ip_ports
    print("[*] Uploading proxyinfo.json...")
    try:
        success, status = upload_or_create(
            "parserpp", "ip_ports", "/proxyinfo.json", token,
            proxyinfo_json, "GitHubAction: Update validated proxy list"
        )
        print(f"[✓] {status} proxyinfo.json")
    except Exception as e:
        print(f"[-] Failed to upload proxyinfo.json: {e}")
        return False

    print("[*] Uploading proxyinfo.txt...")
    try:
        success, status = upload_or_create(
            "parserpp", "ip_ports", "/proxyinfo.txt", token,
            proxyinfo_txt, "GitHubAction: Update validated proxy list"
        )
        print(f"[✓] {status} proxyinfo.txt")
    except Exception as e:
        print(f"[-] Failed to upload proxyinfo.txt: {e}")
        return False

    print("[*] Uploading db.json...")
    try:
        success, status = upload_or_create(
            "parserpp", "ip_ports", "/db.json", token,
            db_json, "GitHubAction: Update validated proxy list"
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

    print(f"[*] All tasks completed successfully! Uploaded {len(valid_proxies)} validated proxies.")
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

    success = validate_merge_and_upload(token)
    sys.exit(0 if success else 1)