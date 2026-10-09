import re

import requests
import truststore

truststore.inject_into_ssl()

BASE = "https://demo.ctfd.io"


def login(user="admin", password="password"):
    s = requests.Session()
    r = s.get(BASE + "/login")
    nonce = re.search(r'name="nonce"[^>]*value="([^"]+)"', r.text)
    nonce = nonce.group(1) if nonce else re.search(r"csrfNonce\W+\"([^\"]+)", r.text).group(1)
    r = s.post(BASE + "/login", data={"name": user, "password": password, "nonce": nonce})
    r = s.get(BASE + ("/admin/challenges" if user == "admin" else "/challenges"))
    if "/login" in r.url:
        raise SystemExit("login failed")
    s.headers["CSRF-Token"] = re.search(r"csrfNonce\W+\"([^\"]+)", r.text).group(1)
    return s
