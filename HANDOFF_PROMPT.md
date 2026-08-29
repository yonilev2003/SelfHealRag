# Handoff prompt — paste this at the start of a new session

This file exists so continuity across sessions is itself disclosed, not just
convenient. It is rewritten at the end of every phase/session (per standing
instruction) so a brand-new session — or a context-compacted one — can pick
up cold with zero information loss. Paste the text below as the first
message in a fresh session, or just point Claude at this file. The user's
own way of resuming is to say: **"start session from where we stopped
before."**

---

## מצב עדכני — הגשה גמורה ומוגשת-ready; עובדים על V3 של הוידאו (בהפסקה, חסום על ElevenLabs)

זה ריפו של הגשה יחידה ל-**micro1 Agentic Workflows Hackathon** (28–31/8/2026,
דדליין **30/8 23:59 UTC = 31/8 02:59 שעון ישראל**, אין הארכות. היום: 29/8).

### מהו SelfHeal RAG (הקונספט)

מערכת RAG על מסמכי מדיניות חברה (handbook) שמזהה תשובות שהתיישנו — עובדה
השתנתה (טיקט/ביקורת), אבל התיעוד לא עודכן — ומתקנת את עצמה **בזמן אמת**, על
כל שאילתה, דרך ערוץ "אותות תיקון" (`data/correction_signals.json`) שאף
baseline לא מקבל. הטענה המרכזית היא **קטגורית, לא אמפירית**: התשובה הנכונה
פשוט לא קיימת בקורפוס, אז "לקרוא יותר" (A0, כל הקורפוס בקריאה אחת) ו"לחשוב
יותר זמן" (B, agent חופשי עם כלים) שניהם נכשלים באותה מידה — רק ערוץ memory
נפרד סוגר את הפער. יש גם verifier דטרמיניסטי נפרד שתופס ציטוטים מיושנים
מתוך שרשראות-החלפה בתוך הקורפוס עצמו (לא תלוי ב-memory).

### מצב ההגשה בפועל

**הקוד, ה-eval, התוצאות, README, CHANGELOG, PROCESS.md, COMPLIANCE.md,
PRODUCTION_ROADMAP.md — כולם גמורים ונעולים.** `submission.zip` נבנה בעבר
(~5MB, מתחת ל-50MB cap). audit agent מלא (39 tool calls) עבר PASS מלא על כל
הריפו: אין oracle leakage, מספרי README תואמים ל-`results/*`, אין
TODO/placeholder, כל ה-unit tests ירוקים, אין secrets. **הדבר היחיד שעוד
בעבודה הוא הוידאו** — גרסה V2 חיה ועובדת ב-Artifact, גרסה V3 (שדרוג) בעבודה
אבל לא פורסמה.

### Frozen boundaries — אסור לגעת בלי אישור מפורש

- `data/corpus/`, `data/probes/test_split.locked.json`,
  `data/fact_registry.json`, `data/correction_signals.json` — קורפוס+split
  נעולים ב-SHA-256. **לא לגעת.**
- `results/*.json/csv`, `results/test_run_log.md`,
  `results/ablations_summary.json`, `results/results_table.json` — התוצאות
  הרשמיות. **לא לגעת, לא "לתקן" מספרים.**
- `trajectories/raw/*.jsonl` — נלכדות מסשן אמיתי, **לא לערוך ידנית.**
- כל טענת מספר בכל מקום (README/CHANGELOG/וידאו) חייבת להתאים בדיוק למה
  שב-`results/`. אם V3 משנה טקסט שמצטט מספרים — לוודא התאמה.

## מה כבר נעשה ב-V1 → V2 של הוידאו (context, לא לחזור עליו)

- **V1** (שקט, ללא narration): 6 beats, `video/beats.html`, נקלט
  ב-Playwright (`record_video_dir`, 1280×720), דחוס ב-ffmpeg
  (`/opt/pw-browsers/ffmpeg-1011/ffmpeg-linux` — **build מוגבל: וידאו
  VP8/webm בלבד, אין audio encoder מקומפל בכלל**, אז אודיו תמיד שכבה נפרדת
  מסונכרנת ב-JS, לא מעורבב לקובץ).
