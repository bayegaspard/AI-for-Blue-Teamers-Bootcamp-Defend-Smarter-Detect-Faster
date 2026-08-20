# Wazuh Alert Summary Prompt

**System:** "SOC Analyst Assistant".

**User template:**
```
Summarize this Wazuh alert for an incident ticket. Use ONLY the alert JSON.

Output exactly these fields:
- TITLE: short, ticket-ready (max 12 words)
- WHAT_HAPPENED: 1-2 sentences in plain language
- SEVERITY: map from rule.level  (0-3 low, 4-7 medium, 8-11 high, 12-15 critical)
- AFFECTED_ASSET: agent.name / agent.ip
- MITRE: list any rule.mitre.id present, else "none listed"
- NEXT_STEP: one action

ALERT JSON:
{{ALERT_JSON}}
```
