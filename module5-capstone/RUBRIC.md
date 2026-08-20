# Module 5 Capstone — Grading Rubric (100 points)

Grade each student's `submissions/<name>_report.md` plus their work through the
[`STUDENT_WORKSHEET.md`](STUDENT_WORKSHEET.md). This human rubric is weighted the
same five ways as the automated [`labs/capstone_check.py`](labs/capstone_check.py),
so the two totals should land close together. Read the report end-to-end; don't grade
on keywords alone.

**Pass mark: 70 / 100.** The **Adversarial Catch** section is a gate: a report that
fails to identify the prompt-injection entry **cannot exceed 80 overall**, regardless
of other points (this mirrors the auto-grader's `ADVERSARIAL MISS` cap).

---

## 1. Detection — 20 pts

| Criteria | Pts |
|---|---:|
| Identifies the SSH brute-force source `10.10.10.5` (failed logins burst) | 6 |
| Identifies the web attacker `10.10.10.7` (SQLi + `sqlmap` + path traversal) | 6 |
| Notes the recon/scan and/or path-traversal `/../../etc/passwd` probe | 3 |
| Flags the "odd" `poisoned.log` entry as worth investigating (even before proving it's an attack) | 5 |

## 2. Analysis — 20 pts

| Criteria | Pts |
|---|---:|
| Uses AI triage to summarize each finding (shows the assistant/CLI was used) | 6 |
| **Verifies** each AI verdict against the exact raw log line (evidence cited) | 8 |
| Correct verdicts: brute force = malicious, SQLi = malicious, injection entry = malicious/attack (not benign) | 6 |

## 3. Response — 20 pts

| Criteria | Pts |
|---|---:|
| Correlates observed IPs with [`threat_intel.csv`](../datasets/threat_intel.csv) (`.5` & `.7` = high, `.11` = medium) | 6 |
| Prioritized, actionable containment (block IPs, disable/rotate `admin`, patch SQLi input handling, preserve logs) | 8 |
| Each recommendation is tied to a specific finding — no orphan actions | 6 |

## 4. Reporting — 20 pts

| Criteria | Pts |
|---|---:|
| All five required sections present and correctly named (Executive Summary, Timeline, Technical Details, Impact, Recommendations) | 6 |
| Timeline is accurate and in UTC, drawn from the evidence | 5 |
| **Impact is conservative and correct** — calls out the successful `admin` login from `10.10.10.5` (compromise), without overstating (no exfiltration claimed beyond evidence) | 6 |
| Clear, non-technical Executive Summary a manager could read | 3 |

## 5. Adversarial Catch — 20 pts  *(gate)*

| Criteria | Pts |
|---|---:|
| Explicitly names the entry as a **prompt-injection / poisoned** log line | 6 |
| Identifies its source IP(s) `10.10.10.9` and/or `10.10.10.11` and rule **100110** | 5 |
| Explains **how they avoided being misled**: verified AI vs. raw evidence, used **hardened mode** / data isolation, did not close on the AI's say-so | 6 |
| Demonstrates the vulnerable-vs-hardened difference (ran both, or explains it) | 3 |

---

## Score sheet

| Section | Max | Score |
|---|---:|---:|
| 1. Detection | 20 | |
| 2. Analysis | 20 | |
| 3. Response | 20 | |
| 4. Reporting | 20 | |
| 5. Adversarial Catch *(gate: fail → cap 80)* | 20 | |
| **Total** | **100** | |

**Grade bands:** 90–100 excellent · 80–89 strong · 70–79 pass · <70 revise & resubmit.

**Cross-check with the auto-grader:** run
`python3 labs/capstone_check.py submissions/<name>_report.md`. A large gap between the
automated total and your human total usually means the student pasted the right IPs
without real analysis (auto high / human low) or wrote strong prose but forgot a
required heading or IP string (human high / auto low). Investigate either way.
