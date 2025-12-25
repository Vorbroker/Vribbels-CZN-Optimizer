"""Image utility functions for UI components."""

from pathlib import Path
from PIL import Image, ImageTk, ImageDraw, ImageFont
import tkinter as tk


def create_icon_with_quantity(icon_path: str, quantity: int,
                               size=(140, 140)) -> ImageTk.PhotoImage:
    """
    Create an icon image with quantity text overlay in bottom right corner.

    Args:
        icon_path: Path to icon image file
        quantity: Quantity number to display
        size: Target size for the icon (width, height)

    Returns:
        PhotoImage ready for use in tkinter Label, or None if error occurs
    """
    try:
        # Load the icon image
        img = Image.open(icon_path)
        img = img.resize(size, Image.Resampling.LANCZOS)

        # Create drawing context
        draw = ImageDraw.Draw(img)

        # Prepare quantity text
        qty_text = str(quantity)

        # Try to use a nice font, fallback to default
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()

        # Get text bounding box at origin
        bbox = draw.textbbox((0, 0), qty_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Position in bottom right corner with padding
        padding = 8
        text_x = size[0] - text_width - padding
        text_y = size[1] - text_height - padding - 8  # Move up slightly

        # Draw background rectangle for better visibility
        # Use the actual bbox relative to text position for perfect alignment
        actual_bbox = draw.textbbox((text_x, text_y), qty_text, font=font)
        rect_padding = 4
        draw.rectangle(
            [actual_bbox[0] - rect_padding,
             actual_bbox[1] - rect_padding,
             actual_bbox[2] + rect_padding,
             actual_bbox[3] + rect_padding],
            fill=(0, 0, 0, 200)
        )

        # Draw the text
        draw.text((text_x, text_y), qty_text, fill="white", font=font)

        # Convert to PhotoImage
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"Error creating icon: {e}")
        return None
