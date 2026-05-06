"""Create a visual thumbnail grid of slides from a PPTX file.

Usage:
    python thumbnail.py <input.pptx> [output_prefix] [--cols N]

Examples:
    python thumbnail.py presentation.pptx
    python thumbnail.py presentation.pptx thumbnails
    python thumbnail.py template.pptx preview --cols 4

Output:
    Creates <output_prefix>.jpg (default: thumbnails.jpg) with a grid of slide previews.
    Each slide is labeled with its filename (e.g., slide1.xml, slide2.xml).

Notes:
    - Default 3 columns, max 12 slides per grid
    - Uses LibreOffice to render slides at 150 DPI
    - For full-resolution visual QA, use soffice.py + pdftoppm instead
"""

import argparse
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def extract_slide_images(pptx_path: Path, temp_dir: Path) -> list[tuple[str, Path]]:
    """Extract slide images from PPTX using LibreOffice conversion."""
    pdf_path = temp_dir / "slides.pdf"

    # Use soffice to convert to PDF
    soffice_script = Path(__file__).parent / "office" / "soffice.py"
    if soffice_script.exists():
        result = subprocess.run(
            [sys.executable, str(soffice_script), "--headless", "--convert-to", "pdf",
             "--outdir", str(temp_dir), str(pptx_path)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Warning: soffice conversion failed: {result.stderr}", file=sys.stderr)
            return []
    else:
        # Fallback: try direct soffice call
        result = subprocess.run(
            ["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(temp_dir), str(pptx_path)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Warning: soffice not available: {result.stderr}", file=sys.stderr)
            return []

    if not pdf_path.exists():
        return []

    # Convert PDF to images
    img_dir = temp_dir / "imgs"
    img_dir.mkdir(exist_ok=True)

    result = subprocess.run(
        ["pdftoppm", "-jpeg", "-r", "150", str(pdf_path), str(img_dir / "slide")],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Warning: pdftoppm failed: {result.stderr}", file=sys.stderr)
        return []

    # Get list of slide images with slide names from PPTX
    slide_names = get_slide_names(pptx_path)

    images = []
    for i, img_file in enumerate(sorted(img_dir.glob("slide-*.jpg"))):
        slide_name = slide_names[i] if i < len(slide_names) else f"slide{i+1}.xml"
        images.append((slide_name, img_file))

    return images


def get_slide_names(pptx_path: Path) -> list[str]:
    """Get slide filenames from the PPTX archive."""
    slide_names = []
    with zipfile.ZipFile(pptx_path, "r") as zf:
        for name in sorted(zf.namelist()):
            if name.startswith("ppt/slides/slide") and name.endswith(".xml"):
                slide_names.append(Path(name).name)
    return slide_names


def create_thumbnail_grid(
    images: list[tuple[str, Path]],
    output_path: Path,
    cols: int = 3,
    thumb_size: tuple[int, int] = (320, 180),
    label_height: int = 20,
) -> None:
    """Create a grid thumbnail image from slide images."""
    if not images:
        print("Error: No images to create thumbnail grid", file=sys.stderr)
        sys.exit(1)

    rows = (len(images) + cols - 1) // cols
    thumb_width, thumb_height = thumb_size

    grid_width = cols * thumb_width
    grid_height = rows * (thumb_height + label_height)

    grid = Image.new("RGB", (grid_width, grid_height), color="white")
    draw = ImageDraw.Draw(grid)

    # Try to use a default font, fall back to minimal
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
    except (OSError, AttributeError):
        try:
            font = ImageFont.load_default()
        except (OSError, AttributeError):
            font = None

    for idx, (slide_name, img_path) in enumerate(images):
        row = idx // cols
        col = idx % cols

        x = col * thumb_width
        y = row * (thumb_height + label_height)

        # Load and resize thumbnail
        try:
            img = Image.open(img_path)
            img = img.resize(thumb_size, Image.LANCZOS)
            grid.paste(img, (x, y))
        except Exception as e:
            # Create placeholder
            placeholder = Image.new("RGB", thumb_size, color="#cccccc")
            grid.paste(placeholder, (x, y))
            print(f"Warning: Could not load {img_path}: {e}", file=sys.stderr)

        # Draw label
        label_y = y + thumb_height
        draw.rectangle([x, label_y, x + thumb_width, label_y + label_height], fill="#f0f0f0")

        if font:
            # Truncate name if too long
            display_name = slide_name if len(slide_name) <= 20 else slide_name[:17] + "..."
            draw.text((x + 4, label_y + 4), display_name, fill="#333333", font=font)
        else:
            display_name = slide_name[:20]
            draw.text((x + 4, label_y + 4), display_name, fill="#333333")

    grid.save(output_path, "JPEG", quality=85)
    print(f"Created {output_path} with {len(images)} slides in {cols} columns")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a visual thumbnail grid of slides from a PPTX file"
    )
    parser.add_argument("input", help="Input PPTX file")
    parser.add_argument(
        "output_prefix",
        nargs="?",
        default="thumbnails",
        help="Output prefix for the thumbnail image (default: thumbnails)"
    )
    parser.add_argument(
        "--cols",
        type=int,
        default=3,
        choices=range(1, 13),
        metavar="N",
        help="Number of columns in the grid (1-12, default: 3)"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    if not input_path.suffix.lower() == ".pptx":
        print(f"Error: {input_path} is not a .pptx file", file=sys.stderr)
        sys.exit(1)

    output_path = Path(f"{args.output_prefix}.jpg")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        print(f"Extracting slides from {input_path}...")
        images = extract_slide_images(input_path, temp_path)

        if not images:
            print("Error: Could not extract slide images", file=sys.stderr)
            print("Ensure LibreOffice (soffice) and poppler-utils (pdftoppm) are installed", file=sys.stderr)
            sys.exit(1)

        print(f"Creating thumbnail grid...")
        create_thumbnail_grid(images, output_path, cols=args.cols)


if __name__ == "__main__":
    main()
