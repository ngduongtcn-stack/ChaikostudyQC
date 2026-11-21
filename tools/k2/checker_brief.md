# Brief: independent blind check of QC検定 practice questions

You are an independent checker. You get questions WITHOUT answers. Solve each one yourself as an expert in 品質管理 / QC検定 (2級, current JIS terminology, JIS Z 9020-2 control-chart rules).
- Solve every calculation question with Python (run it), do not do arithmetic in your head.
- Use only your input file: do not open the chapter bundle, the cleaned files or the repo question data. 

For each question output {"id": ..., "answer": <0-based index of the choice you think is correct>, "confident": true/false, "note": "..."}.
Set confident=false (with a reason in note) if: more than one choice is defensible, none is correct, the Japanese is unclear/unnatural, the content is factually wrong or outdated, or the numbers don't work out cleanly. Be strict — a doubtful question is better dropped.

Write the JSON list with Python (json.dump, ensure_ascii=False) to your output file. Final reply: number checked, number not confident, one line per not-confident item.

These are normal QC検定2級 exam-level questions (some have 5 choices). Mark not confident if the answer is not uniquely defensible or the question needs context that is not in it.
