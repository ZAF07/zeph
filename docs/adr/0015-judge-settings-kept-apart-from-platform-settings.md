# The Judge's settings are kept apart from the Platform Settings

The Judge's model, thinking and prompts are Admin-managed like Platform Settings (ADR-0004), but they live in their own store, seeded from `seed/evals/judge.yaml` and edited on the Eval area's Judge page. Platform Settings are what a Variant's Setting Overrides change and what Make Live writes, so keeping the Judge there would let one Variant be marked by a different Judge and let a run change how cases are marked; apart, every Variant in a run is marked by the same Judge, and a run keeps the Judge it used in its snapshot.
