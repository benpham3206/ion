# LED shortlist: warm core + underglow

Goal: warm (2200-2700K) glow from the glass center, soft underglow, no visible dots. COB/FCOB strip gives dot-free light behind Satinice. Prices checked 2026-10-22 (Amazon US / Adafruit).

| Use | Part | Spec | Price | Link |
|---|---|---|---|---|
| **Core (pick)** | BTF-LIGHTING FCOB CCT, model FCOB-12V-640L-B-IP30 (ASIN B0DF7BHGZJ) | 12 V, tunable 2700-6500K, 640 LED/m, CRI 90+, 10 mm, 3-wire (+V, CW, WW) | $9.99 / 3 m | https://www.amazon.com/dp/B0DF7BHGZJ |
| **Underglow (pick)** | BTF-LIGHTING FCOB 2700K (ASIN B0CVXBF652) | 12 V, 2700K, 480 LED/m, CRI 90+, 8 mm, ~9-11 W/m | $14.99 / 5 m | https://www.amazon.com/dp/B0CVXBF652 |
| Alt (black PCB) | BTF-LIGHTING FCOB 2700K (ASIN B0DCVVDQP6) | same, black PCB (hides better in aluminum) | $14.99 / 5 m | https://www.amazon.com/dp/B0DCVVDQP6 |
| Alt (UL listed) | BTF-LIGHTING UL FCOB 2700K (ASIN B0F83T1ZJM) | UL listed, cut every 25 mm | ~CAD 23 (amazon.ca) | https://www.amazon.ca/dp/B0F83T1ZJM |

**Pick:** CCT FCOB for the core (warm 2700K by default, can tune; WLED drives CW/WW as 2 PWM channels), plain 2700K FCOB for the underglow. Both 12 V so one PD supply runs everything.

Gap: none of these go below 2700K. If bench test shows 2700K too cool, look at 2200K FCOB next (not yet sourced).
