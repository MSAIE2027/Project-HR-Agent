# Visual Retrieval Views

retrieval-comparison.svg compares global expected-family coverage for current scoring, dense-only scoring, and MMR λ=0.5 at k=1, 3, 5, and 8. It also annotates the production route: family seeding plus MMR λ=0.5 achieved complete coverage in all five labeled multi-family probes.

The report includes top-k and weight sensitivity, actual route selection, and a six-case read-only golden policy slice. See evaluation/retrieval-comparison.md. Regenerate the report and chart with evaluation/run_retrieval_comparison.py.
