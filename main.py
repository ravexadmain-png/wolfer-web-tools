import os
import sys
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def banner():
    clear_screen()
    print("\033[1;31m")
    print("     ,     _")
    print("    /|     \\ \\")
    print("   / |      \\ \\")
    print("  /  |       \\ \\")
    print(" /   |        \\ \\")
    print("/    |         \\ \\")
    print("/_____|__________\_\\")
    print("===========================================================================")
    print("                 [ WOLFER WEB TOOLS - ELITE EXRACTOR ]                     ")
    print("===========================================================================")
    print("\033[1;33m       [+] Operator  : Arman Hossen")
    print("       [+] Channel   : @wolfertools0692")
    print("       [+] Repository: https://github.com/ravexadmain-png/wolfer-web-tools")
    print("\033[1;31m===========================================================================\033[0m")

def slow_print(text, delay=0.01):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def main():
    banner()
    slow_print("\033[1;32m[SYSTEM] Wolfer Elite Core Initialized. Ready for Reconnaissance...\033[0m\n")
    
    # সরাসরি ডোমেইন ইনপুট নেওয়ার অপশন
    target_input = input("\033[1;33m[INPUT] Enter Target Domain or Website URL (e.g., example.com): \033[0m").strip()
    
    if not target_input:
        print("\033[1;31m[ERROR] Target input cannot be empty. Terminating protocol.\033[0m")
        sys.exit()

    if not target_input.startswith("http"):
        target_url = "https://" + target_input
    else:
        target_url = target_input

    print(f"\n\033[1;36m[STATUS] Establishing encrypted tunnel to: {target_url}\033[0m")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    try:
        time.sleep(1)
        response = requests.get(target_url, headers=headers, timeout=12)
        if response.status_code != 200:
            print(f"\033[1;31m[ERROR] Target unreachable. Status Code: {response.status_code}\033[0m")
            sys.exit()

        print(f"\033[1;32m[SUCCESS] Target acquired. Extracting source code and structure...\033[0m")
        
        # মোবাইল স্টোরেজে ফোল্ডার তৈরি ও সেভ করার প্রসেস
        parsed_uri = urlparse(target_url)
        folder_name = parsed_uri.netloc.replace(".", "_") + "_target_storage"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        # মূল HTML ফাইল সেভ করা
        html_path = os.path.join(folder_name, "index.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"    [SAVED] Core HTML -> {html_path}")

        soup = BeautifulSoup(response.text, 'html.parser')
        
        css_links = []
        for link in soup.find_all("link", rel="stylesheet"):
            css_url = link.get("href")
            if css_url:
                css_links.append(urljoin(target_url, css_url))

        js_links = []
        for script in soup.find_all("script"):
            js_url = script.get("src")
            if js_url:
                js_links.append(urljoin(target_url, js_url))

        print(f"\n\033[1;33m[RECON] Assets mapped: {len(css_links)} Stylesheet(s), {len(js_links)} Script(s).\033[0m")

        assets_folder = os.path.join(folder_name, "assets")
        if not os.path.exists(assets_folder):
            os.makedirs(assets_folder)

        # CSS ফাইলগুলো ডাউনলোড করে মোবাইলের ফোল্ডারে রাখা
        for idx, css_u in enumerate(css_links):
            try:
                css_res = requests.get(css_u, headers=headers, timeout=5)
                if css_res.status_code == 200:
                    css_filename = os.path.join(assets_folder, f"style_{idx}.css")
                    with open(css_filename, "w", encoding="utf-8") as cf:
                        cf.write(css_res.text)
                    print(f"    [DOWNLOADED] {css_filename}")
            except:
                pass

        # JS ফাইলগুলো ডাউনলোড করে মোবাইলের ফোল্ডারে রাখা
        for idx, js_u in enumerate(js_links):
            try:
                js_res = requests.get(js_u, headers=headers, timeout=5)
                if js_res.status_code == 200:
                    js_filename = os.path.join(assets_folder, f"script_{idx}.js")
                    with open(js_filename, "w", encoding="utf-8") as jf:
                        jf.write(js_res.text)
                    print(f"    [DOWNLOADED] {js_filename}")
            except:
                pass

        print(f"\n\033[1;35m[COMPLETE] All files successfully extracted and saved to mobile storage!")
        print(f"[STORAGE PATH] Folder Name: {folder_name}")
        print(f"[ACTION] Type 'cd {folder_name}' to view files.\033[0m")

    except Exception as e:
        print(f"\033[1;31m[ERROR] Critical failure during extraction: {e}\033[0m")

if __name__ == "__main__":
    main()
