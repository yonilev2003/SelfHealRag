# Handoff prompt — paste this at the start of a new session

This file exists so continuity across sessions is itself disclosed, not just
convenient. The text below is meant to be pasted verbatim as the first message
in a fresh Claude Code session opened in this repo.

---

אני ממשיך עבודה על ריפו ה-Hackathon למיקרו1 Frontier Engineering Challenge
(28–31 באוגוסט 2026). זה סשן חדש לגמרי, בלי זיכרון מהסשן הקודם. לפני שאתה עושה
משהו, תקרא בסדר הזה:

1. `CLAUDE.md` — מוסכמות עבודה, ה-gate היחיד (deploy-confirmation hook), מה
   בפועל נשפט.
2. `TOOLKIT.md` — עץ כלים: איזה כלי/skill/workflow מתאים לכל שלב בספרינט.
3. `README.md` — מבנה הריפו, מה כבר קיים, פקודות reproduce.
4. `.claude/workflows/README.md` — איך מריצים `hackathon-sprint` /
   `hackathon-fix`, כולל checkpoints (`stopAfter`).
5. `PROBLEM.md` — אם כבר הדבקתי שם את תוכן הבעיה המלא, תתחיל משם. **אם זה עדיין
   placeholder — עצור ותבקש ממני את ה-PDF/טקסט המלא של הבעיה לפני שתמשיך** (אם
   זה קובץ PDF, השתמש בסקיל `pdf` לחילוץ טקסט/טבלאות מלא, לא רק תקציר).

## מצב נוכחי (סוף היום שלפני הקיקאוף)

- ברנץ' עבודה: `claude/hackathon-repo-setup-k0cj07`, מסונכרן עם origin.
- קומיט ה-scaffold המקורי מתויג מקומית `pre-kickoff` (על commit `5aa5839`) —
  **לא נדחף** ל-GitHub עקב הרשאות הסשן ההוא; אם צריך שהתג יופיע ב-remote, תריץ
  `git push origin pre-kickoff` בעצמך.
- כל תשתית ה-pre-kickoff קיימת ועברה בדיקה בפועל:
  - `Makefile` + `scripts/*.sh` + `eval/score.py` — עובדים end-to-end (עדיין
    placeholders/no-op עד שהבעיה תהיה ידועה; `CRITERIA` ב-`eval/score.py` ריק).
  - `.github/workflows/ci.yml` — ירוק, כולל `timeout-minutes`, shellcheck,
    ו-py_compile.
  - `.claude/hooks/guard_deploy.py` — עבר סבב hardening (token-aware matching
    עם `shlex`, לא substring על המחרוזת הגולמית) אחרי שסבב ביקורת אדברסרי מצא
    false positives/negatives אמיתיים.
  - `.claude/workflows/hackathon-sprint.js` + `hackathon-fix.js` — עברו סבב
    ביקורת אדברסרי מלא (5 מימדים, verify על כל ממצא) ותוקנו: race condition
    בין lens-ים מקבילים שערכו את אותה תיקייה בו-זמנית, label collision בין
    votes מקבילים, unbounded loop, חוסר guard על all-judges-fail. `hackathon-
    sprint` תומך עכשיו ב-`args.stopAfter: "plan"|"baseline"` לעצירה ידנית
    לפני שממשיכים.
  - `trajectories/raw/` כבר מכיל לוג אמיתי (מסשן ההקמה) — הוכחה שהמנגנון עובד.
  - `.env.example` + הערה ב-`scripts/setup.sh` + סעיף ב-`README.md` — תשתית
    ל-API keys/secrets (מקומי דרך `.env`, ב-CI דרך GitHub repo secrets).
  - `VIDEO_SCRIPT.md` — שלד לסרטון ההגשה (≤5 דקות), עדיין ריק מתוכן אמיתי.

## מה לעשות ברגע שיש לך את תוכן הבעיה המלא

1. הדבק/כתוב את תוכן הבעיה (דרישות, אילוצים, פורמט בדיקות, כל חומר עזר) לתוך
   `PROBLEM.md` במקום ה-placeholder.
2. `Workflow({ name: "hackathon-sprint", args: { problemPath: "PROBLEM.md",
   stopAfter: "plan" } })` — נקודת עצירה ראשונה: תבדוק איתי שהגישה שנבחרה
   הגיונית לפני שממשיכים למימוש בפועל.
3. אחרי אישור — `Workflow({ scriptPath, resumeFromRunId })` בלי `stopAfter` (או
   עם `stopAfter: "baseline"` לעוד נקודת עצירה) כדי להמשיך. שלבים שכבר רצו
   חוזרים מה-cache, לא רצים מחדש.
4. תעקוב אחרי `TOOLKIT.md` לגבי איזה כלי מתאים לכל מצב באמצע הספרינט
   (`hackathon-fix` לבאגים ממוקדים, `code-review`/`simplify` לניקיון קוד,
   `security-review` אם רלוונטי לנתונים/הרשאות).
5. עדכן את `CHANGELOG.md` תוך כדי העבודה — לא בסוף מהזיכרון.
6. הרץ `make trajectories` מדי פעם, לא רק בסוף, כדי לא לאבד לוגים.
7. לקראת הסוף: מלא את `eval/score.py`'s `CRITERIA` לפי קריטריוני ההערכה
   בפועל, ודא ש-`make eval` נותן דלתא אמיתית (לא 0), מלא Runtime/Cost
   ב-`README.md`, מלא את `VIDEO_SCRIPT.md` ותצלם, ותוודא reproducibility
   מסביבה נקייה לגמרי (לא רק "רץ פעם אחת בקונטיינר הזה").

## תזכורות קריטיות

- סדר שיפוט/tie-break: **Agent Solution & Engineering → Reproducibility →
  Measured Improvement → End-to-End Quality**. אל תזניח תיעוד/שקיפות תהליך
  לטובת קוד "יפה" בלבד — זה קריטריון ה-tie-break הראשון.
- ה-gate היחיד שדורש אישור אנושי: פקודות שנראות כמו deploy/publish/release
  (`guard_deploy.py`). כל השאר אמור לרוץ בלי לעצור.
- אל תערוך ידנית `trajectories/raw/*.jsonl`.
- כל טענת שיפור צריכה מספר מ-`eval/score.py` — "יותר טוב" זה לא טענה, דלתא
  היא טענה.
- הדדליין: 31/8, 02:59 שעון ישראל. תכנן קצב בהתאם.

---

*(סוף הפרומפט להעתקה. אם משהו כאן לא מסתדר עם המצב בפועל של הריפו — קרא קודם,
אל תניח.)*
