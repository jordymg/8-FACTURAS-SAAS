# VALIDATION-PLAN — Invoice Photo-to-Data SaaS

Gate result: **2/4 — FAILED.** No PRD until at least one experiment below converts a FAIL into a PASS.

## Gate summary

| # | Question | Result | Notes |
|---|----------|--------|-------|
| 1 | Who has the problem? | PASS (weak) | Founder is the user. Uncle + ex-girlfriend's workplace are hypotheses, not evidence. |
| 2 | Current workaround + cost? | PASS (weak) | Manual entry or handing invoices to an accountant. Cost in time/money not quantified. |
| 3 | Would they pay? | FAIL | Nobody has been asked with a price attached. |
| 4 | Why you, why now? | FAIL | "Cheaper than existing tools" is not a moat. No distribution or timing advantage stated yet. |

## Experiment 1 — Price conversations
- Answers gate question: **#3**
- Method: 3 conversations — uncle, ex-girlfriend (her workplace), and 1 local accountant (SMA network). Show the working prototype, then ask: "¿Pagarías $X por mes por esto?" with a concrete number.
- Cost: ~3 hours
- Deadline: 2026-07-16
- Kill criterion: if 0 of 3 say yes to a concrete price, park the SaaS angle — keep it as a personal tool.

## Experiment 2 — Dogfooding with metrics
- Answers gate question: **#2** (quantify the cost)
- Method: founder uses the existing prototype on all his own invoices for 2 weeks. Log: minutes saved per invoice vs. manual entry, error rate of the OCR extraction.
- Cost: 0 extra hours (invoices need processing anyway)
- Deadline: 2026-07-16
- Kill criterion: if time saved is < 50% vs. manual, the value prop is too thin to sell.

## Experiment 3 — Competitor pricing map
- Answers gate question: **#4**
- Method: list the 3–5 existing tools ("ya hay sistemas que hacen esto"), their prices, and their onboarding friction. Identify one concrete wedge beyond price (e.g., WhatsApp-native intake, informal-invoice support, Spanish/AFIP-specific, accountant multi-client mode).
- Cost: ~2 hours
- Deadline: 2026-07-09
- Kill criterion: if no wedge exists other than "cheaper", park the idea.

## Rule
Re-run the gate after the deadlines. 3/4 or better → proceed to Discovery + PRD. Otherwise the idea is parked, which is a win, not a failure.
