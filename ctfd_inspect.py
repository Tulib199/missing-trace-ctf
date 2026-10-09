import json

from ctfd_session import BASE, login

s = login()
challenges = s.get(BASE + "/api/v1/challenges?view=admin").json()["data"]
for c in challenges:
    print(c["id"], c["name"], "|", c["category"], c["value"], c["type"], c.get("state"))

sample = next((c for c in challenges if "Lost Park" in c["name"]), challenges[0])
cid = sample["id"]
print(json.dumps(s.get(f"{BASE}/api/v1/challenges/{cid}").json()["data"], indent=1)[:3000])
for sub in ["flags", "hints", "files", "tags"]:
    print(sub, s.get(f"{BASE}/api/v1/challenges/{cid}/{sub}").json())
print(s.get(BASE + "/api/v1/configs/ctf_name").json())
