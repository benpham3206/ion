# Goal

## Intent

Build a lamp that shows what "engineering intelligent systems and fluid interfaces" looks like in a single object: mechanical, electrical, and interaction design working as one piece.

## Concept

- Two parallel metal plates (brushed aluminum or copper), about 15 mm apart.
- A clear, water-like glass slab sits between them with a warm diffused glow from its center, fading to clear glass at the edges, so you see a glow and never a bare light source. Cool clear glass, warm light.
- Underglow: soft, diffused light washing out from under the base onto the desk, with no visible LEDs.
- The plates double as heatsinks for the LEDs.
- The plates also act as the controls: capacitive touch to turn on and dim, with no visible switch.

## Definition of done

- A working lamp that turns on, dims smoothly, and turns off by touching the plates.
- No visible LED hotspots through the diffuser.
- LED temperature stays within the LED's rated limit after 1 hour at full brightness, measured.
- Touch control works reliably with no false triggers, measured over repeated tests.
- CAD, wiring diagram, firmware, and a bill of materials are in this repo, and someone could rebuild it from the docs.
- Photos and a short demo video.

## Constraints

- Safe low voltage only (USB-C or a 12 V supply), no mains wiring inside the lamp.
- Buildable without owning a 3D printer (SJSU makerspace, cut metal, off-the-shelf parts).

## Open questions

- Plate material and finish.
- Controller board and power source.
- Overall size and plate shape.
