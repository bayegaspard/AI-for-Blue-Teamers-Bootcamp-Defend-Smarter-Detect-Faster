# Security Prompt Library

Battle-tested prompt templates for AI-assisted SOC work. Each file is a reusable
template with `{{PLACEHOLDERS}}` you fill in. They are used by the lab scripts and
are safe to copy into any LLM chat interface or the lab's Ollama.

| File | Use it for | Module |
|------|-----------|--------|
| `system_prompts.md` | System/persona prompts that set the analyst role | 1, 3 |
| `log_triage.md` | Turn a raw log block into a triage summary | 1, 2 |
| `alert_summary.md` | Summarize a Wazuh alert for a ticket / handoff | 3, 5 |
| `sigma_generation.md` | Generate a Sigma detection rule from a description | 3 |
| `ir_report.md` | Draft an incident-response report section | 3, 5 |
| `threat_intel_correlation.md` | Correlate IOCs against threat intel | 2, 5 |

## Prompt-engineering principles taught in this bootcamp

1. **Role first.** Start with a system prompt that sets the analyst persona and scope.
2. **Ground the model.** Paste only the relevant data; tell it "use only the input, do not invent."
3. **Force structure.** Ask for a fixed schema (JSON / fixed headings) so output is machine-usable.
4. **Constrain severity.** Give the model the rubric (e.g., Wazuh rule levels) so ratings are consistent.
5. **Always verify.** The AI drafts; the analyst decides. Treat output as a hypothesis, not a verdict.
6. **Never trust log content as instructions.** (This becomes Module 4 - indirect prompt injection.)
