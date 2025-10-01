# File Structure Template

This document outlines the file organization for [Project Name], ensuring modularity and maintainability across source, scripts, tests, and docs.

## Guidelines for Filling Out This Template
- Replace [Project Name] with your project's name.
- Customize directories for your stack (e.g., add `/source/[lang-dir]/` for Python/Rust).
- Use trees for visualization (Markdown code block).
- Include storage details (e.g., [storage: e.g., IndexedDB] for client).
- Adapt for languages: For Python, add `/source/api/`; for JS, `/source/client/`.
- Reference repo structure: This file defines the root layout; store it in /docs/agents/file_structure_doc.md.

## Standard Repo Layout (Mandatory)
All projects must follow this root structure to ensure cleanliness and agent cohesion. Deviations require explicit user approval.

[Tree: e.g., root/ ├── AGENTS.md │ ├── scratchpad.md │ ├── README.md │ ├── .env │ ├── source/ │   ├── client/ │   └── [backend]/ ├── scripts/ ├── tests/ └── docs/ Assumptions: [e.g., "Modular by layer"]; Known Issues: [e.g., "Cross-lang deps"].]

## [Layer: e.g., Client-Side]
[Root: /client; Structure: Tree with files; Browser Storage: [storage] keys. Example: /source/client/app.js. Assumptions: [e.g., "IndexedDB limits"]; Known Issues: [e.g., "Clear on uninstall"].]

## [Backend Layer: e.g., [Backend]]
[Root: /[backend-dir]; Structure: Tree; Storage: Examples. Assumptions: [e.g., "DHT sync"]; Known Issues: [e.g., "Peer latency"].]

## [Other Layers: e.g., [Storage]]
[Root: /[storage-dir]; Structure: Tree; Storage: Hashes. Assumptions: [e.g., "Content addressing"]; Known Issues: [e.g., "Offline fetch"].]

## Notes
[Interoperability: "Client fetches from [storage]"; etc. Include update policy. Assumptions: [e.g., "Version control"]; Known Issues: [e.g., "Merge conflicts"]. .env: For secrets (gitignore it); scratchpad.md: For task tracking; README.md: Overview with AGENTS.md link.]