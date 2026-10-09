from pathlib import Path

from ctfd_session import BASE, login

HERE = Path(__file__).parent
NAME = "The Missing Trace"
FLAG = "FLAG{LEGACYPROXY_0905_5_C}"

DESCRIPTION = r"""
**Real-Time Data Integration and Process Optimization** | Team of 3-4 | Target time: 45 minutes
*Author: Meghana Sinha (CITM-501, Assignment 6.6)*

NorthBridge Health Supply is a fictional distributor of serialized medical products. Every pallet received at the warehouse is scanned, posted to the ERP system, and passed in real time through an integration layer to a cloud traceability platform. Regulators and hospital customers rely on that platform to prove where each serialized item has been.

At 09:30 this ticket arrives at the service desk:

```
INC-20931  Priority: High  Opened: 09:30  Caller: Warehouse Operations Lead
"The traceability dashboard is showing 8 receipts missing since about 09:10. They are all in
 the ERP. My team has been resending and rescanning to try to push them through. Please fix
 this before the 11:00 hospital shipment cut-off."
```

Your team is the integration support group. Determine **which component failed**, **exactly when it started failing**, **how many unique business transactions need to be recovered**, and **which long-term design prevents a repeat**.

All evidence you need is on this page. Your facilitator can also provide the printable packet with a Team Answer Sheet for documenting your reasoning.

---

### How to play as a team

| Role | Primary evidence | Delivers to the team |
|---|---|---|
| 1. Data Reconciliation Analyst | A, G | Which missing receipts are unique, duplicates, or never reached the integration layer |
| 2. Log Analyst | B, C, H | Exact time the root-cause component began failing, and what changed |
| 3. Infrastructure Analyst | D, E | Which network path / component is broken and which are healthy |
| 4. Solutions Architect | F + findings from 1-3 | The option that prevents recurrence without creating new data-quality risk |

Combine roles 3 and 4 for a team of three. Work in parallel for about 20 minutes, then regroup.

### Rules
- Use only the evidence provided. No outside lookups are needed.
- The component that *reports* an error is not necessarily the component that *caused* it.
- A "missing" receipt on the dashboard is not automatically a failed integration message.
- Separate retries, manual resends, and rescans from unique business transactions.
- The flag is checked character-for-character. **You have 10 attempts.**

### System flow
`Warehouse Scanner (VLAN 30)` -> `ERP Receiving` -> `Integration Hub` -> `Legacy App Proxy :8443` -> `Traceability Cloud :443` -> `Operations Dashboard`

ERP creates a Match ID from the purchase order and the serial numbers on the pallet. If two rows have the same Match ID, they are the same physical pallet — even if the transaction IDs are different. Duplicate serial records in the cloud platform trigger compliance holds.

---

### Evidence A - Transaction Timeline (ERP + Dashboard export, 09:29)

| Txn ID | ERP Time | ERP Status | PO | Match ID | Hub Status | Cloud Ack | Dashboard |
|---|---|---|---|---|---|---|---|
| T1001 | 09:02:14 | Posted | PO-5510 | RX-88410 | Forwarded | ACK-200 | Visible |
| T1002 | 09:05:29 | Posted | PO-5511 | RX-88411 | Forwarded | ACK-200 | Visible |
| T1003 | 09:06:11 | Posted | PO-5512 | RX-88412 | Parked | None | Missing |
| T1004 | 09:08:08 | Posted | PO-5513 | RX-88415 | Parked | None | Missing |
| T1005 | 09:10:03 | Rejected (VAL-112) | PO-5514 | - | Not received | None | Missing |
| T1006 | 09:11:30 | Posted | PO-5515 | RX-88419 | Parked | None | Missing |
| T1007 | 09:14:17 | Posted | PO-5516 | RX-88421 | Parked | None | Missing |
| T1008 | 09:18:04 | Posted | PO-5515 | RX-88419 | Parked | None | Missing |
| T1009 | 09:21:39 | Posted | PO-5517 | RX-88426 | Parked | None | Missing |
| T1010 | 09:23:01 | Posted | PO-5512 | RX-88412 | Parked | None | Missing |
| TEST-DIRECT | 09:25:10 | N/A | - | - | Health test | HTTP 200 | N/A |

VAL-112 = the ERP rejected the receipt because the lot number was blank. Rejected receipts are never sent to the hub.

### Evidence B - Integration Hub Log
```
08:00:00  CONFIG  retry_max=3  retry_interval=30s  dedupe_check=OFF  parked_queue_alert=OFF
09:02:15  MSG T1001  key=RX-88410  route=legacy-proxy:8443  attempt=1  result=HTTP_200  ack=ACK-200
09:05:30  MSG T1002  key=RX-88411  route=legacy-proxy:8443  attempt=1  result=HTTP_200  ack=ACK-200
09:06:12  MSG T1003  key=RX-88412  route=legacy-proxy:8443  attempt=1  result=HTTP_504_GATEWAY_TIMEOUT
09:06:42  MSG T1003  key=RX-88412  route=legacy-proxy:8443  attempt=2  result=HTTP_504_GATEWAY_TIMEOUT
09:07:12  MSG T1003  key=RX-88412  route=legacy-proxy:8443  attempt=3  result=RETRY_EXHAUSTED  status=PARKED
09:08:09  MSG T1004  key=RX-88415  route=legacy-proxy:8443  attempts=3  result=RETRY_EXHAUSTED  status=PARKED
09:11:31  MSG T1006  key=RX-88419  route=legacy-proxy:8443  attempts=3  result=RETRY_EXHAUSTED  status=PARKED
09:14:18  MSG T1007  key=RX-88421  route=legacy-proxy:8443  attempts=3  result=RETRY_EXHAUSTED  status=PARKED
09:18:05  MSG T1008  key=RX-88419  source=MANUAL_RESEND  attempts=3  result=RETRY_EXHAUSTED  status=PARKED
09:21:40  MSG T1009  key=RX-88426  route=legacy-proxy:8443  attempts=3  result=RETRY_EXHAUSTED  status=PARKED
09:23:02  MSG T1010  key=RX-88412  source=ERP_RECEIPT  attempts=3  result=RETRY_EXHAUSTED  status=PARKED
09:25:10  TEST-DIRECT  route=tracecloud-api:443 (temporary rule FW-TMP-77)  result=HTTP_200  health=OK
```

### Evidence C - Legacy App Proxy Log
```
08:52:10  CHG-4471  OS security patch applied; relay configuration reloaded
08:52:11  truststore=/opt/lap/certs rebuilt from baseline image  entries=112
08:55:47  graceful restart completed; existing upstream pool connections retained  max_age=600s
09:02:15  relay T1001  upstream=tracecloud-api:443  pooled_conn=7  status=200
09:05:30  relay T1002  upstream=tracecloud-api:443  pooled_conn=3  status=200
09:05:47  pool=tracecloud  all pooled connections reached max_age; opening new upstream connections
09:05:47  upstream TLS handshake failed: unable to get local issuer certificate (TraceCloud Issuing CA G2)
09:05:47  connector_pool=tracecloud  status=UNAVAILABLE
09:06:12  inbound session accepted from integration-hub
09:06:42  upstream connection not established before timeout (30s); returned 504 to client
09:08:09  upstream connection not established before timeout (30s); returned 504 to client
09:11:31  upstream connection not established before timeout (30s); returned 504 to client
   ...    (same pattern repeats for every relay request through 09:23:02)
```

### Evidence D - Connectivity Tests (Network Team, 09:25-09:28)

| Source | Destination | Test | Result |
|---|---|---|---|
| Warehouse scanner (VLAN 30) | ERP Receiving :443 | HTTPS | Success |
| ERP server | Integration Hub :443 | TCP | Success |
| Integration Hub | Legacy App Proxy :8443 | TCP | Success (4 ms) |
| Integration Hub | Legacy App Proxy :8443 | POST /relay/tracecloud | HTTP 504 after 30 s |
| Legacy App Proxy | TraceCloud API :443 | TCP | Success (22 ms) |
| Legacy App Proxy | TraceCloud API :443 | TLS handshake | Failed - certificate verify failed (unknown issuer) |
| Integration Hub | TraceCloud API :443 | HTTPS health check via FW-TMP-77 | HTTP 200 - certificate chain valid (Issuing CA G2) |
| User workstation | Operations Dashboard | HTTPS | Success |

### Evidence E - External Platform Status (TraceCloud Status Page, 09:27)
All systems operational. No active incident. API health endpoint responding normally. No maintenance window in progress. Inbound processing normal for all regions during the last 24 hours.

*Notice (posted Sep 28):* TraceCloud replaced its security certificate with a newer one called "TraceCloud Issuing CA G2." Any customer that keeps its own list of trusted certificates must add the new G2 certificate. Everyday browsers and public lists already include it.

### Evidence F - Architecture Options
- **Option A** - Keep sending data through the old proxy. Give the hub more time (30 seconds to 2 minutes) and more retries (3 to 10) so short delays can clear on their own.
- **Option B** - Connect the ERP straight to the cloud and shut down both the hub and the old proxy, so there are fewer systems that can break.
- **Option C** - Keep the hub so IT can still hold and retry messages. Stop using the old proxy and send data from the hub straight to the cloud on an approved secure connection. Ignore repeat sendings of the same pallet so resends do not create duplicate records, and alert the team when messages sit unsent for too long.
- **Option D** - Keep the hub and stop using the old proxy; send data from the hub straight to the cloud. Add a job that automatically resends every stuck message every 15 minutes.

### Evidence G - Warehouse Scanner & Operations Log
```
09:06:05  WH-SCN-02  user=wh.recv1  PO-5512  pallet scanned  serials=48  lot=L24-0912
09:10:01  WH-SCN-04  user=wh.recv3  PO-5514  pallet scanned  serials=36  lot=<blank>  label damaged
09:11:24  WH-SCN-02  user=wh.recv1  PO-5515  pallet scanned  serials=60  lot=L24-0915
09:17:40  OPS-DESK   user=wh.ops2   "PO-5515 not on dashboard - used ERP Resend button"
09:20:55  WH-SCN-04  user=wh.recv3  PO-5512  pallet RESCANNED  serials=48  lot=L24-0912
                     note="not visible on dashboard, scanning again"
09:24:30  OPS-DESK   user=wh.ops2   "Told team to stop rescanning until IT responds"
```

### Evidence H - Change Calendar (Today)

| Change | Window | System | Description | Status |
|---|---|---|---|---|
| CHG-4460 | 08:30-08:40 | Firewall | Rule update on warehouse wireless VLAN 30 (scanner network) | Completed |
| CHG-4471 | 08:50-09:00 | Legacy App Proxy | Monthly OS security patch and config reload. Risk: Low. "No user impact expected." | Completed |
| CHG-4475 | 22:00-23:00 | ERP | Monthly database index maintenance | Scheduled |
| INC-20410 | Sep 28 | Legacy App Proxy | Manually imported TraceCloud Issuing CA G2 into proxy truststore after vendor rotation | Closed |

---

### Your tasks
1. **Root cause** - Identify the root-cause component (use the codes below).
2. **Onset** - The time (HH:MM, 24-hour) at which the root-cause component *itself* first became unable to deliver data.
3. **Recovery scope** - How many unique business transactions must be replayed through the integration layer? Do not count resends, rescans, or receipts that never reached the hub.
4. **Immediate recovery** - The safest immediate recovery action, including what to do with duplicates and non-integration items *(answer sheet)*.
5. **Long-term design** - The option (A, B, C, or D) that best prevents recurrence while preserving real-time processing and data integrity.
6. **Control** - One monitoring or control improvement that would have detected this before operations did *(answer sheet)*.

**Component codes:** `SCANNER` `FIREWALL` `ERP` `HUB` `LEGACYPROXY` `TRACECLOUD` `DASHBOARD`

### Flag format
```
FLAG{<COMPONENT_CODE>_<ONSET_HHMM>_<UNIQUE_REPLAY_COUNT>_<OPTION_LETTER>}
```
Uppercase, no spaces, no colon in the time. Format example only (not the answer): `FLAG{ERP_1342_3_A}`
""".strip()

