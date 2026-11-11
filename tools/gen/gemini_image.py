"""Ask Gemini for an image, with optional reference images, and save it into the project.

    .venv\\Scripts\\python.exe tools/gen/gemini_image.py --out assets/characters/concepts/hero_a.png
        --ref assets/surface_side.png --prompt-file tools/gen/prompts/hero_a.txt

The API key is read from the GEMINI_API_KEY environment variable (never stored in the repo).
Only the prompt and the given reference images are sent. Every saved image gets a sidecar
<name>.txt with the model, prompt and references, so concepts stay traceable.
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--prompt", default=None)
    parser.add_argument("--prompt-file", default=None)
    parser.add_argument("--ref", nargs="*", default=[])
    parser.add_argument("--model", default="gemini-3.1-flash-image")
    args = parser.parse_args()
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set")
    prompt = args.prompt or Path(args.prompt_file).read_text(encoding="utf-8")

    parts = [{"text": prompt}]
    for ref in args.ref:
        data = base64.b64encode(Path(ref).read_bytes()).decode()
        parts.append({"inline_data": {"mime_type": "image/png", "data": data}})
    body = json.dumps({"contents": [{"parts": parts}],
                       "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}}).encode()
    request = urllib.request.Request(API.format(model=args.model), data=body, method="POST",
                                     headers={"Content-Type": "application/json", "x-goog-api-key": key})
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        print(f"HTTP {error.code}: {error.read().decode(errors='replace')[:1500]}")
        sys.exit(2)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    saved = False
    notes = []
    for part in result.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        blob = part.get("inline_data") or part.get("inlineData")
        if blob and not saved:
            out.write_bytes(base64.b64decode(blob["data"]))
            saved = True
        elif part.get("text"):
            notes.append(part["text"])
    usage = result.get("usageMetadata", {})
    out.with_suffix(".txt").write_text(
        f"model: {args.model}\nrefs: {', '.join(args.ref)}\nusage: {json.dumps(usage)}\n\n"
        f"prompt:\n{prompt}\n\nmodel notes:\n" + "\n".join(notes), encoding="utf-8")
    print(("saved " + str(out)) if saved else "no image returned: " + " ".join(notes)[:500])
    print("usage", usage)


if __name__ == "__main__":
    main()
