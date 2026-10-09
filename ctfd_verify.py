from ctfd_session import BASE, login

CID = 6
s = login()
c = s.get(f"{BASE}/api/v1/challenges/{CID}").json()["data"]
print(c["name"], "|", c["category"], c["value"], c["state"], "max_attempts", c["max_attempts"])
print("tags", c["tags"])
print("hints", [(h["id"], h["cost"]) for h in c["hints"]])
print("files", c["files"])
print("flags", s.get(f"{BASE}/api/v1/challenges/{CID}/flags").json()["data"])
for f in c["files"]:
    r = s.get(BASE + f)
    print(r.status_code, r.headers.get("content-type"), len(r.content))
for guess in ["FLAG{LEGACYPROXY_0905_5_C}", "FLAG{HUB_0906_7_D}", "flag{legacyproxy_0905_5_c}"]:
    r = s.post(f"{BASE}/api/v1/challenges/attempt?preview=true", json={"challenge_id": CID, "submission": guess})
    print(guess, "->", r.json().get("data"))
print([x["name"] for x in s.get(BASE + "/api/v1/challenges").json()["data"]])
