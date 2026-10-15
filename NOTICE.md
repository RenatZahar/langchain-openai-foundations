# Attribution and adaptation notes

The seven notebooks are adapted from Module 1 of
https://github.com/langchain-ai/lca-lc-foundations, by LangChain, Inc. (MIT, 2026).
The upstream MIT license is reproduced unchanged in LICENSE.

The local learning adaptation was requested by Renat and prepared with Codex.
Renat's learning experiments include the small notes database tool and inspecting
messages and usage metadata. This does not claim authorship of the original course.

Changes in this edition:

- OpenAI-only configuration from a repository-local .env, with an empty key template.
- English explanations, comments and example questions; no machine-specific paths.
- Shared model factory and explicit separation of text, search and optional audio.
- OpenAI web search instead of Tavily, so no Tavily credentials are required.
- Extra teaching notes on Python objects/dictionaries, structured output and memory.
- Cleared execution outputs and widget metadata; only synthetic teaching examples.
- Setup checks, offline HTTP fixtures, kernel verification and pinned dependencies.

Modules 2 and 3, the original chat UI and unrelated repositories are not included.
