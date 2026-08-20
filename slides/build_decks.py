#!/usr/bin/env python3
"""
build_decks.py - generate the five module PowerPoint decks.

    python3 slides/build_decks.py

Each deck is graphic-first (timelines, chevron flows, pipelines, card grids,
KPI tiles, a bar chart, takeaways) and paced for a 2-hour session. Text is kept
short on purpose; the detailed steps live in each module's STUDENT_GUIDE.md.
No em dashes, no emojis (enforced by deckkit.clean_text).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deckkit import Deck, PALETTE as P  # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))

DAYS = [("Day 1", "Foundations"), ("Day 2", "Detection"),
        ("Day 3", "Prompt engineering"), ("Day 4", "AI red teaming"),
        ("Day 5", "Capstone")]

SEGMENTS = [("0:00 - 0:20", "Concept and demo"),
            ("0:20 - 1:40", "Guided hands-on labs"),
            ("1:40 - 2:00", "Debrief and Q and A")]


# ===========================================================================
def module1():
    d = Deck(1, "Foundations", "AI for Blue Team Operations", P["blue"])
    d.title_slide("Day 1", "2 hours", "How AI is changing defensive security work")
    d.timeline_slide("How today runs", SEGMENTS, labs=[
        ("Lab 1.1", "Connect to Ollama and Wazuh, and check the GPU"),
        ("Lab 1.2", "Your first AI conversation for security"),
        ("Lab 1.3", "AI-assisted log triage"),
        ("Lab 1.4", "Tour the Wazuh SIEM")])
    d.roadmap_slide("Where this fits in the week", 1, DAYS, kicker="The road ahead")
    d.kpi_slide("The problem: analysts are drowning in alerts", [
        ("11k+", "alerts per day in a busy SOC"),
        ("60%", "of alerts never get fully investigated"),
        ("30 min", "to triage a single alert by hand")],
        kicker="Why AI, why now",
        footer_note="Numbers are illustrative. AI does not replace the analyst; it removes the slow first pass so people focus on judgment.")
    d.chart_slide("Where AI saves time", ["Triage an alert", "Summarize an incident", "Draft a report"],
                  [("Manual (minutes)", [30, 25, 45]), ("AI-assisted (minutes)", [6, 4, 10])],
                  kicker="Minutes per task", caption="Illustrative. AI-assisted work still ends with a human check.",
                  series_colors=[P["slate"], P["blue"]])
    d.cards_slide("Where AI helps across the SOC", [
        ("Log analysis", "Turn thousands of raw lines into a plain-language summary and a verdict."),
        ("Alert triage", "Rank what matters first and explain why, with the evidence cited."),
        ("Incident response", "Draft timelines, summaries, and reports so responders move faster.")],
        kicker="Three everyday wins")
    d.cards_slide("AI-assisted automation", [
        ("Accelerating log parsing", "Turn raw, high-volume logs into structured, readable findings in seconds instead of scrolling."),
        ("Identifying anomalies", "Surface the unusual: odd logins, rare user-agents, and spikes a tired analyst would scroll past."),
        ("Supporting investigation workflows", "Draft the next steps, pivots, and summaries so the analyst investigates faster.")],
        kicker="Automation that speeds the first pass")
    d.cards_slide("The tools you will use", [
        ("Ollama and llama3.1 8b", "A large language model running on the lab GPU. Private, and no data leaves the lab."),
        ("Wazuh 4.14", "The SIEM. It collects logs, applies rules, and raises alerts."),
        ("Shared Python clients", "ollama_client and wazuh_client connect the two in a few lines of code.")],
        kicker="Your toolkit")
    d.pipeline_slide("How the lab connects together", [
        ("Student VM", "You run scripts and prompts", P["blue"]),
        ("Ollama GPU VM", "llama3.1 8b analyzes", P["violet"]),
        ("Wazuh SIEM", "Alerts and log store", P["teal"])],
        kicker="The architecture",
        caption="One .env file points every script at the real lab or a local offline copy.")
    d.cards_slide("Anatomy of a good AI request", [
        ("Role", "Set who the model is: a SOC analyst assistant."),
        ("Task", "Say what to do: summarize this log and give a verdict."),
        ("Data", "The log itself, kept separate from the instructions."),
        ("Constraints", "A fixed output shape so results stay consistent.")],
        columns=2, kicker="Prompt basics",
        intro="Every prompt in this course follows the same simple shape.")
    d.cards_slide("Human in the loop", [
        ("AI is a co-pilot", "It proposes. It does not decide."),
        ("Always verify", "Treat the output as a hypothesis backed by evidence."),
        ("Never trust data as instructions", "A preview of Day 4: attackers hide commands in logs.")],
        kicker="The mindset that keeps you safe")
    d.takeaways_slide("Key takeaways", [
        "AI is now part of the modern SOC for log analysis, triage, and response.",
        "A large language model turns raw logs into summaries and verdicts in seconds.",
        "A good prompt has four parts: role, task, data, and constraints.",
        "The analyst stays in control and verifies every AI output.",
        "Never let untrusted data act as instructions to the model."])
    d.closing_slide("Foundations set.", "Tomorrow you generate real attacks and catch them.",
                    next_hint="Next: Day 2, Applied Detection")
    return d.save(os.path.join(OUT, "Module1_Foundations.pptx"))


# ===========================================================================
def module2():
    d = Deck(2, "Applied Detection", "Traffic Analysis and Threat Identification", P["teal"])
    d.title_slide("Day 2", "2 hours", "Run real attacks. See the telemetry. Catch them.")
    d.timeline_slide("How today runs", SEGMENTS, labs=[
        ("Lab 2.1", "Bring up the targets and the attacker toolbox"),
        ("Lab 2.2", "SSH brute force and the Wazuh alerts it raises"),
        ("Lab 2.3", "Web SQL injection and login brute force"),
        ("Lab 2.4", "Parse the logs and correlate with threat intel"),
        ("Lab 2.5", "Hand the evidence to AI for a fast summary")])
    d.roadmap_slide("Where this fits in the week", 2, DAYS, kicker="The road ahead")
    d.cards_slide("Recap and today's goal", [
        ("Yesterday", "You connected AI to the SOC and ran your first triage."),
        ("Today", "You generate attacks in the lab and detect them."),
        ("Bridge", "Then hand the evidence to AI for a fast summary.")],
        kicker="From foundations to action")
    d.cards_slide("Two ways to detect threats", [
        ("Signature based", "Match known-bad patterns like a SQL keyword or a scanner name. Fast and precise, but blind to new tricks."),
        ("Behavior based", "Watch patterns over time, like many failed logins from one host. Catches bursts that no single line reveals.")],
        columns=2, kicker="Know the difference")
    d.cards_slide("Common attack vectors you will see", [
        ("Brute force", "Many login attempts to guess a password."),
        ("SQL injection", "Malicious input that bypasses a login or reads the database."),
        ("Path traversal", "Requests that try to reach files like /etc/passwd."),
        ("Scanning", "Probing many ports or paths to map the target.")],
        columns=2, kicker="The usual suspects")
    d.pipeline_slide("The detection pipeline", [
        ("Attacker", "The lab toolbox", P["red"]),
        ("Endpoint", "Victim web and SSH", P["amber"]),
        ("Wazuh", "Rules raise alerts", P["teal"]),
        ("Analyst", "Triage with AI", P["blue"])],
        kicker="Attack to alert",
        caption="Every attack you launch produces logs that Wazuh turns into alerts.")
    d.bullets_slide("Brute force, up close", [
        ("The signal", "Dozens of failed logins from one source in seconds."),
        ("The catch", "One successful login hidden inside the burst."),
        ("Wazuh rules", "5710 and 5712 flag failures; rule 100120 flags the burst."),
        ("The lesson", "The dangerous event is the success you almost missed.")],
        kicker="Behavior over time")
    d.bullets_slide("SQL injection, up close", [
        ("The trick", "The password field carries ' OR '1'='1 instead of a password."),
        ("Why it works", "The app builds its query as text, so the input becomes logic."),
        ("The result", "The condition is always true and the login is bypassed."),
        ("The fix", "Parameterized queries, input validation, and a rule that flags the pattern.")],
        kicker="Signature detection")
    d.flow_slide("Turning intel into a verdict", [
        ("Observe", "IPs and payloads from logs"),
        ("Correlate", "Match against the threat feed"),
        ("Prioritize", "Rank by severity"),
        ("Act", "Block and investigate")],
        kicker="Correlation",
        caption="Lab 2.4: correlate the attacking IPs with the threat intelligence feed.")
    d.bullets_slide("The detection logic you will write", [
        ("Count", "Failed logins per source IP."),
        ("Window", "Within a short time span, for example 60 seconds."),
        ("Threshold", "Flag any IP over the limit."),
        ("Enrich", "Check flagged IPs against threat intelligence.")],
        kicker="What a SIEM rule really does",
        intro="This is exactly what detect_bruteforce.py does, and what a SIEM rule encodes.")
    d.takeaways_slide("Key takeaways", [
        "Attacks leave a trail; detection is about reading that trail well.",
        "Signature detection is precise; behavior detection catches what single lines hide.",
        "Correlating with threat intelligence turns raw IPs into priorities.",
        "The scariest event in a brute force is the login that succeeded.",
        "AI turns a pile of attack logs into a clear summary in seconds."])
    d.closing_slide("You can see the attack now.", "Next you sharpen the tool that summarizes it: the prompt.",
                    next_hint="Next: Day 3, Prompt Engineering")
    return d.save(os.path.join(OUT, "Module2_Detection.pptx"))


# ===========================================================================
def module3():
    d = Deck(3, "Prompt Engineering", "Applied AI for Security Operations", P["violet"])
    d.title_slide("Day 3", "2 hours", "Turn prompting into a repeatable SOC skill.")
    d.timeline_slide("How today runs", SEGMENTS, labs=[
        ("Lab 3.1", "Prompt fundamentals: the six principles"),
        ("Lab 3.2", "Generate a Sigma detection rule with AI"),
        ("Lab 3.3", "Automate an incident summary and a report"),
        ("Lab 3.4", "Build an AI-assisted triage workflow")])
    d.roadmap_slide("Where this fits in the week", 3, DAYS, kicker="The road ahead")
    d.cards_slide("Why prompting is a SOC skill", [
        ("Speed", "Draft summaries and detection rules in seconds."),
        ("Consistency", "A good template gives the same shape every time."),
        ("Scale", "Handle more alerts without adding more people.")],
        kicker="The payoff")
    d.cards_slide("The six principles", [
        ("Role", "Tell the model who it is."),
        ("Ground", "Give it only the relevant data."),
        ("Structure", "Ask for a fixed output shape."),
        ("Constrain", "Provide the rating scale to use."),
        ("Verify", "Treat the output as a draft to check."),
        ("Guard the data", "Never let data act as instructions.")],
        columns=3, kicker="Prompt engineering in six moves")
    d.compare_slide("Bad prompt versus good prompt",
                    {"title": "Vague prompt", "lines": [
                        "'Is this log bad?'", "No role and no format",
                        "A rambling, unpredictable answer", "Hard to use or automate"]},
                    {"title": "Structured prompt", "lines": [
                        "Role: senior SOC analyst", "Fixed fields: verdict, confidence, evidence",
                        "Cites the exact lines", "Ready for a ticket or a script"]},
                    kicker="Same log, very different result")
    d.cards_slide("Anatomy of a security prompt", [
        ("Persona", "You are a detection engineer."),
        ("Task", "Convert this behavior into a Sigma rule."),
        ("Data", "The behavior description, kept separate."),
        ("Constraints", "Output valid YAML only and minimize false positives.")],
        columns=2, kicker="Four parts, every time")
    d.cards_slide("What you will automate", [
        ("Summarize incidents", "Alert JSON becomes a ticket-ready summary."),
        ("Generate detection rules", "A behavior becomes a Sigma rule draft."),
        ("Write reports", "Evidence becomes an incident report."),
        ("Triage at scale", "A queue of alerts becomes a ranked table.")],
        columns=2, kicker="Real SOC tasks")
    d.flow_slide("Generating a detection rule with AI", [
        ("Describe", "The attacker behavior"),
        ("Draft", "AI writes the Sigma YAML"),
        ("Validate", "Check syntax and logic"),
        ("Deploy", "Add to the SIEM and test")],
        kicker="AI drafts, you verify",
        caption="AI writes the first draft. The engineer always validates before anything is deployed.")
    d.pipeline_slide("The AI-assisted triage workflow", [
        ("Wazuh alerts", "Pulled by the client", P["teal"]),
        ("Prompt template", "alert_summary", P["violet"]),
        ("Ollama", "Structured triage", P["blue"]),
        ("Analyst table", "Rank and act", P["amber"])],
        kicker="Lab 3.4 end to end",
        caption="triage_workflow.py builds this whole chain and prints a ranked table.")
    d.bullets_slide("The guardrail that matters most", [
        ("AI drafts, the engineer verifies", "Especially for detection rules."),
        ("A wrong rule is worse than no rule", "It creates noise or a blind spot."),
        ("Test against real data", "Before anything reaches production.")],
        kicker="Trust, but verify")
    d.takeaways_slide("Key takeaways", [
        "Prompting is a core analyst skill, not a novelty.",
        "The six principles turn vague questions into reliable, reusable prompts.",
        "AI can draft Sigma rules, summaries, and reports in seconds.",
        "Structure the output and the result becomes machine-usable.",
        "AI drafts the detection; the engineer always validates it."])
    d.closing_slide("You can direct the AI now.", "Next you learn how attackers try to hijack it.",
                    next_hint="Next: Day 4, AI Red Teaming")
    return d.save(os.path.join(OUT, "Module3_Prompt_Engineering.pptx"))


# ===========================================================================
def module4():
    d = Deck(4, "AI Red Teaming", "Attacking and Defending AI Systems", P["red"])
    d.title_slide("Day 4", "2 hours", "Attack the AI, then defend it. Authorized and defensive.")
    d.timeline_slide("How today runs", SEGMENTS, labs=[
        ("Lab 4.1", "Direct prompt injection: flip the verdict"),
        ("Lab 4.2", "Extract the system prompt and jailbreak"),
        ("Lab 4.3", "Indirect injection through poisoned logs"),
        ("Lab 4.4", "Defense in depth, and detection with Wazuh"),
        ("Lab 4.5", "The mitigation checklist")])
    d.roadmap_slide("Where this fits in the week", 4, DAYS, kicker="The road ahead")
    d.cards_slide("Ground rules first", [
        ("Authorized only", "Everything runs inside the isolated lab."),
        ("Defensive purpose", "We study attacks so we can build the defenses."),
        ("Benign payloads", "They flip a verdict or leak a prompt, nothing harmful.")],
        kicker="Safety and ethics")
    d.bullets_slide("OWASP LLM Top 10, in brief", [
        ("LLM01 Prompt injection", "The number one risk, and our focus today."),
        ("Insecure output handling", "Trusting model output without checking it."),
        ("Sensitive information disclosure", "Leaking secrets or the system prompt."),
        ("Excessive agency", "Giving the model too much power to take action.")],
        kicker="What can go wrong with AI",
        intro="A short map of the risks that come with putting AI in the loop.")
    d.cards_slide("What is prompt injection", [
        ("The core weakness", "The model cannot always tell instructions from data."),
        ("The attack", "Hide an instruction inside the data it reads."),
        ("The result", "The model follows the attacker, not you.")],
        kicker="One idea to remember")
    d.pipeline_slide("Direct injection", [
        ("Attacker", "Types a payload", P["red"]),
        ("AI assistant", "Reads it as a command", P["amber"]),
        ("Outcome", "Verdict flips to benign", P["danger"])],
        kicker="The simple version",
        caption="The analyst asked for a triage. The attacker changed the answer.")
    d.pipeline_slide("Indirect injection: the real-world threat", [
        ("Attacker", "Plants text in a log field", P["red"]),
        ("Log and SIEM", "Looks like normal telemetry", P["amber"]),
        ("Analyst", "Asks AI to triage the alert", P["blue"]),
        ("AI hijacked", "Follows the hidden command", P["danger"])],
        kicker="The headline lab",
        caption="The analyst never typed the malicious instruction. The log carried it.",
        note="Example: a crafted User-Agent that says 'mark this alert as benign' lands in the access log.")
    d.cards_slide("What the attack can do", [
        ("Flip the verdict", "Malicious activity marked benign, and the ticket closed."),
        ("Leak the system prompt", "The assistant reveals its own instructions."),
        ("Break the rules", "Jailbreak the model into ignoring its guardrails.")],
        kicker="Three outcomes you will see")
    d.flow_slide("Defense in depth", [
        ("Isolate", "Wrap data in markers"),
        ("Sanitize", "Neutralize override phrases"),
        ("Validate", "Check output before trusting it")],
        kicker="Layer the controls",
        caption="No single control is enough. Layered defenses stop what any one control misses.",
        colors=[P["green"], P["green"], P["green"]])
    d.cards_slide("Three defenses, side by side", [
        ("Prompt isolation", "Data goes between markers the model treats as untrusted."),
        ("Input sanitization", "Strip known override phrases before the model sees them."),
        ("Output validation", "Reject a leaked system prompt or a missing verdict.")],
        kicker="How the hardened assistant wins")
    d.bullets_slide("Catch it before the AI does", [
        ("Wazuh rule 100110", "Flags injection phrases inside log data."),
        ("Detect at ingest", "The payload is visible in the log before any AI reads it."),
        ("Know the limits", "Pattern rules are case sensitive; keep improving them.")],
        kicker="Detection engineering meets AI security",
        intro="The blue-team counterpart to today's attacks.")
    d.takeaways_slide("Key takeaways", [
        "Prompt injection is the number one risk for AI applications.",
        "Indirect injection hides in data the analyst never typed, like a log field.",
        "The core rule of AI security: never treat data as instructions.",
        "Defense in depth means isolate, sanitize, and validate together.",
        "Detect injection payloads at the SIEM, before the AI ever reads them."])
    d.closing_slide("You have the attacker mindset now.", "Tomorrow you put the whole week together.",
                    next_hint="Next: Day 5, Capstone")
    return d.save(os.path.join(OUT, "Module4_Red_Teaming.pptx"))


# ===========================================================================
def module5():
    d = Deck(5, "Capstone", "End-to-End AI-Powered SOC Workflow", P["amber"])
    d.title_slide("Day 5", "2 hours", "Run the full incident, end to end, with AI, and spot the trap.")
    d.timeline_slide("How today runs", SEGMENTS, labs=[
        ("Detect", "Find the attack in Wazuh or the datasets"),
        ("Analyze", "Triage with AI, and verify it"),
        ("Respond", "Contain and correlate"),
        ("Report", "Draft the incident report with AI"),
        ("Adversarial", "Catch and resist the prompt injection")])
    d.roadmap_slide("Where this fits in the week", 5, DAYS, kicker="The finish line")
    d.section_slide("The mission", "Operation Nightjar",
                    "A multi-stage intrusion hit the lab overnight. You run the response.")
    d.flow_slide("The incident lifecycle", [
        ("Detect", "Find the attack"),
        ("Analyze", "Triage with AI"),
        ("Respond", "Contain and correlate"),
        ("Report", "Draft with AI")],
        kicker="Everything from Days 1 to 4",
        caption="You apply the full week, with AI supporting every stage.")
    d.cards_slide("What happened overnight", [
        ("Recon", "A scan mapped the running services."),
        ("Brute force", "Many login attempts against SSH and the web app."),
        ("SQL injection", "A login bypass from a scanner."),
        ("An odd entry", "One log line looks strange and needs a closer look.")],
        columns=2, kicker="The story in the logs")
    d.bullets_slide("Stage 1: Detect", [
        ("Pull the alerts", "From Wazuh, or from the datasets on the offline path."),
        ("Find the brute force", "Source 10.10.10.5, with a hidden successful login."),
        ("Find the injection", "Scanner 10.10.10.7 hitting the login page."),
        ("Note anything strange", "Keep a list of what needs a second look.")],
        kicker="Read the trail")
    d.pipeline_slide("Stage 2: Analyze with AI, but verify", [
        ("Alert", "The raw evidence", P["amber"]),
        ("AI triage", "Summary and verdict", P["blue"]),
        ("Your check", "Confirm against the data", P["green"])],
        kicker="Trust, then verify",
        caption="One entry will try to fool your AI. Do not accept a verdict you cannot confirm.")
    d.bullets_slide("Stage 3: Respond", [
        ("Contain", "Block the attacking sources."),
        ("Correlate", "Match the IPs to the threat feed."),
        ("Prioritize", "Handle the confirmed compromise first."),
        ("Preserve", "Keep the evidence for the report.")],
        kicker="Act on what you found")
    d.bullets_slide("Stage 4: Report", [
        ("Executive summary", "Plain language, written for management."),
        ("Timeline", "What happened, and when."),
        ("Technical detail", "With the supporting evidence."),
        ("Recommendations", "Prioritized and actionable.")],
        kicker="Tell the story clearly",
        intro="Use the AI report template, then edit every line for accuracy.")
    d.pipeline_slide("The trap", [
        ("Poisoned log", "Carries a hidden instruction", P["red"]),
        ("Naive AI", "Marks it benign", P["danger"]),
        ("Sharp analyst", "Flags the injection", P["green"])],
        kicker="The adversarial catch",
        caption="The top score goes to the analyst who catches and resists the prompt injection.")
    d.kpi_slide("How you are scored", [
        ("100", "points in total"),
        ("20", "points for the adversarial catch"),
        ("80", "cap if you miss the trap")],
        kicker="Grading",
        footer_note="capstone_check.py verifies your report sections, the attacking IPs, and the injection flag.")
    d.takeaways_slide("What you can now do", [
        "Operate as an AI-augmented blue team analyst.",
        "Run an incident from detection through reporting.",
        "Use AI to move faster without giving up control.",
        "Recognize and resist attacks against AI systems.",
        "Turn a week of labs into a repeatable daily workflow."])
    d.closing_slide("Congratulations.",
                    "You have completed the AI Blue Team and Intro to AI Red Teaming Bootcamp.",
                    next_hint="Valix AI  x  Evolve Academy")
    return d.save(os.path.join(OUT, "Module5_Capstone.pptx"))


if __name__ == "__main__":
    built = [module1(), module2(), module3(), module4(), module5()]
    for b in built:
        print("built", os.path.basename(b))
