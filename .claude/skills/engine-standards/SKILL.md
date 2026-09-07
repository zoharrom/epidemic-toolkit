---
name: engine-standards
description: Enforce type hints, docstrings, and a corresponding pytest test for every new function added to the epidemic-toolkit codebase. Use when writing, editing, or reviewing Python code in this repo.
---

# Engine Standards

This project is a portfolio piece demonstrating software engineering rigor, not just working code. Apply these rules to every function added or modified under `src/epidemic_toolkit/`:

1. **Type hints are mandatory.** Every parameter and return value must be annotated. Use `from __future__ import annotations` and stdlib generics (`tuple[float, ...]`, `list[...]`, `collections.abc.Callable`) — no bare `Any` unless truly unavoidable, and no numpy/scipy types until those dependencies are actually introduced (step 2+).

2. **Every function needs a docstring.** Google-style: one-line summary, then `Args:` and `Returns:` sections. State units or shape where it isn't obvious (e.g. "S, I, R as population counts", "dt in the same time units as beta/gamma").

3. **Every new function gets a corresponding test.** No function is considered done until there's a pytest test exercising it in `tests/`, mirroring the source module name (e.g. `models/sir.py` -> `tests/test_sir.py`). At minimum, cover:
   - The normal/expected case.
   - One edge case (zero input, boundary parameter, degenerate state).
   - Any invariant the function should preserve (e.g. conservation, monotonicity), if applicable.

4. **Keep model and numerical code pure.** Functions in `models/` and `integrators/` must not do I/O, printing, or touch global state — they take inputs and return outputs. This keeps them trivially testable and reusable from the future API/frontend.

5. **No premature dependencies.** Don't reach for numpy/scipy/FastAPI/etc. before the roadmap step that introduces them (see CLAUDE.md). If a step's stdlib-only constraint makes something awkward, that's fine — it's the point.

When reviewing a diff against this repo, check each new/changed function against points 1-3 before considering the change complete.