HINTS = [
    ("Line up the Match ID column. Two different transaction IDs can describe the same physical pallet. "
     "Also check whether every missing receipt actually reached the hub.", 50),
    ("The hub records when it *noticed* the failure, not when the failure began. Find the earliest line where "
     "the failing component reports its own problem, and ask why it happened then rather than right after the restart.", 100),
]
TAGS = ["Data Integration", "Troubleshooting", "Team (3-4)", "45 min"]
FILES = ["The_Missing_Trace_Challenge_Packet.pdf", "Assignment_6.6_CTF_Challenge_Packet_MS_v2.docx"]


def main():
    s = login()
    fields = {
        "name": NAME,
        "category": "Real-Time Data Integration",
        "description": DESCRIPTION,
        "value": 500,
        "max_attempts": 10,
    }
    existing = [c for c in s.get(BASE + "/api/v1/challenges?view=admin").json()["data"] if c["name"] == NAME]
    if existing:
        cid = existing[0]["id"]
        s.patch(f"{BASE}/api/v1/challenges/{cid}", json=fields).raise_for_status()
        print("updated challenge id", cid)
    else:
        r = s.post(BASE + "/api/v1/challenges", json={**fields, "type": "standard", "state": "hidden"})
        r.raise_for_status()
        cid = r.json()["data"]["id"]
        print("created challenge id", cid)

    def current(kind):
        return s.get(f"{BASE}/api/v1/challenges/{cid}/{kind}").json()["data"]

    if not any(f["content"] == FLAG for f in current("flags")):
        s.post(BASE + "/api/v1/flags", json={"challenge": cid, "content": FLAG, "type": "static",
                                             "data": "case_sensitive"}).raise_for_status()
    have_hints = {h["content"] for h in current("hints")}
    for content, cost in HINTS:
        if content not in have_hints:
            s.post(BASE + "/api/v1/hints", json={"challenge": cid, "content": content,
                                                 "cost": cost}).raise_for_status()
    have_tags = {t["value"] for t in current("tags")}
    for tag in TAGS:
        if tag not in have_tags:
            s.post(BASE + "/api/v1/tags", json={"challenge": cid, "value": tag}).raise_for_status()
    have_files = {f["location"].split("/")[-1] for f in current("files")}
    for name in FILES:
        if name in have_files:
            continue
        with open(HERE / name, "rb") as fh:
            s.post(BASE + "/api/v1/files", data={"challenge": cid, "type": "challenge", "nonce": s.headers["CSRF-Token"]},
                   files={"file": (name, fh)}).raise_for_status()

    s.patch(f"{BASE}/api/v1/challenges/{cid}", json={"state": "visible"}).raise_for_status()
    print(f"{BASE}/challenges#{NAME.replace(' ', '%20')}-{cid}")


if __name__ == "__main__":
    main()
