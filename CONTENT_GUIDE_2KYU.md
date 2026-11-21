# 2級 section — weekly chapter conversion

The 2級 pages are converted from the owner's private daily 2級 study lessons (artifact
https://claude.ai/artifact/1RZudoJVZgFSE7iVFDNrZn, collection `lessons`, plus `plan/main`).
**One chapter per run, as cheaply as possible** (the owner wants low weekly usage):
1 cleaning subagent + 1 blind-check subagent per chapter, no other subagents.

Chapter order: B4, B5, B6, B7, B8, B3, B9, B10, B11, B12, B13, A1, A2, A3, A4, A5
(the chapter id is the part before the dot in lesson codes such as "B4.2").
A chapter is **ready** when every day in `plan/main.days` whose `c` list contains a code of
that chapter has a date `d` before today (Asia/Tokyo). Take the first chapter in the order
that is ready and not yet on the site (levels["2"].topics in src/data/questions.json, ids
are lower-case: "b4"). If none is ready, change nothing and report that.

## Steps (S = a scratch folder outside the repo)
1. Download lessons: ArtifactData `list` on collection `lessons` with `out_dir` = S/lessons
   (page with `query.cursor` until no `next_cursor`), and `get` plan/main if needed.
2. `python3 tools/k2/extract.py S/lessons S/in <CH>` → S/in/<CH>.json (sections, deduplicated quiz, terms).
3. Blind file: from S/in/<CH>.json write S/blind.json = [{id, level: 2, topic, question: q_ja, choices: options}].
4. Launch, in parallel, two general-purpose subagents:
   - cleaner: follow tools/k2/clean_brief.md for BOTH sections and quiz; input S/in/<CH>.json,
     output S/out.json; validate with `python3 tools/k2/check_out.py S/in/<CH>.json S/out.json`.
   - checker: follow tools/k2/checker_brief.md; input S/blind.json; output S/chk.json.
5. `python3 tools/import_2kyu.py --chapter <CH> --bundle S/in/<CH>.json --sec S/out.json --quiz S/out.json --check S/chk.json`
   (keeps only questions the checker answered the same way with confidence and the cleaner did not drop).
6. `python3 build.py`, commit ("2級: add chapter <CH> …"), push to main, wait for the
   "Build and deploy site" GitHub Actions run to succeed.

Never publish personal content from the lessons: progress, results, schedules, day numbers,
book names/pages, the learner's workplace. Vietnamese text must contain no Japanese characters.
