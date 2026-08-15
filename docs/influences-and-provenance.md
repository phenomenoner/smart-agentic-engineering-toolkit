# Influences and provenance

The toolkit's workflow language is independently authored from observed engineering failures,
explicit product requirements, and primary documentation.

## Primary compatibility references

- [OpenAI: Build skills](https://developers.openai.com/plugins/build/skills) for focused skill
  structure, progressive disclosure, activation boundaries, and behavior testing.
- [Agent Skills specification](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/docs/specification.mdx)
  for portable `SKILL.md` frontmatter and resource conventions.

## Comparative repositories

- [addyosmani/agent-skills at `df1edb2`](https://github.com/addyosmani/agent-skills/tree/df1edb2e05487d0aa6d93c747141e0aed1187f25)
  (MIT) informed comparison of focused lifecycle skills and eval structure. This toolkit rejects
  universal multi-file, TDD, full-suite, and Git-workflow requirements.
- [obra/superpowers at `b36e082`](https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797)
  (MIT) was consulted for composability and skill-evaluation ideas. Its mandatory bootstrap,
  universal invocation/TDD, automatic worktrees/fan-out, and reviewer chains remain retired and are
  not authority here.

No distinctive prose, code, templates, fixtures, or scripts from those repositories are included
unless a future file-level provenance row says otherwise.

## Migrated project-authored skills

Several project-authored MIT skills were previously distributed through
`phenomenoner/Chatgpt-Codex-App-Plus` or a local authored source. Their exact origins, source hashes,
allow-listed files, modifications, and canonical cutover state are recorded in
`manifest/provenance.json`. Runtime state, caches, receipts, and private evidence are never source.