- **V1.5** (narration + מוזיקה): נוספו 6 קטעי narration
  (`eleven_multilingual_v2`, קול "River") + bed אמביינטי. משוב אמיתי
  מהמשתמש: הקול נשמע "מוזר מאוד", המוזיקה "קצת מוזרה", מתחרה עם ה-narration.
- **V2** (הגרסה החיה כרגע): הוסרה המוזיקה לגמרי (החלטה מנומקת, לא מתוך
  אינרציה). Redesign מלא: פתיחה שקופצת ישר ל-clash $200 מול $250 בשניות
  הראשונות, pipeline-stepper עקבי, ערכי-מפתח מודגשים עם pulse, JSON
  structure מעומעם מול value lines בולטות. כיתובים הוחלפו מ-baked-in text
  ל-`<track kind="subtitles">` WebVTT אמיתי עם toggle (`textTrack.mode`
  showing/hidden, מאומת ב-Playwright). משך: 304s. גודל עמוד: 6.41MB.
  **חי כרגע ב-**: https://claude.ai/code/artifact/42418c8e-e0fd-4ce8-90c9-fd7eca0ccaf0
  (מקושר מ-README/VIDEO_SCRIPT/SUBMISSION.md — **לא נגעתי בקישור, לא נגעתי
  ב-`video/demo_page.html` עצמו** — V2 עדיין הגרסה החיה עד ש-V3 עם narration
  אמיתי מוכן ועובר QA).

## למה V3 נבנית

בקשה מפורשת ומפורטת מהמשתמש (לא רפאקטור קוסמטי): לעשות את הוידאו יותר
מרתק/קולנועי — פחות אוויר מת, narration יותר "חי" ודינמי, pacing טוב יותר,
אנקדוטות עסקיות/יצירתיות **בלי המצאת מספרים** (rule קשיח), hook תוך 5-10
שניות, closing שממוסגר כ-vision. משוב "dead air" הגיע מצפייה אמיתית ב-V2 —
**אין לי timestamps מדויקים שמורים מהצפייה ההיא** (לא נשמרו verbatim לפני
ה-compaction של השיחה); אם רלוונטי, לצפות שוב ב-V2 לזהות רגעים ספציפיים של
אוויר מת לפני שממשיכים לבנות V3 יותר לעומק. התחושה הכללית שהועברה: רגעי
"reveal" ב-JSON היו שקטים מדי/סטטיים מדי, מה שהוביל ל-V3's sub-beat reveal
system (ראה למטה).

## מבנה V3 — 9 beats (לא 8, תוקן בסיבוב הזה)

`video/beats.html` נכתב מחדש מאפס ל-V3. **מבנה חדש, timeline חדש (217s
provisional, יוחלף במשכי audio אמיתיים):**

| # | id | start–end (provisional) | תוכן |
|---|-----|------|------|
| 0 | b0 | 0–12s | Cold open/hook: "$250 שינו אתמול, ה-AI עדיין אומר $200" |
| 1 | b1 | 12–30s | Evidence: clash $200/$250 + 2 filecards (handbook vs ticket) |
| 2 | b2 | 30–54s | Baselines fail: A0 + B שניהם עונים $200 בטרמינל |
| 3 | b3 | 54–92s | SelfHeal fires — live, עם sub-reveals: wait-dots ב-+5s,
  memory-write JSON ב-+12s, final answer ב-+20s (מתוך תחילת ה-beat) |
| 4 | b4 | 92–115s | Verifier: תופס ציטוט VPN מיושן, עוקף עם reason |
| 5 | b5 | 115–140s | Frozen 16-case table, progressive row-reveal (~1.6s
  בין שורה לשורה), subtitle ב-+9s |
| 6 | b6 | 140–160s | Scale/economics anecdote (עובד יחיד מול 10,000 עובדים —
  **אין מספר כלכלי ממציא, נשאר ברמת אנלוגיה**) |
| 7 | b7 | 160–190s | The lesson / hot take: הבאג האמיתי של ה-frozen-test |
| 8 | b8 | 190–217s | Closing/vision — `.vision-tag` אומר מפורשות "vision,
  not yet built — see PRODUCTION_ROADMAP.md" |

**באג שתוקן הרגע בסשן הזה:** `#stepper` היה עם 8 `.step` בלבד מול 9
`.beat` divs — beat b8 (Closing) לא היה לו step מתאים ב-stepper. תוקן
בהוספת `<div class="step" data-i="8">Closing</div>`, מאומת ב-Playwright:
9 steps / 9 beats, `Closing` נדלק נכון ב-t=205s. **זה כבר commit-ed.**

