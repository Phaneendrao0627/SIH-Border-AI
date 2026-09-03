"""Command-Line Interface (CLI) for local testing and validation of tampering detection."""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from tampering_detection.api import analyze_document
from tampering_detection.config import DetectionConfig
from tampering_detection.exceptions import TamperingDetectionError
from tampering_detection.logging_config import setup_logging


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="tampering-detection",
        description="Module 3: Standalone Document Tampering Detection CLI Tool",
    )
    parser.add_argument(
        "--image",
        "-i",
        type=str,
        required=True,
        help="Path to the document image file (JPEG, PNG, TIFF, etc.).",
    )
    parser.add_argument(
        "--document-id",
        type=str,
        default=None,
        help="Optional opaque document identifier.",
    )
    parser.add_argument(
        "--document-type",
        type=str,
        default="unknown",
        help="Document category (e.g., passport, visa, national_id, driving_license).",
    )
    parser.add_argument(
        "--regions",
        "-r",
        type=str,
        default=None,
        help="Optional path to a JSON file containing region coordinates (photo, text, stamp).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output directory to save visual artifacts and exported result JSON.",
    )
    parser.add_argument(
        "--save-artifacts",
        action="store_true",
        help="Generate and save ELA heatmaps and annotated region visualizations to disk.",
    )
    parser.add_argument(
        "--privacy-mode",
        action="store_true",
        help="Enforce strict privacy: prevents saving visual artifacts and logs.",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=None,
        help="Optional path to custom JSON configuration file overriding default weights and thresholds.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose DEBUG logging to stderr.",
    )

    return parser.parse_args()


def load_regions_file(file_path: Optional[str]) -> Optional[Dict[str, Any]]:
    """Safely read and parse region coordinates JSON file."""
    if not file_path:
        return None
    p = Path(file_path)
    if not p.exists():
        sys.stderr.write(f"Warning: Regions file not found: {file_path}\n")
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        sys.stderr.write(f"Error parsing regions JSON: {e}\n")
        return None


def main() -> None:
    """Main execution entrypoint for CLI."""
    args = parse_args()

    # 1. Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(level=log_level, stream=sys.stderr)

    # 2. Build configuration
    cfg_kwargs: Dict[str, Any] = {}
    if args.config:
        cfg_path = Path(args.config)
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg_kwargs = json.load(f)

    if args.privacy_mode:
        cfg_kwargs["privacy_mode"] = True
    if args.save_artifacts:
        cfg_kwargs["save_artifacts"] = True
    if args.output:
        cfg_kwargs["artifacts_dir"] = args.output

    config = DetectionConfig(**cfg_kwargs)

    # 3. Load regions
    regions = load_regions_file(args.regions)

    # 4. Execute Analysis
    try:
        result = analyze_document(
            image_source=args.image,
            document_id=args.document_id,
            document_type=args.document_type,
            regions=regions,
            options=config,
        )

        result_dict = result.model_dump()
        json_output = json.dumps(result_dict, indent=2)

        # Output JSON result to stdout
        sys.stdout.write(json_output + "\n")

        # Save result JSON to output directory if specified and permitted
        if args.output and config.get_effective_save_artifacts():
            out_dir = Path(args.output)
            out_dir.mkdir(parents=True, exist_ok=True)
            doc_tag = (args.document_id or "document").replace("/", "_").replace("\\", "_")
            json_file = out_dir / f"{doc_tag}_tampering_report.json"
            json_file.write_text(json_output, encoding="utf-8")

        sys.exit(0)

    except TamperingDetectionError as e:
        sys.stderr.write(f"\n[TamperingDetectionError] {e}\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"\n[Unexpected Error] {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
