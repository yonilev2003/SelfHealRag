# Handoff prompt — paste this at the start of a new session

This file exists so continuity across sessions is itself disclosed, not just
convenient. It is rewritten at the end of every phase (per standing
instruction) so a brand-new session — or a context-compacted one — can pick
up cold with zero information loss. Paste the text below as the first
message in a fresh session, or just point Claude at this file.

---

## מצב עדכני — פאזה 7 (וידאו + אריזה) הושלמה, בעבודה על ליטוש להגשה

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

## פאזה 7 — גמורה. מצב עכשווי: ליטוש להגשה בפועל

וידאו 5:04 (`video/beats.html` הקליט, `video/demo_page.html` מארח) חי ב-Artifact:
https://claude.ai/code/artifact/42418c8e-e0fd-4ce8-90c9-fd7eca0ccaf0 — מקושר
מ-README/VIDEO_SCRIPT/SUBMISSION.md. `submission.zip` נבנה (5MB). **audit agent
מלא (39 tool calls) עבר על כל הריפו לפני הגשה — 8/8 PASS**: `eval/score.py`
נכון ומתאים לתוצאות המחייבות, אין oracle leakage (`make verify-no-leak`
ירוק), מספרי README תואמים ל-`results/*` בפועל, אין TODO/placeholder, כל
ה-unit tests עוברים, אין secrets בריפו.

**גילויים טכניים חשובים מפאזה 7 (לזכור להמשך):**
- ffmpeg המותקן מראש (`/opt/pw-browsers/ffmpeg-1011/ffmpeg-linux`) הוא build
  מוגבל של Playwright: **וידאו VP8/webm בלבד, אין שום audio encoder מקומפל**.
  אי אפשר לערבב אודיו לתוך קובץ וידאו בסביבה הזו כלל.
- `assets` capability של Artifact **לא זמינה לחשבון הזה** — אי אפשר להעלות
  קובץ וידאו כ-asset נפרד. הפתרון שנבחר: להטמיע כ-`data:` URI בתוך עמוד HTML
  יחיד (מגבלה כוללת 16MB).
- double-backgrounding bug אמיתי: `Bash(run_in_background:true)` + `&` בתוך
  הפקודה עצמה גורם ל-shell לדווח "exited 0" מיידית בעוד התהליך האמיתי ממשיך
  לרוץ יתום ברקע. תמיד להמתין על ה-PID האמיתי (`while kill -0 <pid>`).

**עבודה נוכחית (אחרי אישור המשתמש, לא פאזה חדשה אלא ליטוש להגשה):**
1. **וידאו עם הקראה אמיתית (ElevenLabs) + מוזיקת רקע** — הוחלט לבנות ולהחליף
   את הוידאו הקיים (לא לשמור שתי גרסאות — "הכי יעיל לשופטים"). פתרון טכני:
   בגלל ש-ffmpeg כאן לא תומך באודיו, לא מערבבים מחדש את קובץ ה-webm — מוסיפים
   שכבת `<audio>` מסונכרנת ב-JS על גבי `video/demo_page.html` (מוזיקת רקע
   loop + 6 קטעי narration שמופעלים בדיוק ב-beat boundaries הקיימים:
   0/30/75/165/225/270/300 שניות). מוזיקת רקע אמביינטית סונתזה מקומית
   (`/tmp/synth_ambient.py`, numpy+wave, ~1.1MB, 26s loop) — לא הורדה
   מהאינטרנט, בלי סיכון זכויות יוצרים. **חסום על מפתח ElevenLabs API** (לא
   קיים ב-env, המשתמש אמור לספק אותו).
2. **הגשה בפועל לטופס התחרות** — המשתמש ביקש לנסות מכאן דרך Playwright (לא
   דרך "Claude in Chrome" שלו — אין לי גישה לזה מהסביבה המרוחקת הזו). **חסום
   על ה-URL של טופס ההגשה** — עדיין לא סופק. תוכן הטופס (Title/Description/
   Video URL) כבר מוכן ב-`SUBMISSION.md`. **לפני לחיצה על Submit בפועל —
   לעצור ולבקש אישור סופי מהמשתמש**, זו פעולה בלתי הפיכה על תחרות אמיתית.
3. **שינוי שם ריפו ל-`selfheal-rag`** — **אין tool זמין** ב-MCP של GitHub
   לשינוי שם ריפו (נבדק). המשתמש צריך לעשות את זה ידנית (GitHub Settings →
   General → Repository name), ואז לעדכן את הקישורים הפנימיים (README,
   SUBMISSION.md, footer של demo_page.html) לשם החדש.
4. פוסט לינקדאין — ינוסח בנפרד, אין connector ללינקדאין זמין (נבדק), אז זו
   טיוטת טקסט בלבד שהמשתמש יפרסם בעצמו.

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
