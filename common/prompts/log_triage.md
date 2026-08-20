# Log Triage Prompt

**System:** use the "SOC Analyst Assistant" persona (`system_prompts.md`).

**User template:**
```
Analyze the following log block. Use ONLY the data provided.

Return your answer as:
1. SUMMARY: one sentence describing what happened.
2. VERDICT: benign | suspicious | malicious
3. CONFIDENCE: low | medium | high
4. INDICATORS: the exact IPs, users, ports, or strings that drove your verdict.
5. RECOMMENDED ACTION: one concrete next step for the analyst.

LOG BLOCK:
{{LOG_BLOCK}}
```

**Example fill-in:**
```
LOG BLOCK:
Aug 10 03:11:02 web01 sshd[2001]: Failed password for invalid user admin from 10.10.10.5 port 51122 ssh2
Aug 10 03:11:03 web01 sshd[2003]: Failed password for invalid user admin from 10.10.10.5 port 51124 ssh2
Aug 10 03:11:04 web01 sshd[2005]: Failed password for root from 10.10.10.5 port 51126 ssh2
... (x120 in 40 seconds)
```
