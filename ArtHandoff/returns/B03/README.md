# B03 art return — production in progress

Original built-in image_gen generations, using B01 and B02 approved hero exports as style references. This return is not owner approval. All authored repository files stay inside B03; image_gen's default raw outputs are copied here. No Unity import or gameplay changes.

## Style lock

Dark Mythic Fantasy, painterly stylized 2.5D. Palette: charcoal `#2a2c31`, ash `#625c55`, oxblood `#6b2734`, basalt edge `#1d1f24`; fire `#ff6a2b`, Crystal `#8fe3ff` and `#2b5cff`. Key upper-left-front `#ffe9d0`, rim back-right `#9fe8ff`, ambient `#16233a`. Dark local-hue edge, no uniform black outline; cool 1–3 px rim; controlled broad brush planes.

Shared prompt prefix: “Dark Mythic Fantasy, painterly stylized 2.5D; orthographic 38.3-degree elevation, three-quarter front body turned 25 degrees toward screen-right. Key upper-left-front #ffe9d0, rim back-right #9fe8ff, ambient #16233a. Controlled broad brush planes, coloured local-hue dark edges without black outlines.”

## Method and prompts

Full actual prompts and attached reference paths: `source/prompts/*.json`. Raw sources, including rejected explorations: `source/sheets/`. `source/jobs.json` maps selected sources to exports. `python source/scripts/produce.py` performs utility-only extraction, component cleanup, uniform scale, torso registration, foot alignment, Lanczos reduction, sRGB metadata, and nearest-opaque defringe. It refuses upscaling and saves 2× masters. No anatomy is drawn with code.

Identity frames precede dependent poses; evolutions use the base identity and evolution actions use the evolution identity. Pose sheets are used as explicitly permitted by COMMON_CONTRACT §5. Tool accepts at most five attached references; B01 references rotate across calls alongside B02 heroes. Requested generation dimensions are not guaranteed; actual source dimensions must be measured.

## Progress and issues

Tidal: all eleven exports generated. First base sheet actions were rejected because water whips disappeared. First evolution sheet rejected for incorrect Floodbreaker weapon and an unrequested Healing Spring staff. Individual replacement evolution identities are selected. Full QA pending. Floodbreaker’s weapon reads as a crest-headed water pole-flail; its link is shorter and more rigid than the brief implies. Wide action silhouettes may reduce apparent height when uniformly fitted.

The later batch request overrides the older bible prohibition on authored attacks. No effects are emitted from attack sprites; Tidal's held water weapons and healer ribbons are intrinsic props. Portrait generated from the identity; its dark vignette preserves transparent exterior.

Workspace baseline: `qa/workspace_baseline.json`. No git state changes are made. Final delivered/blocked counts, intake and risk assessment will be recorded after production.