### Visuals שכבר מוכנים (לא צריך לבנות מחדש)

כל 9 ה-beats ויזואלית **גמורים ומאומתים**: cold open עם `.megaline`/
`.megasub`, evidence clash עם 2 filecards, baselines-fail terminal, SelfHeal
sub-reveal sequence (cursor blink → wait-dots → JSON reveal → final answer
pulse), verifier terminal, frozen-test table עם progressive row reveal,
scale/closer anecdote, lesson text, closing/vision עם explicit
"not yet built" tag. נבדק חזותית ב-Playwright screenshots ב-t=3,18,40,58,
68,78,100,118,130,148,172,205 — הכל נראה נקי. **מה שחסר זה רק ה-audio
layer** (narration אמיתי) ותזמון מדויק שמבוסס עליו (הזמנים הנוכחיים הם
הערכת מילים/170wpm, provisional).

## למה זה חסום — ElevenLabs connector

`ListConnectors` מראה `connected: true` ברמת החשבון אבל
`enabledInChat: false`. `ToolSearch` על כלי ElevenLabs (speech/voice)
החזיר "No matching deferred tools found" בכל בדיקה (4+ ניסיונות בשיחה
הקודמת, כולל פעמיים אחרי שהמשתמש אמר "מחובר!" ונסה לחבר מחדש). **זה לא
משהו שסבב ניסיון נוסף מהצד שלי צפוי לפתור** — נבדק שוב ושוב עם אותה תוצאה
שלילית. **חשוב: לא להשתמש ב-Hugging Face TTS כתחליף** — המשתמש דחה את זה
מפורשות ("אין סיבה להכניס ספק חדש ולא מוכח"), רף איכות הקול חשוב וקיים
חשבון ElevenLabs Starter אמיתי.

