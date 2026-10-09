import os
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
URL = (HERE / "The_Missing_Trace_Game.html").as_uri()
SHOTS = Path(os.environ["TEMP"])

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome")
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: m.type == "error" and errors.append(m.text))
    page.goto(URL)
    page.screenshot(path=SHOTS / "game_intro.png")

    page.fill("#teamName", "Team Packet Tracers")
    page.click("#startBtn")
    page.locator(".site", has_text="Legacy App Proxy").click()
    page.click("#inspBody >> text=Suspect")
    page.locator(".site", has_text="Warehouse Scanner").click()
    page.click("#inspBody >> text=Healthy")
    page.click("#tabs >> text=C · Legacy App Proxy Log")
    page.click(".log div >> nth=6")
    page.click("text=1. Data Reconciliation Analyst")
    page.screenshot(path=SHOTS / "game_main.png")

    page.select_option("#fbComp", "HUB")
    page.fill("#fbTime", "0906")
    page.fill("#fbCount", "7")
    page.click("#fbOpt >> text=D")
    page.click("#submitBtn")
    page.wait_for_function("document.getElementById('feedback').textContent.includes('Incorrect')", timeout=15000)
    print("wrong:", page.text_content("#feedback").encode("ascii", "replace").decode(), "| score", page.text_content("#score"), "| attempts", page.text_content("#attempts"))
    page.locator("#recon").scroll_into_view_if_needed()
    page.screenshot(path=SHOTS / "game_builder.png", full_page=True)

    page.fill("#manualFlag", "FLAG{LEGACYPROXY_0905_5_C}")
    page.click("#submitBtn")
    page.wait_for_selector("#win:not(.hidden)", timeout=15000)
    page.wait_for_timeout(600)
    print("win:", page.text_content("#winTeam"), "| score", page.text_content("#winScore"))
    page.screenshot(path=SHOTS / "game_win.png")

    page.reload()
    print("after reload attempts:", page.text_content("#attempts"), "| intro hidden:", "hidden" in page.get_attribute("#intro", "class"))
    print("errors:", errors)
    browser.close()
