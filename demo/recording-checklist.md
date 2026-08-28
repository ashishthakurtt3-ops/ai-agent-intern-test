# 2–4 Minute Demo Recording Checklist

This checklist is designed to produce the exact demo requested by the take-home assignment.

## Before recording

1. Create `.env` from `.env.example` and add `OPENAI_API_KEY`.
2. Run `pip install -r requirements.txt`.
3. Start the web app with `uvicorn app.web:app --reload`.
4. Open `http://127.0.0.1:8000`.
5. Keep a second terminal ready for `python -m evaluation.runner`.

## Scene 1 — Policy answer with citation

Ask:

> How long does a regular customer have to return an unused backpack?

Show the answer and the source citation for `01-returns-policy-current.md`.

## Scene 2 — Order lookup

Ask:

> Where is ORD-1007 and when should it arrive?

Show that the answer contains the current shipped status, UPS, and the August 22, 2026 estimate, without exposing customer email/address/risk/internal notes.

## Scene 3 — Multi-turn context

Ask:

> Do you ship internationally?

Then:

> What about Canada, and how long does it take?

Show that the second turn uses the first turn's context and cites the international shipping source.

## Scene 4 — Safe conflict / abstention

Ask either:

> Can I put the entire Breeze Tumbler in the dishwasher?

or:

> Are all fabrics and adhesives in your bags vegan?

Show that the agent does not guess. For the dishwasher question, it explicitly surfaces the conflict between the two current official sources and recommends human confirmation. For the vegan/material question, it states that the supplied information is insufficient.

## Scene 5 — Evaluation

Switch to the terminal and run:

```bash
python -m evaluation.runner
```

Show the individual case results plus category/overall output.

## Final README step

Record a 2–4 minute screen capture, export as GIF or MP4, upload it to the GitHub repository or a stable video host, and embed the GIF/video or a clickable thumbnail in the README's Demo recording section.

Do not include the API key or any real credentials in the recording.
