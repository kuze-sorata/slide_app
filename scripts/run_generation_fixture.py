import argparse
import json
from pathlib import Path

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a fixed generation input against the local slide_app server.",
    )
    parser.add_argument(
        "input_json",
        help="Path to the generation request JSON file.",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Base URL of the local slide_app server.",
    )
    parser.add_argument(
        "--output-json",
        help="Optional path to save the generated slide JSON.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=180.0,
        help="Request timeout in seconds.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input_json)
    payload = json.loads(input_path.read_text(encoding="utf-8"))

    response = httpx.post(
        f"{args.base_url.rstrip('/')}/api/generate",
        json=payload,
        timeout=args.timeout,
    )
    response.raise_for_status()
    generated = response.json()

    formatted = json.dumps(generated, ensure_ascii=False, indent=2)
    print(formatted)

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(formatted + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
