---
name: lucaviruscress
description: "Use when working on the CressClaw / LucaVirusCress project: environment installation, requirements setup, Ollama + Langchain-Chatchat RAG, sequence alignment and 3D-structure based cress-virus identification, or OpenClaw integration."
---

# LucaVirusCress Skill

Use this skill when the task is about the CressClaw project workflow documented in `实战.docx` and the dependency list in `requirements.txt`.

## Primary Uses

- Set up the Python environment and install project dependencies.
- Build and query a knowledge base with Ollama and Langchain-Chatchat.
- Compare biological sequences with tools such as diamond, MMseqs2, and HMMER.
- Compare predicted 3D structures against reference Rep protein structures.
- Combine alignment, structure, and knowledge-base signals to judge whether a sequence is a Cress virus.
- Integrate the project with OpenClaw for downstream analysis.

## Recommended Workflow

1. Create and activate the conda environment described in the project notes.
2. Install the packages listed in `requirements.txt`.
3. Prepare the RAG stack:
   - pull the embedding and chat models with Ollama,
   - initialize Langchain-Chatchat,
   - configure `model_settings.yaml`,
   - build the knowledge base,
   - expose the chat API for OpenClaw.
4. Run sequence-based screening with diamond, MMseqs2, or HMMER.
5. Run 3D-structure comparison against the Rep protein reference.
6. Merge the evidence and produce a final judgment.

## Notes

- Keep installation steps aligned with the versions pinned in `requirements.txt`.
- Prefer the repository's documented workflow over inventing new tooling unless the user asks for an alternative.
- When helping with setup, point back to the original project notes for the exact commands and parameters.