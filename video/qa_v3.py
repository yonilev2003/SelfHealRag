"""Full QA pass on video/demo_page_v3.html: cold start sync, mid-video seek,
pause/resume, caption toggle, console errors, narration-vs-video timing.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
PAGE = REPO / "video" / "demo_page_v3.html"

console_msgs = []
results = {}

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/opt/pw-browsers/chromium",
        args=["--autoplay-policy=no-user-gesture-required"],
    )
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.on("console", lambda m: console_msgs.append(f"[{m.type}] {m.text}"))
    page.on("pageerror", lambda e: console_msgs.append(f"[pageerror] {e}"))

    page.goto(f"file://{PAGE}")
    page.wait_for_selector("#v3video")

    # --- Cold start: play from t=0 ---
    page.evaluate("document.getElementById('v3video').play()")
    page.wait_for_timeout(2000)
    r = page.evaluate("""() => {
        const v = document.getElementById('v3video');
        const a0 = document.getElementById('beat0_hook');
        return {videoTime: v.currentTime, videoPaused: v.paused, audioPaused: a0.paused, audioTime: a0.currentTime};
    }""")
    results["cold_start"] = r

    # --- Pause/resume ---
    page.evaluate("document.getElementById('v3video').pause()")
    page.wait_for_timeout(500)
    r_pause = page.evaluate("""() => {
        const audios = ['beat0_hook','beat1_evidence','beat2_baselines','beat3_selfheal','beat4_verifier','beat5_frozentest','beat6_scale','beat7_lesson','beat8_closing'];
        return audios.map(id => ({id, paused: document.getElementById(id).paused}));
    }""")
    results["pause_all_narration_stopped"] = r_pause
    page.evaluate("document.getElementById('v3video').play()")
    page.wait_for_timeout(1000)
    r_resume = page.evaluate("""() => {
        const v = document.getElementById('v3video');
        return {videoPaused: v.paused, videoTime: v.currentTime};
    }""")
    results["resume"] = r_resume

    # --- Mid-video seek: seek into beat4 (verifier), e.g. t=115 (15s into a 31.3s beat) ---
    page.evaluate("document.getElementById('v3video').currentTime = 115")
    page.wait_for_timeout(1500)
    r_seek = page.evaluate("""() => {
        const v = document.getElementById('v3video');
        const a4 = document.getElementById('beat4_verifier');
        const others = ['beat0_hook','beat1_evidence','beat2_baselines','beat3_selfheal','beat5_frozentest','beat6_scale','beat7_lesson','beat8_closing']
            .map(id => ({id, paused: document.getElementById(id).paused}));
        return {videoTime: v.currentTime, a4_paused: a4.paused, a4_currentTime: a4.currentTime, others};
    }""")
    results["mid_seek_beat4"] = r_seek

    # --- Seek near end of a beat, verify it doesn't misfire into wrong track ---
    page.evaluate("document.getElementById('v3video').currentTime = 250")  # near end, beat8
    page.wait_for_timeout(1000)
    r_seek_end = page.evaluate("""() => {
        const v = document.getElementById('v3video');
        const a8 = document.getElementById('beat8_closing');
        return {videoTime: v.currentTime, a8_paused: a8.paused, a8_currentTime: a8.currentTime};
    }""")
    results["seek_near_end"] = r_seek_end
    page.evaluate("document.getElementById('v3video').pause()")

    # --- Caption toggle ---
    r_track_default = page.evaluate("""() => {
        const track = document.getElementById('captions').track;
        return {mode: track.mode, cueCount: track.cues ? track.cues.length : null};
    }""")
    results["captions_default_mode"] = r_track_default
    page.evaluate("document.getElementById('captions').track.mode = 'hidden'")
    r_track_hidden = page.evaluate("document.getElementById('captions').track.mode")
    results["captions_hidden_after_toggle"] = r_track_hidden
    page.evaluate("document.getElementById('captions').track.mode = 'showing'")
    r_track_showing = page.evaluate("document.getElementById('captions').track.mode")
    results["captions_showing_after_toggle_back"] = r_track_showing

    # Screenshot at a mid-point for visual sanity
    page.evaluate("document.getElementById('v3video').currentTime = 65")
    page.wait_for_timeout(600)
    page.screenshot(path=str(REPO / "video" / "recording" / "qa_final_page.png"))

    browser.close()

import json
print(json.dumps(results, indent=2))
print(f"\nConsole messages ({len(console_msgs)}):")
for m in console_msgs:
    print(" ", m)
