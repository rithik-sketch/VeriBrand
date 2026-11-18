# AI and development-tool disclosure

This disclosure should be checked and edited by the team before submission so it reflects the tools actually used.

- ChatGPT was used as a development assistant for code suggestions, debugging, test-case design, packaging and documentation drafting.
- The current VeriBrand judge application does not call a live OpenAI or other AI model. Its runtime checks use configured Python rules, regular expressions and lexical matching against the local approved-facts knowledge base.
- No API key is needed to run the judge demo.
- The team should add any other AI tools used and describe each member's actual contribution.

Do not describe the runtime as GPT-powered, semantic AI or RAG unless those capabilities are actually implemented and tested in the submitted version.
