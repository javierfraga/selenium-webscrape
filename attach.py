#!/usr/bin/env python3
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

HELP_TEXT = """
Usage:
  python attach.py [--help]

Description:
  Attaches to a running Chrome instance (debug port 9222) and ChromeDriver (port 9515).
  Drops you into an IPython REPL with `driver` ready for automation.
  Chrome Debugging Port (9515):
    - Without this port:
    - You couldn’t connect to a preexisting tab or control an existing Chrome session
    — you’d always have to launch Chrome from Selenium.
  ChromeDriver Port (9222):
    - Without this port:
    - Your Python Selenium code can’t send WebDriver commands to Chrome.
    - You’d only have DevTools access

Workflow:
  1. On the host machine, run:
       selenium-chrome   # keep running in a separate terminal
  2. Ensure proper libraries installed:
       pip install --upgrade selenium
       pip install ipython
  3. In your Python container, run:
       python attach.py
  4. Navigate to a site you want:
       driver.get("https://example.com")
       download("https://example.com/video.mp4", "myvideo.mp4") # OR can use 5 below
  5. In IPython, to download an authenticated file:
       url = "https://example.com/video.mp4"
       cookies = driver.get_cookies()
       cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
       !curl -L -H "Cookie: {cookie_str}" {url} -o myvideo.mp4

Helpers:
  - info(): list open tabs with handle, title, and URL
  - switch_to(): change active tab by handle, title, or URL fragment
  - download(url, filename): download current-session-authenticated file directly

Notes:
  - Do NOT call driver.quit() unless you want to close Chrome.
  - `!` prefix in IPython runs shell commands (wget, curl, etc.).
"""

# Show help if requested
if "--help" in sys.argv or "-h" in sys.argv:
    print(HELP_TEXT.strip())
    sys.exit(0)

# === Attach to Chrome ===
REMOTE_URL = os.getenv("SELENIUM_REMOTE_URL", "http://host.docker.internal:9515")
DEBUGGER   = os.getenv("SELENIUM_DEBUGGER",    "127.0.0.1:9222")

opts = Options()
opts.debugger_address = DEBUGGER
driver = webdriver.Remote(command_executor=REMOTE_URL, options=opts)

driver.switch_to.new_window('tab')
controlled_handle = driver.current_window_handle

# ----- Helper functions -----
def info():
    """List open info with handle, title, and URL."""
    data = []
    current = driver.current_window_handle
    for h in driver.window_handles:
        driver.switch_to.window(h)
        data.append({"handle": h, "title": driver.title, "url": driver.current_url})
    driver.switch_to.window(current)
    return data

def switch_to(handle=None, title_contains=None, url_contains=None):
    """Switch to a tab by handle, title, or URL."""
    if handle:
        driver.switch_to.window(handle)
        return driver.current_window_handle
    for h in driver.window_handles:
        driver.switch_to.window(h)
        if (title_contains and title_contains.lower() in (driver.title or "").lower()) \
           or (url_contains and url_contains.lower() in (driver.current_url or "").lower()):
            return driver.current_window_handle
    raise RuntimeError("No matching tab found")

def download(url, filename):
    """Download a file using the current Selenium session's cookies."""
    cookies = driver.get_cookies()
    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
    os.system(f'curl -L -H "Cookie: {cookie_str}" "{url}" -o "{filename}"')

# --- Console output when starting ---
print(HELP_TEXT.strip())
print("\n✅ Attached to Chrome")
print("🪟 Controlled tab handle:", controlled_handle)
print("💡 Helpers: info(), switch_to(...), download(url, filename)")
print("💡 Example: download('https://example.com/video.mp4', 'video.mp4')")

# --- Start REPL ---
try:
    from IPython import embed
    embed(colors='neutral')  # type: ignore
except Exception:
    import code
    code.interact(local=globals())