**צעד ראשון בסשן חדש: לבדוק אם ה-ElevenLabs connector זמין עכשיו**
(`ToolSearch` על "eleven" / "voice" / "speech", או `ListConnectors`). אם כן
— אפשר לגשת ישירות דרך ה-MCP tools (`creative_list_voices`,
`creative_generate_speech` עם `eleven_v3`, וכו') בלי צורך ב-Studio prompt
package. אם לא — להשתמש בחבילה למטה כדי לייצר ידנית ב-ElevenLabs Studio
(דרך הדפדפן של המשתמש, לא מהסשן המרוחק הזה).

## חבילת Prompt ל-ElevenLabs Studio (Option 2 — נשקל practical, לשימוש ידני)

**החלטה קודמת בשיחה:** Option 2 (workflow single-prompt-driven ב-Studio)
נשקל **genuinely practical** — עם caveat כן ש-mechanics המדויקים של ה-UI
הנוכחי לא אומתו בפועל (אין גישת דפדפן חיה מהסביבה המרוחקת). המשתמש צריך
לבצע את זה בעצמו ב-ElevenLabs Studio, או שסשן חדש עם ה-connector זמין יכול
לייצר ישירות דרך ה-MCP tools.

### הגדרה
1. Studio project חדש, מודל **`eleven_v3`** (יותר expressive מ-multilingual_v2,
   תומך תגיות inline כמו `[pause]`).
2. **לבדוק 2-3 קולות לפני בחירה סופית** — לא לבחור על העין. קריטריון: קול
   טבעי, בטוח בעצמו (confident), עם נימה של סקרנות (curious) — לא
   promotional, לא רובוטי. להשתמש במשפט הבדיקה (~15 שניות) למטה על כל קול
   מועמד לפני שמחליטים.
3. משפט בדיקה מוצע (טבעי, לא סופר טכני, מבחן את הטון): *"Here's the thing
   nobody tells you about AI systems in production — the hard part was
   never getting an answer. It was knowing when the answer you already
   trusted had quietly gone stale."*

### 9 קבצי narration (שם קובץ ← טקסט), ~217s כולל, `eleven_v3`

**Chapter 1 — `beat0_hook.mp3`** (~12s, hook תוך 5-10 שניות):
> Your company changed the price to two hundred fifty dollars. Yesterday.
> [pause] Your AI still confidently tells every employee... two hundred.

**Chapter 2 — `beat1_evidence.mp3`** (~18s):
> Here's the evidence. On the left, the handbook — still says two hundred.
> On the right, the finance ticket that actually approved the raise — two
> hundred fifty. [pause] Nobody updated the handbook.

**Chapter 3 — `beat2_baselines.mp3`** (~24s):
> Two strong baselines. Same wrong answer. [pause] Full context — every
> document, one call — still two hundred. An unrestricted agent, free to
> read anything it wants, for as long as it wants — also two hundred.
> [pause] More reading doesn't fix this, because the right answer simply
> isn't written down anywhere in the documents.

**Chapter 4 — `beat3_selfheal.mp3`** (~38s, dramatic, 3 `[pause]` tags —
timing שלהם צריך לעקוב אחרי sub-reveal ב-JS: wait-dots +5s, JSON reveal
+12s, final answer +20s מתוך תחילת ה-beat):
> Now watch what happens differently. [pause] The entity isn't in memory
> yet — so instead of guessing, SelfHeal checks a signal feed no baseline
> gets: a stand-in for the ticket system this bot was never connected to.
> [pause] Found it. Ticket 4521. Writing it to memory, right now, live.
> [pause] Final answer: two hundred fifty — cited as memory, not a lookup
> trick. This runs on every single query, continuously, not just once
> during tuning.

**Chapter 5 — `beat4_verifier.mp3`** (~23s):
> There's a second safety net, independent of memory entirely. [pause] A
> deterministic verifier — no model call, no guessing — checks every
> citation against the corpus's own supersession chain. Here it catches a
> generator that cited a stale January policy, overrides it with the
> current one, and flags it for human review.

**Chapter 6 — `beat5_frozentest.mp3`** (~25s):
> Here's the proof, on sixteen test cases the system never saw during
> development. [pause] Every baseline: zero out of three, on the category
> this was built for. SelfHeal: three for three. [pause] Flip memory off,
> change nothing else — back to zero. One capability. That's the entire
> difference.

**Chapter 7 — `beat6_scale.mp3`** (~20s):
> Think about the scale for a second. One employee getting the wrong number
> is an annoyance. [pause] Ten thousand employees getting it — that's not a
> bug anymore. That's an operating-system problem for your company's own
> knowledge.

**Chapter 8 — `beat7_lesson.mp3`** (~30s):
> The first time I ran this frozen test, SelfHeal tied the baseline. Zero
> out of three, on the exact case it was built for. Not a crash — just a
> quiet, forgettable number, the kind you could rationalize away under
> deadline pressure. [pause] The bug: memory only ever learned from
> training-time data, never from what it was actually being asked, live.
> [pause] A good held-out test doesn't just measure whether you generalize
> — it catches you lying to yourself about scope. Silently.

**Chapter 9 — `beat8_closing.mp3`** (~27s, vision-framed):
> A RAG system that retrieves information is useful. [pause] One that
> knows when its own knowledge has expired — and fixes itself before it
> answers — is something I'd actually trust inside a company. [pause] That
> trust part isn't built yet. This is the prototype that proves the
> mechanism works.

**חשוב: הטקסטים האלה נכתבו מחדש בסשן הזה** (לא בהכרח זהים מילה-במילה
לגרסה שהוצגה למשתמש בסשן הקודם, לפני compaction) — אבל **מדויקים ועקביים
עם מה שבפועל מוצג ב-`video/beats.html` עכשיו**, ומתוזמנים לפי ה-provisional
windows. לפני שמייצרים בפועל: לוודא עם המשתמש שהטקסט מקובל (אין המצאת
מספרים, שום claim עסקי לא מגובה).

### אחרי הייצור
- כל קובץ mp3 חייב להישמר, המשכים האמיתיים שלהם נמדדים, ואז ה-`beats`
  array ב-`video/beats.html` (שורות ~260-270) מתעדכן למשכים האמיתיים
  (לא provisional) לפני ההקלטה מחדש.
- הקלטה מחדש: Playwright, אותו pipeline כמו V2 (`record_video_dir`,
  1280×720), דחיסה עם אותו ffmpeg command.
- ה-audio layer מתווסף כמו ב-V2: `<audio>` elements נפרדים על
  `video/demo_page.html`, מסונכרנים ב-JS מול `timeupdate`/`play`/`pause`/
  `seeking` של ה-`<video>`, **לא** מעורבב לתוך קובץ הוידאו (ffmpeg כאן חסר
  audio encoder).

## דרישות QA לפני פרסום V3 (לא לפרסם בלי זה)

1. Playwright: לוודא סנכרון נכון מ-cold start ולאחר seek אמצע-וידאו (הקליפ
   הנכון מתחיל ב-offset הפנימי הנכון, או לא מנגן כלום אם ה-seek אחרי
   שה-narration של אותו beat כבר היה נגמר).
2. Pause/resume עוצר narration בצורה נקייה (בלי חפיפה/שאריות).
3. Captions — לחזור על ה-WebVTT toggleable pattern מ-V2 (`<track
   kind="subtitles">`, cues קצרים לפי clause, לא פסקה שלמה אחת ל-beat),
   לאמת `textTrack.mode` showing/hidden.
4. שום קונסול/page error ב-Playwright.
5. גודל עמוד סופי מתחת ל-16MB (Artifact cap).
6. Secret scan (`scripts/package_submission.sh`) ירוק — לב שים: יש false-positive
   filter קיים על base64 padding, לא לשבור אותו.
7. לוודא README.md/VIDEO_SCRIPT.md מתעדכנים לתאר את המבנה/משך V3 **האמיתי**
   בפועל (לא V2's 6-beat/300s language) רק **אחרי** שV3 מפורסם בהצלחה.
8. **לא לגעת ב-`video/demo_page.html` (V2 החי) עד ש-V3 עובר את כל זה.**

## ממצאי ביקורת כנה — נשמרו, לא לפעול עליהם עכשיו

יש קובץ נפרד: **`REVIEW_FINDINGS.md`** (נוצר בסשן הזה) — ביקורת "good/bad/
ugly" כנה על הפרויקט (n=3 על memory_correction, entity resolution
שנראה pre-solved, ניסוח README section 3 שנשמע כמו staleness detection,
3/4 קומפוננטות עם 0 ablation impact, הפער בין agentic *process* ל-shipped
*runtime*). **מפורש מהמשתמש: לא לפעול על זה עכשיו** — לטפל בנפרד אחרי
שV3 נסגר. הקובץ לא מקושר מ-README/SUBMISSION בכוונה.

## מה כבר גמור (פאזות 0–7, קוד+מספרים אמיתיים, לא placeholder)

- קורפוס דטרמיניסטי: 81 chunks, 40 probes, split 24 dev / 16 test **נעול
  ב-SHA-256** (`data/probes/test_split.locked.json`, `data/fact_registry.json`).
- 5 arms מלאים + הרצה + trajectories אמיתיים לכל case: `baseline/run_{A0,A,A2,B}*.py`,
  `advanced/{retriever,generator,verifier,memory_writer,tuner,run_case}.py`.
- `eval/score.py`, `eval/grade_test.py`, `eval/audit_no_peek.py` (בדיקת
  oracle-isolation), `eval/sandbox_guard.py` (אכיפת sandbox ל-Arm B) — כולם עם
  unit tests ירוקים.
- `results/*.json/csv` + `results/test_run_log.md` (קבלות: timestamp, git SHA,
  hash) + `results/ablations_summary.json` + `results/results_table.json`.
- `README.md` מלא (7 סעיפים, כולל "מי המשתמש/מה ה-bottleneck" בפתיחה — 15%
  מהציון), `CHANGELOG.md` מלא (טבלת שלבים + hot take + main failure mode — 5%),
  `PROCESS.md` (יומן append-only של כל באג/החלטה עם תאריך).
- `archive/ledgerguard-pretest/` — הקונספט הראשון שנבחר ונהרג ע"י ה-baseline
  ההוגן שלו עצמו, שמור עם README כן על הכישלון.

### תוצאות רשמיות (16 מקרי בדיקה קפואים, entity-disjoint מ-dev)

| Arm | Overall | memory_correction |
|---|---|---|
| A0 — כל הקורפוס בקריאה אחת | 13/16 | **0/3** |
| A — RAG סטטי (BM25 k=3) | 8/16 | **0/3** |
| A2 — A + שאילתה מתקנת אחת | 10/16 | **0/3** |
| B — agent גנרי חופשי (ה-baseline ההוגן של ה-PDF עצמו) | 12/16 | **0/3** |
| **C — SelfHeal RAG** | 11/16 | **3/3** |

באגרגט הגולמי SelfHeal **לא** מנצח את כולם (מדווח ביושר, לא מוסתר) — אבל על
הקטגוריה שקיימת בדיוק בשביל זה, זה 0/3 מוחלט מול 3/3 מוחלט, מאושש באבלציה
ישירה (memory ON/OFF, שאר הקונפיג זהה).

## שני items ישנים ל"בדיקה סופית" — עדיין לא נבדקו, אולי moot אם V3 מחליף V2

1. לוודא שאין 4 שניות dead time/desync בסוף וידאו V2 (304s קובץ מול 300s
   timeline).
2. לוודא ש-secret-scan hardening (ב-`scripts/package_submission.sh`) מסנן
   רק false positives אמיתיים ולא מחליש זיהוי מפתחות אמיתיים.

אלה עשויים להיות לא רלוונטיים אם V3 מחליף את V2 לגמרי — אבל אם V2 נשאר
fallback לתקופה כלשהי, לא לשכוח.

## הוראות סטנדינג מהמשתמש (בתוקף, לא לשכוח)

- **מטרה: מקום ראשון**, לא רק "לעבור".
- **`/goal`**: לבצע את התכנית בשלמותה, תוך בדיקה ביקורתית ושיפורים בלייב —
  לצוד ולתקן באגים אמיתיים, לא רק לבצע מכנית.
- **קריטריון LinkedIn/novelty/judge-affinity**: אסור לתת בונוס implicit. רק
  כשוקטור-ביצועים לפי הרוביקה קרוב מדי להבחנה — אז ורק אז, זה טיברייקר.
- **מודל**: Sonnet 5 (`claude-sonnet-5`) לכל שלבי הביצוע, מאושר מפורשות.
- **אחרי כל סיום פאזה/session — סיום מסודר**: קומיט, push, עדכון הקובץ הזה
  עם מצב מלא ומדויק, ואז המשך בשיחה חדשה. הסיבה: המשתמש לא אוהב compacting
  (איבוד קונטקסט/פירוט באמצע). קובץ זה הוא בדיוק המנגנון למניעת אובדן מידע
  בין סשנים. **חוזר על עצמו כרגע**: הסשן הזה מסתיים כאן לפי בקשה מפורשת.

## תזכורות קריטיות (לא השתנו)

- רוביקה (100 נק'): Problem&value 15%, **Agent solution&engineering 30%**,
  E2E quality 20%, Measured improvement 15%, Reproducibility 15%, Hot take 5%.
  Tie-break: Agent Solution&Eng → Reproducibility → Measured Improvement → E2E.
- Gate יחיד שדורש אישור: >2 ניסיונות תיקון כושלים לאותה שגיאה → עצור, הצג לוג
  מלא, התייעץ. הכל אחר רץ בלי לעצור.
- כל טענת שיפור צריכה מספר מ-`eval/score.py` — לא רק "יותר טוב".
- אל תערוך ידנית `trajectories/raw/*.jsonl`.
- deploy/publish/release דורש אישור (PreToolUse hook ב-`.claude/settings.json`).

## קבצים/paths רלוונטיים לסבב הבא

- `video/beats.html` — מקור ההקלטה, V3 מוכן ויזואלית (9 beats), commit-ed.
- `video/demo_page.html` — העמוד המתפרסם, **עדיין V2** (לא לגעת עד ש-V3
  מוכן עם narration אמיתי + עובר QA).
- `VIDEO_SCRIPT.md` — יתעדכן אחרי V3 (עדיין מתאר V2 בפועל).
- `README.md` — סעיף Video יתעדכן אחרי V3.
- `REVIEW_FINDINGS.md` — ביקורת כנה שמורה, לא לפעול.
- `PROCESS.md` — יומן append-only, לעדכן עם entry על V3 + הבאג של ה-stepper.
- `scripts/package_submission.sh` — secret scan עם false-positive filter,
  לבדוק שוב לפני package סופי.
- `PRODUCTION_ROADMAP.md` — ה-vision שה-closing beat (b8) מפנה אליו.

---

*(סוף הפרומפט. אם משהו כאן לא תואם את מצב הריפו בפועל — קרא את `PROCESS.md`
ו-`git log` קודם, אל תניח שהקובץ הזה מדויק ב-100% אם עבר זמן מאז שנכתב.)*
