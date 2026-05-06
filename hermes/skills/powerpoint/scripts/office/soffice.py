"""LibreOffice wrapper for converting Office files to PDF and other formats.

Usage:
    python soffice.py [--headless] [--convert-to FORMAT] [--outdir DIR] <file(s)>

Examples:
    python soffice.py --headless --convert-to pdf presentation.pptx
    python soffice.py --headless --convert-to pdf --outdir ./output/ presentation.pptx
    python soffice.py --headless --convert-to png --outdir ./images/ slide.pptx

Description:
    Wrapper around LibreOffice's soffice command with proper handling for:
    - Headless mode (no GUI)
    - Output directory specification
    - Format conversion (pdf, png, jpg, docx, xlsx, etc.)
    - Sandbox compatibility (uses user-provided temp directories)

Notes:
    - Supported formats depend on LibreOffice installation
    - Common conversion targets: pdf, png, jpg, docx, xlsx, pptx, odt, ods, odp
    - PDF export preserves formatting and is useful for visual QA
    - PNG/JPG export creates individual images per slide (use --outdir)
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def find_soffice() -> Path | None:
    """Find the LibreOffice soffice executable."""
    # Check common locations
    possible_paths = [
        Path("/usr/bin/soffice"),
        Path("/usr/local/bin/soffice"),
        Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
        Path(os.path.expanduser("~/Applications/LibreOffice.app/Contents/MacOS/soffice")),
    ]

    # Check if soffice is in PATH
    if shutil.which("soffice"):
        return Path(shutil.which("soffice"))

    for path in possible_paths:
        if path.exists():
            return path

    return None


def run_soffice(
    files: list[str],
    output_dir: str | None = None,
    format: str | None = None,
    headless: bool = True,
) -> tuple[int, str]:
    """Run LibreOffice soffice to convert files.

    Args:
        files: List of input files to convert
        output_dir: Output directory (uses temp dir if None)
        format: Target format (e.g., 'pdf', 'png')
        headless: Run in headless mode (no GUI)

    Returns:
        Tuple of (return_code, output_message)
    """
    soffice = find_soffice()
    if soffice is None:
        return 1, "Error: LibreOffice (soffice) not found. Install LibreOffice to use this feature."

    if not files:
        return 1, "Error: No input files specified"

    # Validate input files exist
    for f in files:
        if not Path(f).exists():
            return 1, f"Error: Input file not found: {f}"

    # Create temporary output directory if not specified
    if output_dir is None:
        temp_out = tempfile.mkdtemp(prefix="soffice_")
        output_dir = temp_out
    else:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Build command
    cmd = [str(soffice)]

    if headless:
        cmd.append("--headless")

    if format:
        cmd.extend(["--convert-to", format])

    if output_dir:
        cmd.extend(["--outdir", str(output_dir)])

    cmd.extend(files)

    # Run conversion
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
        )

        if result.returncode != 0:
            return result.returncode, f"soffice failed: {result.stderr}"

        # Collect output files
        output_files = list(Path(output_dir).glob("*"))
        output_names = [f.name for f in output_files]

        return 0, f"Converted successfully to {output_dir}/\nOutput files: {', '.join(output_names)}"

    except subprocess.TimeoutExpired:
        return 1, "Error: soffice timed out after 2 minutes"
    except Exception as e:
        return 1, f"Error running soffice: {e}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="LibreOffice wrapper for converting Office files",
        epilog="Example: python soffice.py --headless --convert-to pdf presentation.pptx"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Run in headless mode (no GUI, default: True)"
    )
    parser.add_argument(
        "--convert-to",
        dest="format",
        help="Target format for conversion (e.g., pdf, png, jpg)"
    )
    parser.add_argument(
        "--outdir",
        help="Output directory (default: temp directory)"
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Input files to convert"
    )

    args = parser.parse_args()

    return_code, message = run_soffice(
        files=args.files,
        output_dir=args.outdir,
        format=args.format,
        headless=args.headless,
    )

    print(message)
    sys.exit(return_code)


if __name__ == "__main__":
    main()
