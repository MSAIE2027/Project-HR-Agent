# AI Tooling Disclosure

AI assistance was used for design discussion, implementation, documentation, retrieval evaluation, and debugging. The MSAIE HR Agent behavior, policies, examples, and synthetic records are specific to this standalone project.

The project instructions for future coding agents are in AGENTS.md. Local agent skills are developer tooling and are ignored by Git; they are not application dependencies.

## Verification record

The production embedding baseline remains `sentence-transformers/all-MiniLM-L6-v2` at 384 dimensions, with 120-word chunks and 20-word overlap. The 120/20 setting was the smallest of three tied configurations (120/20, 160/24, and 220/30). LLM endpoint settings remain separate from embedding settings.

The MiniLM-only retrieval comparison covered 15 hand-labeled policy queries, including five multi-family cases, at global k=1, 3, 5, and 8. At k=5, MMR λ=0.5 raised multi-family all-family coverage from 2/5 to 3/5 and overall expected-family recall from 0.81 to 0.86. Production now applies that reranker to up to ten score-ranked candidates and returns five citations. For multi-family questions, it searches up to three results per detected family, seeds one result per family, then fills remaining citations with MMR. Scoring weights, model, chunk size, and output budget remain unchanged.

A fresh read-only route comparison measured 100% expected-family coverage across the 15 queries, including 5/5 multi-family probes. The six-item read-only policy golden slice scored 100% on status, citation-prefix, and groundedness-proxy checks. Runtime retrieval reported `huggingface_dense_cosine`. These small, hand-authored query sets measure retrieval and deterministic proxy outcomes; they do not establish general semantic correctness.

Regression coverage was added for MMR diversity and family citations. Python syntax compilation and the read-only retrieval comparison were run. **Pytest, the full golden-set evaluation, transaction/action scenarios, browser review, and deployment were not run.** A non-fatal Hugging Face cache metadata write warning appeared during the retrieval run; the local model loaded and the comparison completed.

All employee records, policies, tickets, and actions remain fictional. No production HR system is connected.
