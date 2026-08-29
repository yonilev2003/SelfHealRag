"""Records video/beats.html (V3, 9 beats, 251.168s real narration timeline)
via Playwright, real-time capture matching V1/V2's pipeline. Video-only
(this ffmpeg build has no audio encoder) -- audio is added as separate
synced <audio> elements in the final page, per video/demo_page.html's
established pattern.
"""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
BEATS_HTML = REPO / "video" / "beats.html"
OUT_DIR = REPO / "video" / "recording"
OUT_DIR.mkdir(exist_ok=True)
TOTAL_S = 251.168
BUFFER_S = 2.5  # small tail buffer so the closing beat's final frame is captured

console_messages = []

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        record_video_dir=str(OUT_DIR),
        record_video_size={"width": 1280, "height": 720},
    )
    page = context.new_page()
    page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
    page.on("pageerror", lambda exc: console_messages.append(f"[pageerror] {exc}"))

    page.goto(f"file://{BEATS_HTML}")
    t0 = time.time()
    time.sleep(TOTAL_S + BUFFER_S)
    elapsed = time.time() - t0

    video_path = page.video.path()
    context.close()
    browser.close()

print(f"Recorded {elapsed:.1f}s wall-clock (target {TOTAL_S + BUFFER_S:.1f}s)")
print(f"Video saved to: {video_path}")
print(f"Console messages ({len(console_messages)}):")
for m in console_messages:
    print(" ", m)
