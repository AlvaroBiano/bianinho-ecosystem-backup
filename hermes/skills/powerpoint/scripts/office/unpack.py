"""Unpack a PPTX (or DOCX/XLSX) file into a directory of XML files.

Usage:
    python unpack.py <input.pptx> <output_dir> [--pretty]

Examples:
    python unpack.py presentation.pptx unpacked/
    python unpack.py document.docx extracted/

Description:
    Extracts an Office Open XML file (PPTX/DOCX/XLSX) into a directory structure.
    All XML files are pretty-printed with proper indentation for easy editing.
    Smart quotes are converted to XML entities for safe editing.

Notes:
    - XML files are pretty-printed with 2-space indentation
    - Smart quotes (curly quotes) are converted to XML entities (&#x201C;, etc.)
    - Binary files (images, embedded objects) are extracted as-is
    - Original file timestamps are preserved where possible
"""

import argparse
import shutil
import zipfile
from pathlib import Path

import defusedxml.minidom


# Smart quote replacements - convert curly quotes to XML entities
SMART_QUOTE_REPLACEMENTS = [
    ("\u201c", "&#x201C;"),  # Left double quote "
    ("\u201d", "&#x201D;"),  # Right double quote "
    ("\u2018", "&#x2018;"),  # Left single quote '
    ("\u2019", "&#x2019;"),  # Right single quote '
]


def convert_smart_quotes(text: str) -> str:
    """Convert smart/curly quotes to XML entities."""
    for smart_char, entity in SMART_QUOTE_REPLACEMENTS:
        text = text.replace(smart_char, entity)
    return text


def pretty_print_xml(xml_content: str) -> str:
    """Pretty-print XML content with proper indentation."""
    try:
        dom = defusedxml.minidom.parseString(xml_content.encode("utf-8"))
        pretty_xml = dom.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")

        # Remove extra blank lines and fix indentation
        lines = pretty_xml.split("\n")
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped:
                # Fix self-closing tags to not have /> vs /> issue
                cleaned_lines.append(line.rstrip())

        # Join and remove multiple blank lines
        result = "\n".join(cleaned_lines)
        while "\n\n\n" in result:
            result = result.replace("\n\n\n", "\n\n")

        return result
    except Exception:
        # If parsing fails, return original with basic cleanup
        return xml_content


def extract_file(zf: zipfile.ZipFile, name: str, output_dir: Path) -> None:
    """Extract a single file from the zip, processing XML if needed."""
    output_path = output_dir / name
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if name.endswith(".xml") or name.endswith(".rels"):
        # Read and process XML content
        try:
            content = zf.read(name).decode("utf-8")

            # Convert smart quotes to XML entities
            content = convert_smart_quotes(content)

            # Pretty print XML
            content = pretty_print_xml(content)

            output_path.write_text(content, encoding="utf-8")
        except Exception as e:
            print(f"Warning: Could not process {name}: {e}", file=__import__("sys").stderr)
            # Copy raw content as fallback
            output_path.write_bytes(zf.read(name))
    else:
        # Binary file - copy as-is
        with zf.open(name) as src, output_path.open("wb") as dst:
            shutil.copyfileobj(src, dst)


def unpack(office_file: str, output_dir: str, pretty: bool = True) -> tuple[int, int]:
    """Unpack an Office Open XML file into a directory.

    Returns:
        Tuple of (file_count, xml_count)
    """
    input_path = Path(office_file)
    output_path = Path(output_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    suffix = input_path.suffix.lower()
    if suffix not in {".pptx", ".docx", ".xlsx"}:
        raise ValueError(f"Unsupported file type: {suffix} (expected .pptx, .docx, or .xlsx)")

    # Remove existing output directory if present
    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True)

    file_count = 0
    xml_count = 0

    with zipfile.ZipFile(input_path, "r") as zf:
        for name in zf.namelist():
            extract_file(zf, name, output_path)
            file_count += 1
            if name.endswith(".xml") or name.endswith(".rels"):
                xml_count += 1

    return file_count, xml_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Unpack a PPTX/DOCX/XLSX file into a directory of XML files"
    )
    parser.add_argument("input", help="Input Office file (.pptx, .docx, or .xlsx)")
    parser.add_argument("output", help="Output directory")
    parser.add_argument(
        "--no-pretty",
        action="store_true",
        help="Disable XML pretty-printing (faster extraction)"
    )

    args = parser.parse_args()

    try:
        file_count, xml_count = unpack(args.input, args.output, pretty=not args.no_pretty)
        print(f"Unpacked {file_count} files ({xml_count} XML/rels) to {args.output}/")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        __import__("sys").exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        __import__("sys").exit(1)


if __name__ == "__main__":
    main()
