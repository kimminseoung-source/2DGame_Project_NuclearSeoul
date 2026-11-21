"""Run every check in tools/checks with the game window hidden and write a table (2026-11-21).

    .venv\\Scripts\\python.exe tools/checks/run_all.py [name ...]      (from the project root)

- Each check runs through run_hidden.py (no window in front). A check that wants arguments
  (sys.argv[1]) is run again with "src docs/planning", as they were written.
- PASS: ran to the end without a traceback; FAIL: a traceback; TIMEOUT: over 240 s.
  A check prints numbers to read - PASS only means it ran; read its last line in the table.
- Checks save pictures into docs/planning. Pictures that were unchanged before the run are put
  back afterwards (git checkout), so a run never leaves committed pictures changed.
- The table goes to tools/checks/LAST_RUN.md.
"""

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PY = str(ROOT / ".venv/Scripts/python.exe")
NEEDS_ARGS = ("IndexError: list index out of range", "sys.argv[1]")


def changed_pictures():
    out = subprocess.run(["git", "diff", "--name-only", "--", "docs/planning"], cwd=ROOT,
                         capture_output=True, text=True, encoding="utf-8").stdout
    return {line for line in out.splitlines() if line.endswith((".png", ".gif"))}


def run(script, args=()):
    try:
        r = subprocess.run([PY, "-X", "utf8", str(HERE / "run_hidden.py"), str(script), *args], cwd=ROOT,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return None, ""


def last_line(log):
    lines = [l.strip() for l in log.splitlines()
             if l.strip() and "UserWarning" not in l and "Pico2d" not in l and not l.startswith("warnings.warn")]
    return lines[-1][:150].replace("|", "/") if lines else ""


def main():
    names = sys.argv[1:]
    scripts = sorted(HERE.glob("check_*.py"))
    if names:
        scripts = [s for s in scripts if any(n in s.stem for n in names)]
    before = changed_pictures()
    rows, start = [], time.time()
    for s in scripts:
        code, log = run(s)
        if code not in (0, None) and any(k in log for k in NEEDS_ARGS):
            code, log = run(s, ("src", "docs/planning"))
        state = "TIMEOUT" if code is None else ("FAIL" if "Traceback" in log or code else "PASS")
        error = next((l.strip() for l in reversed(log.splitlines()) if "Error" in l or "Exception" in l), "")
        rows.append((s.stem, state, last_line(log), error[:120].replace("|", "/")))
        print(f"{state:7} {s.stem}  {rows[-1][2][:90]}", flush=True)
    restored = sorted(changed_pictures() - before)
    if restored:
        subprocess.run(["git", "checkout", "--", *restored], cwd=ROOT)
    passed = sum(r[1] == "PASS" for r in rows)
    lines = [f"# 점검 결과 ({time.strftime('%Y-%m-%d %H:%M')}, {len(rows)}개 중 {passed}개 통과, "
             f"{time.time() - start:.0f}초)", "",
             "`tools/checks/run_all.py`가 씀. PASS는 끝까지 돌았다는 뜻 — 숫자는 마지막 줄을 읽을 것.", "",
             "| 점검 | 결과 | 마지막 줄 | 오류 |", "|---|---|---|---|"]
    lines += [f"| {n} | {st} | {ln} | {er} |" for n, st, ln, er in rows]
    if restored:
        lines += ["", f"되돌린 그림 {len(restored)}개(점검이 바꾼 docs/planning 그림): " + ", ".join(restored)]
    if names:                                  # a partial run does not replace the full table
        print(f"{passed}/{len(rows)} PASS, restored {len(restored)} pictures (partial run: LAST_RUN.md kept)")
        return
    (HERE / "LAST_RUN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{passed}/{len(rows)} PASS, restored {len(restored)} pictures -> tools/checks/LAST_RUN.md")


if __name__ == "__main__":
    main()
