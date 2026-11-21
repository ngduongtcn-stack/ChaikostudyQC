# Brief: prepare one 2級 chapter for the public study website

You prepare lesson content for the QC検定2級 section of a free public study website for Vietnamese workers in Japan (Japanese pages with an optional Vietnamese explanation, plus a separate pure-Vietnamese version). The source is a private daily study plan written for one learner; it must become clean public content.

Input: a JSON bundle {chapter, sections:[{key, code, heading_ja, body_ja, body_vi}], quiz:[{id, code, q_ja, q_vi, options, answer (0-based), exp_ja, exp_vi}], terms:[...]}. body_* are Markdown (#### headings, **bold**, "- " lists, "> " formula lines).

## What to do
1. **Remove personal / course references** from ALL Japanese and Vietnamese text: day numbers ("Day 45", "明日", "今日"), schedules, time allocations, references to the learner's books or pages ("本で解く", "p.26", "教科書", "正誤表"), "this lesson/note/tab", and anything about one specific learner. Rewrite the sentence so it still reads naturally (e.g. "サンプリングの種類はDay 45で学ぶ" → "サンプリングの種類は別の項目で扱う" or just drop the clause). Keep all technical content.
2. **Vietnamese must be purely Vietnamese**: no kanji, kana or Japanese punctuation (「」（）・、。～：！？＝ full-width characters). Replace Japanese terms with standard Vietnamese QC terms (かたより → độ chệch, ばらつき → độ phân tán, 平方和 → tổng bình phương độ lệch, 不偏分散 → phương sai không chệch, 正規分布 → phân phối chuẩn, 管理図 → biểu đồ kiểm soát, 特性要因図 → biểu đồ nhân quả, 層別 → phân tầng…). Latin symbols/abbreviations and math (x̄, σ, S, V, n, Σ, √, ≒, ≤, χ², QC, JIS…) are fine; use ASCII = + − × ÷ ( ) instead of full-width ones.
3. **body_vi** must be a full, faithful Vietnamese version of body_ja (same structure: same #### headings, lists, formula lines, worked examples with the same numbers). If the current body_vi is only a summary, rewrite it fully. Also write **heading_vi** (Vietnamese translation of heading_ja).
4. **Quiz**: write **q_vi** (Vietnamese translation of the question, pure Vietnamese) and **exp_vi** (pure Vietnamese explanation that agrees with options[answer] and exp_ja). Answer choices are displayed IN THEIR ORIGINAL ORDER with labels ア, イ, ウ, エ, オ — exp_ja may keep referring to ア/イ…; in exp_vi refer to them as "phương án 1, 2, 3, 4, 5" (same order). Clean exp_ja of personal references only (rule 1).
5. **Check correctness** as you go (re-compute any number with Python). If a quiz question is wrong, ambiguous, depends on context not in the question (e.g. "上の表", "本レッスンの例"), or is about the learner's own schedule/book, put its id in "drop" instead of fixing it heavily. Fix small errors in the lesson text if you find them.

## Output
Write with Python (json.dump, ensure_ascii=False, indent=1) to the output file:
{"sections":[{"key","heading_ja","heading_vi","body_ja","body_vi"} — every input section],
 "quiz":[{"id","q_ja","q_vi","exp_ja","exp_vi"} — every input quiz item not dropped],
 "drop":["B1-007", ...]}
Then run: python3 <repo>/tools/k2/check_out.py <input> <output>  and fix until it reports 0 lỗi. Do not modify any other files.
Final reply: the check line, ids dropped with a one-line reason each, and any content errors you corrected.
