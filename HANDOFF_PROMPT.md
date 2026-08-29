# Handoff prompt — paste this at the start of a new session

This file exists so continuity across sessions is itself disclosed, not just
convenient. It is rewritten at the end of every phase (per standing
instruction) so a brand-new session — or a context-compacted one — can pick
up cold with zero information loss. Paste the text below as the first
message in a fresh session, or just point Claude at this file.

---

## מצב עדכני — סוף פאזה 6, פאזה 7 (וידאו + אריזה) באמצע

זה ריפו של הגשה יחידה ל-**micro1 Agentic Workflows Hackathon** (28–31/8/2026,
דדליין **30/8 23:59 UTC = 31/8 02:59 שעון ישראל**, אין הארכות).

**הקונספט הנבחר: SelfHeal RAG.** מערכת RAG על מסמכי מדיניות חברה (handbook)
שמזהה תשובות שהתיישנו — עובדה השתנתה (טיקט/ביקורת), אבל התיעוד לא עודכן —
ומתקנת את עצמה בזמן אמת דרך ערוץ "אותות תיקון" שאף baseline לא מקבל. הטענה
המרכזית היא **קטגורית, לא אמפירית**: התשובה הנכונה פשוט לא קיימת בקורפוס, אז
"לקרוא יותר" (A0, כל הקורפוס בקריאה אחת) ו"לחשוב יותר זמן" (B, agent חופשי עם
כלים) שניהם נכשלים באותה מידה — רק ערוץ memory נפרד סוגר את הפער.

### התוצאה הרשמית (16 מקרי בדיקה קפואים, entity-disjoint מ-dev)

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

### באגים אמיתיים שנמצאו ותוקנו בלייב (הרשימה המלאה ב-`PROCESS.md`/`CHANGELOG.md`)

החשוב מכולם: **הריצה הרשמית הראשונה על ה-test הקפוא הראתה C=A (8/16, 0/3 על
memory_correction)** — כי לולאת ה-self-improvement של Phase 4 למדה תיקונים רק
לישויות שהיו ב-dev, וה-test מכוון בכוונה entity-disjoint. תוקן ע"י הפיכת
`advanced/memory_writer.py`'s `heal_entities()` למנגנון שרץ **בלייב** בתוך
`generator.py` על כל ישות שנשלפת, לא רק בזמן ה-tuning הלא-מקוון. זה גם ה-**Hot
Take** של ההגשה: split קפוא לא רק מודד generalization — הוא תופס אותך "נועל"
יכולת ל-scope הלא נכון, בשקט, כמספר מאכזב במקום שגיאה.

באגים נוספים (רשימה מלאה + evidence ב-PROCESS.md): `allowed_tools` לא חוסם
Bash (רק `disallowed_tools` כן) | פיצול chunk context/value שבר retrieval+ ציון
| citation לא מסומן `"MEMORY"` | verifier השווה chunk_id במקום effective_date |
`next_k()` לא התקדם בלולאה | `run_ablations.py` היה דורס את הריצה הרשמית.

## מה כבר גמור (פאזות 0–6, קוד+מספרים אמיתיים, לא placeholder)

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

## מה עדיין באמצע — פאזה 7 (וידאו + אריזה)

1. **`video/beats.html`** — עמוד הקלטה: 6 beats לפי `VIDEO_SCRIPT.md` (0:00–5:00),
   עם כל בלוקי הטרמינל ממולאים מפלט אמיתי שנתפס בלייב (לא מבוים). כולל
   `window.__seek(seconds)` דיבאג-הוק לתצוגה מקדימה מהירה.
2. **הקלטה בפועל**: Playwright + Chromium שהותקנו מראש (`/opt/pw-browsers/`),
   `record_video_dir` על `beats.html`, המתנה ל-304 שניות מלאות. **שים לב**: אם
   מריצים דרך `Bash(run_in_background:true)` — **אל תוסיפו `&` בתוך הפקודה
   עצמה** — זה יוצר double-backgrounding: ה-shell מדווח "exited 0" כמעט מיד
   (כי רק ה-`&`-launch עצמו הסתיים), בעוד התהליך האמיתי ממשיך לרוץ "יתום"
   ברקע בלי שהכלי עוקב אחריו. זה קרה בפועל הפעם — תוקן ע"י המתנה נכונה
   (`while kill -0 <pid>; do sleep 5; done`) על ה-PID האמיתי.
3. **ffmpeg המותקן מראש** (`/opt/pw-browsers/ffmpeg-1011/ffmpeg-linux`) הוא
   build מוגבל של Playwright — **תומך רק ב-encoder=libvpx (webm), אין מוקסר
   mp4, אין `-f null`**. אי אפשר להמיר ל-mp4 בסביבה הזו. הפלט נשאר `.webm`
   (נתמך native בדפדפנים דרך `<video>`).
