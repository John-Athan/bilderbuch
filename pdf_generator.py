import os
import textwrap

from reportlab.lib.colors import black
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from model import State, load_state


def draw_wrapped_title(c, title, max_width, size):
    font_name = "Helvetica-Bold"
    font_size = 28
    wrapped_lines = textwrap.wrap(title, width=25)
    line_height = font_size + 4
    total_height = len(wrapped_lines) * line_height

    # Compute box dimensions
    padding = 12
    box_height = total_height + 2 * padding
    box_width = size - 2 * inch
    x_box = (size - box_width) / 2
    y_box = 0.75 * inch  # bottom margin

    # Adjust Y so that text is vertically centered inside the box
    text_start_y = y_box + padding + total_height - line_height

    # Semi-transparent white box
    c.saveState()
    c.setFillColorRGB(1, 1, 1)
    c.setFillAlpha(0.60)
    c.roundRect(x_box, y_box, box_width, box_height, 12, fill=1, stroke=0)
    c.restoreState()

    # Draw text lines
    c.setFillColorRGB(0.2, 0.2, 0.9)
    c.setFont(font_name, font_size)
    y = text_start_y
    for line in wrapped_lines:
        c.drawCentredString(size / 2, y, line)
        y -= line_height


def draw_text_box(c, text, size):
    font_name = "Helvetica"
    font_size = 14
    wrapped_lines = textwrap.wrap(text, width=65)  # slightly wider lines
    line_height = font_size + 4
    total_text_height = len(wrapped_lines) * line_height

    padding = 12
    box_width = size - inch  # wider box
    box_height = total_text_height + 2 * padding
    x_box = (size - box_width) / 2
    y_box = 0.6 * inch  # closer to bottom

    # Semi-transparent white box
    c.saveState()
    c.setFillColorRGB(1, 1, 1)
    c.setFillAlpha(0.60)
    c.roundRect(x_box, y_box, box_width, box_height, 10, fill=1, stroke=0)
    c.restoreState()

    # Draw text lines
    c.setFillColor(black)
    c.setFont(font_name, font_size)
    y = y_box + box_height - padding - font_size
    for line in wrapped_lines:
        c.drawCentredString(size / 2, y, line)
        y -= line_height


def generate_pdf(state: State, output_path="bilderbuch.pdf"):
    if state.storyline is None:
        raise ValueError("No storyline available in state.")

    size = 8 * inch  # square page: 8x8 inches
    c = canvas.Canvas(output_path, pagesize=(size, size))

    # Title Page
    title = state.storyline.title
    title_image_path = state.storyline.title_image_filepath

    if title_image_path and os.path.exists(title_image_path):
        c.drawImage(title_image_path, 0, 0, width=size, height=size, preserveAspectRatio=True, anchor='c')

    #draw_wrapped_title(c, title, max_width=size - 2 * inch, size=size)
    c.showPage()

    # Content Pages
    for page in state.storyline.pages:
        if page.image_filepath and os.path.exists(page.image_filepath):
            c.drawImage(page.image_filepath, 0, 0, width=size, height=size, preserveAspectRatio=True, anchor='c')

        draw_text_box(c, page.text, size)
        c.showPage()

    c.save()
    print(f"Bilderbuch saved to {output_path}")
    return output_path


if __name__ == "__main__":
    generate_pdf(load_state("59c4a22d-d892-4fdc-9f20-8fdd05a323ae"))
