# Incident Response Report Prompt

**System:** "Incident Report Writer".

**User template:**
```
Draft the following sections of an incident report. Use ONLY the provided evidence.
Do not overstate impact beyond what the evidence supports.

Sections:
1. EXECUTIVE SUMMARY (3-4 sentences, non-technical)
2. TIMELINE (bulleted, UTC, from the evidence)
3. TECHNICAL DETAILS (what the attacker did, with the supporting log/alert references)
4. IMPACT (what was/was not affected, stated conservatively)
5. RECOMMENDATIONS (prioritized, actionable)

EVIDENCE:
{{EVIDENCE_BLOCK}}
```
