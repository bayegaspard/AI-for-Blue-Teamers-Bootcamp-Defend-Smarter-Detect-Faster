# Threat Intel Correlation Prompt

**System:** "SOC Analyst Assistant".

**User template:**
```
You are given (A) observed indicators from our environment and (B) a threat-intel
list. Correlate them. Use ONLY the provided data.

Output:
- MATCHES: table of indicator | source (A/B) | intel note | severity
- UNMATCHED_BUT_SUSPICIOUS: observed indicators with no intel hit that still look risky, and why
- PRIORITY: which matched indicator to investigate first and the one-line reason

(A) OBSERVED INDICATORS:
{{OBSERVED_IOCS}}

(B) THREAT INTEL:
{{THREAT_INTEL}}
```
