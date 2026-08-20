# Sigma Rule Generation Prompt

**System:** "Detection Engineer".

**User template:**
```
Write a valid Sigma rule that detects the behavior described below.
Requirements:
- Output ONLY valid YAML (a single Sigma rule), no prose.
- Include: title, id (leave as a placeholder GUID), status: experimental, description,
  author, date, logsource, detection (with a selection + condition), falsepositives,
  level.
- Keep the logic tight to minimize false positives.
- Add a comment line explaining which log source/fields it assumes.

BEHAVIOR TO DETECT:
{{BEHAVIOR_DESCRIPTION}}
```

**Example behavior fill-in:**
```
More than 10 failed SSH logins (Linux auth log) from a single source IP within 60
seconds, followed by a successful login from that same IP.
```

> Teaching note: always validate AI-generated Sigma with `sigma check` / a linter and
> test against real data before deploying. The AI drafts; the engineer verifies.
