Test FHIR Bundles

Sample FHIR JSON Bundles to exercise ingestion and scheduling logic:

- 01_simple_amoxicillin_bundle.json
  - Single antibiotic, TID x 7 days, after food
- 02_polypharmacy_mixed_schedules.json
  - Metformin BID with meals, Atorvastatin QHS, Augmentin q12h x 10 days
- 03_complex_with_notes_and_prn.json
  - Albuterol PRN, Prednisone taper with notes, Warfarin daily with safety notes
- 04_large_duration_and_special_routes.json
  - Insulin SC nightly, Levothyroxine daily x 90 days with interaction note

Use: upload one of these files via Telegram using the "Upload FHIR record" option.
