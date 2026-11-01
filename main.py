import os
import sys
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def banner():
    print("\033[1;36m")
    print("=" * 70)
    print("                      🐺 WOLFER WEB TOOLS 🐺                      ")
    print("=" * 70)
    print("\033[1;33m       Created by Arman Hossen")
    print("       Subscribe YouTube Channel: @wolfertools0692")
    print("       Official Web Link: https://github.com/wolfertools0692")
    print("\033[1;36m" + "=" * 70 + "\033[0m")

def slow_print(text, delay=0.02):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def extract_website():
    target_url = input("\033[1;33m[+] Enter Website URL (e.g., https://example.com): \033[0m").strip()
    if not target_url:
        print("\033[1;31m[!] Invalid URL provided!\033[0m")
        return

    if not target_url.startswith("http"):
        target_url = "https://" + target_url

    print(f"\n\033[1;36m[*] Connecting and analyzing target: {target_url}\033[0m")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(target_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"\033[1;31m[!] Failed to fetch page. Status Code: {response.status_code}\033[0m")
            return

        print(f"\033[1;32m[+] Connection successful! Extracting HTML, CSS, and JS structure...\033[0m")
        
        # ডোমেইনের নাম অনুযায়ী ফোল্ডার তৈরি
        parsed_uri = urlparse(target_url)
        folder_name = parsed_uri.netloc.replace(".", "_") + "_structure"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        # মূল HTML সেভ করা
        html_path = os.path.join(folder_name, "index.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"    [SAVED] Main HTML Structure -> {html_path}")

        # BeautifulSoup দিয়ে CSS এবং JS ফাইল খোঁজা
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

        print(f"\n\033[1;33m[*] Found {len(css_links)} Stylesheet(s) and {len(js_links)} Script(s).\033[0m")

        # অ্যাসেটস ফোল্ডার তৈরি
        assets_folder = os.path.join(folder_name, "assets")
        if not os.path.exists(assets_folder):
            os.makedirs(assets_folder)

        # CSS ডাউনলোড
        for idx, css_u in enumerate(css_links):
            try:
                css_res = requests.get(css_u, headers=headers, timeout=5)
                if css_res.status_code == 200:
                    css_filename = os.path.join(assets_folder, f"style_{idx}.css")
                    with open(css_filename, "w", encoding="utf-8") as cf:
                        cf.write(css_res.text)
                    print(f"    [CSS SAVED] {css_filename}")
            except:
                pass

        # JS ডাউনলোড
        for idx, js_u in enumerate(js_links):
            try:
                js_res = requests.get(js_u, headers=headers, timeout=5)
                if js_res.status_code == 200:
                    js_filename = os.path.join(assets_folder, f"script_{idx}.js")
                    with open(js_filename, "w", encoding="utf-8") as jf:
                        jf.write(js_res.text)
                    print(f"    [JS SAVED] {js_filename}")
            except:
                pass

        print(f"\n\033[1;35m[+] Complete! All structural files saved inside folder: '{folder_name}'\033[0m")

    except Exception as e:
        print(f"\033[1;31m[!] Error occurred: {e}\033[0m")

def main():
    banner()
    slow_print("\033[1;32m[i] Wolfer Engine Initialized. Ready for Action, Operator.\033[0m")
    
    while True:
        print("\n\033[1;36m--- MENU ---")
        print("1. Extract Website Structure (HTML, CSS, JS)")
        print("2. Exit\033[0m")
        
        choice = input("\033[1;33m[?] Select an option (1-2): \033[0m").strip()
        
        if choice == '1':
            extract_website()
        elif choice == '2':
            print("\n\033[1;31m[!] Exiting Wolfer Web Tools. Stay safe, Operator!\033[0m")
            sys.exit()
        else:
            print("\033[1;31m[!] Invalid option. Please choose 1 or 2.\033[0m")

if __name__ == "__main__":
    main()
