# Slide Decks

One professional PowerPoint per module, paced for a 2-hour session. The decks are
graphic-first (timelines, chevron flows, pipeline diagrams, card grids, KPI tiles, a
bar chart, and takeaways), use plain-language explanations, and end each module with
key takeaways. House style: no em dashes, no emojis.

| Deck | Module | Slides |
|------|--------|--------|
| `Module1_Foundations.pptx` | Day 1 - AI for Blue Team Operations | 13 |
| `Module2_Detection.pptx` | Day 2 - Traffic Analysis and Threat Identification | 13 |
| `Module3_Prompt_Engineering.pptx` | Day 3 - Prompt Engineering for Security Operations | 13 |
| `Module4_Red_Teaming.pptx` | Day 4 - Introduction to AI Red Teaming | 14 |
| `Module5_Capstone.pptx` | Day 5 - End-to-End AI-Powered SOC Workflow | 14 |

The `.pptx` files are the deliverable; open and edit them in PowerPoint, Keynote, or
Google Slides. Each pairs with the matching module folder (instructor `README.md`,
`STUDENT_GUIDE.md`, labs, and solutions).

## Rebuilding the decks

The decks are generated from code so they stay consistent and easy to update.

```bash
python3 -m pip install python-pptx
python3 slides/build_decks.py        # regenerates all five .pptx files
```

- `deckkit.py` - the reusable design system (theme, colors, and the slide builders).
  `clean_text()` automatically strips em dashes and emojis, so edits stay on-style.
- `build_decks.py` - the content of all five decks. Edit the text or add slides here.

To restyle every deck at once (colors, fonts, header band), change `deckkit.py` and
rerun the build.
