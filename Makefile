# Recipes are prefixed with ">" instead of a tab (GNU make 3.82+).
.RECIPEPREFIX = >
PY ?= python3
PROMPT ?= how should I set epsilon for q-learning exploration

.PHONY: test validate hook-demo

test:
> $(PY) -m pytest -q

validate:
> $(PY) scripts/validate_context.py

hook-demo:
> $(PY) .claude/hooks/context_router.py --explain "$(PROMPT)"
