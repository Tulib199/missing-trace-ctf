import base64
import json
import os
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

HERE = Path(__file__).parent
FLAG = "FLAG{LEGACYPROXY_0905_5_C}"
ITERATIONS = 250_000

SOLUTION = {
    "title": "How the trace went missing",
    "sections": [
        {"h": "Root cause: LEGACYPROXY",
         "p": "Change CHG-4471 rebuilt the Legacy App Proxy truststore from a baseline image, which removed the "
              "TraceCloud Issuing CA G2 intermediate that had been imported by hand under INC-20410. The proxy can "
              "still reach TraceCloud over TCP, but every TLS handshake fails. The hub reaches the same API directly "
              "with a valid certificate chain, and the vendor reports no incident, so the cloud and the firewall are "
              "healthy. The hub only reported the 504 errors that the proxy returned."},
        {"h": "Onset: 09:05",
         "p": "The graceful restart at 08:55:47 kept the existing pooled connections alive for max_age = 600 seconds. "
              "At 09:05:47 those connections expired, new handshakes failed, and the proxy marked the connector "
              "UNAVAILABLE. T1002 at 09:05:30 still succeeded on a pooled connection. Common traps: 09:06 (the hub's "
              "first error), 08:55 (restart), 08:52 (patch), and 09:10 (the ticket's estimate)."},
        {"h": "Replay count: 5",
         "p": "Replay T1003, T1004, T1006, T1007, and T1009. Do not replay T1008 (manual resend of T1006, same key "
              "RX-88419) or T1010 (rescan of the T1003 pallet, same key RX-88412). T1005 was rejected by ERP "
              "validation (blank lot number) and never reached the hub, so it must be fixed at the source. T1001 and "
              "T1002 succeeded, and TEST-DIRECT is only a health check. The dashboard said 8 missing; only 5 need replay."},
        {"h": "Long-term design: Option C",
         "p": "C removes the unnecessary proxy hop while keeping the hub so IT can still hold and retry messages. "
              "It ignores repeat sendings of the same pallet so resends and rescans cannot become duplicate records, "
              "and it alerts before operations notices. A waits longer on a failure that will never clear. B removes "
              "the hub, so there is no controlled place to hold and retry failures. D fixes the route but blindly "
              "resends every stuck message, which would post T1008 and T1010 as duplicates."},
        {"h": "Immediate recovery",
         "p": "Re-import the G2 intermediate into the proxy truststore (or roll back the CHG-4471 truststore) and reset "
              "the connector pool, or move traffic to the tested direct hub-to-cloud route under an emergency change. "
              "Replay only the five unique messages once, cancel the parked duplicates and void ERP receipt T1010, send "
              "T1005 back to receiving to correct the lot number, confirm ACKs and dashboard visibility, and tell the "
              "warehouse to stop resending and rescanning."},
        {"h": "Controls that would have caught it sooner",
         "p": "Alert on retry exhaustion or parked-queue age; turn dedupe_check on; run a synthetic end-to-end test "
              "transaction every few minutes; add a post-change TLS handshake check to the proxy patch procedure; "
              "monitor certificate chains."},
        {"h": "Next step",
         "p": "Complete the playtest feedback form and give it to the challenge author."},
    ],
}


def build():
    salt, iv = os.urandom(16), os.urandom(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERATIONS).derive(FLAG.encode())
    ct = AESGCM(key).encrypt(iv, json.dumps(SOLUTION).encode(), None)
    vault = {k: base64.b64encode(v).decode() for k, v in {"salt": salt, "iv": iv, "ct": ct}.items()}
    vault["iter"] = ITERATIONS

    html = (HERE / "game_template.html").read_text(encoding="utf-8")
    html = html.replace("/*__VAULT__*/null", json.dumps(vault))
    assert "LEGACYPROXY_0905" not in html and "Option C." not in html
    out = HERE / "The_Missing_Trace_Game.html"
    out.write_text(html, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    build()
