# Contributing

SelfDiff welcomes concrete improvements to source compatibility, evidence validation, accessibility and personal-insight workflows.

1. Explain the user-visible failure or workflow.
2. Reproduce it using the smallest synthetic input. Never submit real conversations, API keys, local databases or private screenshots.
3. Add a failing behavioral test, then implement the fix and run the suite.
4. Update the support matrix when a parser's compatibility changes.

See [development](docs/development.md) for commands. Source adapters must preserve speaker identity and stable message versions. Model-generated claims must cite exact source text. Missing evidence should produce an explicit gap, not an invented conclusion.

Keep model calls opt-in, exports under user control, and examples synthetic. Proposed scoring or diagnostic features need evidence and a separate design discussion; the current product does not offer them.
