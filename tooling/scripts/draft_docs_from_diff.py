#!/usr/bin/env python3
"""Draft a docs update from an OpenAPI spec diff.

Real usage in CI: a GitHub Action runs this on every merge that touches
the spec, diffing the previous version against the new one, and opens a
PR with the drafted update for human review. It never commits directly.

Always builds the real prompt. Only fakes the network call when
ANTHROPIC_API_KEY isn't set, so the pipeline still runs end to end
without a live key.
"""
import argparse
import difflib
import json
import os
import sys
import urllib.request


def build_system_prompt(product_name: str) -> str:
    return f"""You are drafting a documentation update for the {product_name} API docs.

Follow the house style rules in the attached Vale configuration: consistent
terminology, no hedge words (simply, obviously, just, easily, clearly).
Every new or changed field needs one sentence explaining what it means and,
if it's new, which version introduced it.

Output only the replacement Markdown for the affected section. No preamble,
no explanation, no code fences around the whole output.
"""


def build_diff(old_path: str, new_path: str) -> str:
    with open(old_path) as f:
        old_lines = f.readlines()
    with open(new_path) as f:
        new_lines = f.readlines()
    diff = difflib.unified_diff(old_lines, new_lines, fromfile=old_path, tofile=new_path)
    return "".join(diff)


def build_user_prompt(diff_text: str, current_doc: str) -> str:
    return f"""Here is the diff to the OpenAPI spec:

```diff
{diff_text}
```

Here is the current documentation page that describes this part of the API:

```markdown
{current_doc}
```

Update the documentation page to reflect the diff, following the house style rules exactly.
"""


def call_claude(system_prompt: str, user_prompt: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    body = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 1000,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return "".join(block["text"] for block in data["content"] if block["type"] == "text")


def mock_draft(current_doc: str, diff_text: str) -> str:
    """Stand-in used only when no API key is present, so the demo still runs."""
    return current_doc.rstrip() + (
        "\n\n<!-- MOCK DRAFT: no ANTHROPIC_API_KEY present. "
        "This is a placeholder, not a real generated update. -->\n"
        f"\n<!-- Diff that would have driven the real draft:\n{diff_text}\n-->\n"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-spec", required=True)
    parser.add_argument("--new-spec", required=True)
    parser.add_argument("--doc", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--product-name", default="the API")
    args = parser.parse_args()

    diff_text = build_diff(args.old_spec, args.new_spec)
    with open(args.doc) as f:
        current_doc = f.read()

    system_prompt = build_system_prompt(args.product_name)
    user_prompt = build_user_prompt(diff_text, current_doc)

    try:
        draft = call_claude(system_prompt, user_prompt)
        source = "live Claude API call"
    except RuntimeError as e:
        print(f"[info] {e}, falling back to mock draft for this demo run", file=sys.stderr)
        draft = mock_draft(current_doc, diff_text)
        source = "MOCK (no ANTHROPIC_API_KEY present)"

    with open(args.out, "w") as f:
        f.write(draft)

    print(f"Draft written to {args.out}  (source: {source})")


if __name__ == "__main__":
    main()