4. **דחיסה נדרשת לפני אירוח**: ההקלטה הגולמית יוצאת ב-~400-500kbps, מה שיוצא
   ל-~15-18MB ל-300 שניות — **קרוב מדי או מעל מגבלת ה-16MB** של Artifact
   data-URI (ובנוסף base64 מנפח ~33%!). יש להריץ מחדש דרך ffmpeg עם `-b:v
   ~250-260k -r 12 -crf 30 -an` כדי לרדת ל-~9-10MB גולמי (~12-13MB אחרי
   base64, כולל מרווח ל-wrapper HTML). סקריפט מוכן: `/tmp/compress_video.sh`.
5. **חשוב — `assets` capability לא זמינה לחשבון הזה** (נבדק דרך skill
   `artifact-capabilities`: הרשימה הזמינה היא רק `artifact, downloads, mcp,
   self` — אין `assets`). **אי אפשר להעלות את קובץ הוידאו כ-asset נפרד ל-Artifact.**
   הדרך היחידה לאירוח: להטמיע את הוידאו כ-`data:` URI בתוך עמוד HTML יחיד
   ולפרסם עם `Artifact` הרגיל (בלי `capabilities`), תחת מגבלת 16MB הכוללת.
6. אחרי שהוידאו מתארח: לעדכן `README.md` (יש placeholder `[link once
   recorded]`) ו-`VIDEO_SCRIPT.md` עם ה-URL, למלא את `SUBMISSION.md`'s "Video
   URL" section (כבר כתוב Title+Description מלא שם).
7. להריץ `scripts/package_submission.sh` (כבר נבדק, מייצר zip תקין מתחת
   ל-50MB — היה 2MB בבדיקה עם תוכן חלקי; לוודא שוב עם התוכן הסופי).
8. קומיט + push סופיים.

## הוראות סטנדינג מהמשתמש (בתוקף, לא לשכוח)

- **מטרה: מקום ראשון**, לא רק "לעבור". פועלים במצב `/loop` דינמי
  (self-pacing עם `ScheduleWakeup`), ה-prompt המדויק שחייב לעבור verbatim בכל
  קריאת `ScheduleWakeup` הוא: `"/loop התאמה לענייני התכנית, לחוקים ושאיפה
  לניצחון בהאקתון תוך בניית פרויקט משמעותי שאפשר להציג בלינקדאין ושhead of ai
  בארגון היה עושה בעצמו"`.
- **`/goal`**: לבצע את התכנית בשלמותה, תוך בדיקה ביקורתית ושיפורים בלייב — כלומר
  לצוד ולתקן באגים אמיתיים, לא רק לבצע מכנית.
- **קריטריון LinkedIn/novelty/judge-affinity**: אסור לתת בונוס implicit. רק
  כשוקטור-ביצועים לפי הרוביקה קרוב מדי להבחנה — אז ורק אז, זה טיברייקר.
- **מודל**: Sonnet 5 (`claude-sonnet-5`) לכל שלבי הביצוע, מאושר מפורשות.
- **חדש מעכשיו**: **אחרי כל סיום פאזה — סיום סשן מסודר** (קומיט, push, עדכון
  הקובץ הזה עם מצב מלא ומדויק) **ואז המשך בשיחה חדשה**, לא להמשיך ולצבור
  context בסשן אחד. הסיבה: המשתמש לא אוהב compacting (איבוד קונטקסט/פירוט
  באמצע). קובץ זה הוא בדיוק המנגנון למניעת אובדן מידע בין סשנים.

## תזכורות קריטיות (לא השתנו)

- רוביקה (100 נק'): Problem&value 15%, **Agent solution&engineering 30%**,
  E2E quality 20%, Measured improvement 15%, Reproducibility 15%, Hot take 5%.
  Tie-break: Agent Solution&Eng → Reproducibility → Measured Improvement → E2E.
- Gate יחיד שדורש אישור: >2 ניסיונות תיקון כושלים לאותה שגיאה → עצור, הצג לוג
  מלא, התייעץ. הכל אחר רץ בלי לעצור.
- כל טענת שיפור צריכה מספר מ-`eval/score.py` — לא רק "יותר טוב".
- אל תערוך ידנית `trajectories/raw/*.jsonl`.

---

*(סוף הפרומפט. אם משהו כאן לא תואם את מצב הריפו בפועל — קרא את `PROCESS.md`
ו-`git log` קודם, אל תניח שהקובץ הזה מדויק ב-100% אם עבר זמן מאז שנכתב.)*
