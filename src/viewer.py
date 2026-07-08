"""Image viewer widget for JpgLosslessCrop.

This module provides a Tkinter-based canvas widget that displays a Pillow
image while preserving the original image data and scaling it to fit the
current canvas size without distortion.
"""

from __future__ import annotations

from typing import Optional

from PIL import Image, ImageTk
import tkinter as tk


class ImageViewer(tk.Canvas):
    """A canvas-based image viewer with adaptive scaling.

    The viewer keeps the original Pillow image unchanged and stores the
    currently displayed image as a Tk-compatible PhotoImage. It supports
    resizing the canvas and recalculating the displayed image size while
    preserving aspect ratio.
    """

    def __init__(self, master: tk.Misc, **kwargs: object) -> None:
        """Initialize the viewer widget.

        Args:
            master: The parent Tk widget that will own this canvas.
            **kwargs: Additional keyword arguments passed to tkinter.Canvas.
        """
        # Start with a light gray canvas background so the displayed image is
        # easy to see when the window is larger than the content.
        kwargs.setdefault("bg", "light gray")
        kwargs.setdefault("highlightthickness", 0)

        # Call the parent constructor first so the canvas exists before we
        # configure it with internal state.
        super().__init__(master, **kwargs)

        # Keep the original Pillow image untouched for future operations.
        self._source_image: Optional[Image.Image] = None

        # Store the current zoom factor used to scale the displayed image.
        self._zoom_factor: float = 1.0

        # Store the currently displayed Tk image object.
        self._photo_image: Optional[ImageTk.PhotoImage] = None

        # Bind resize events so the viewer can redraw when the canvas changes
        # size at runtime.
        self.bind("<Configure>", self.on_canvas_resize)

    def set_image(self, image: Image.Image) -> None:
        """Assign a new Pillow image to the viewer.

        The original image is stored unchanged. A resized copy is generated to
        fit the current canvas size while preserving aspect ratio.

        Args:
            image: A Pillow image object to display.
        """
        # Keep the original data intact for future operations.
        self._source_image = image.copy()

        # Reset the zoom to a neutral value before computing a new fit.
        self._zoom_factor = 1.0

        # Fit the image to the current canvas size immediately.
        self.fit_to_window()

    def fit_to_window(self) -> None:
        """Resize the image so it fits within the current canvas area.

        The method preserves aspect ratio and chooses a zoom factor based on the
        current canvas size and the source image dimensions.
        """
        if self._source_image is None:
            return

        # Read the canvas dimensions. Tk may report zero width/height during
        # initialization, in which case we cannot compute a meaningful scale.
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1:
            return

        # Calculate the scale needed to fit the full image inside the canvas.
        image_width, image_height = self._source_image.size
        width_scale = canvas_width / max(image_width, 1)
        height_scale = canvas_height / max(image_height, 1)
        self._zoom_factor = min(width_scale, height_scale)

        # Ensure the image is not scaled up beyond its natural size when the
        # canvas is large. This keeps the display stable and avoids unnecessary
        # enlargement.
        self._zoom_factor = max(self._zoom_factor, 0.1)

        # Redraw using the newly calculated zoom ratio.
        self.redraw()

    def redraw(self) -> None:
        """Render the current image onto the canvas.

        The method resizes the source image using Pillow's LANCZOS filter,
        converts it to a Tk-compatible image, and draws it at the top-left
        corner of the canvas.
        """
        if self._source_image is None:
            self.delete("all")
            return

        # Clear any existing canvas content before drawing the new image.
        self.delete("all")

        # Determine the scaled size while preserving aspect ratio.
        image_width, image_height = self._source_image.size
        scaled_width = max(1, int(image_width * self._zoom_factor))
        scaled_height = max(1, int(image_height * self._zoom_factor))

        # Resize the original image using a high-quality resampling filter.
        resized_image = self._source_image.resize(
            (scaled_width, scaled_height),
            Image.Resampling.LANCZOS,
        )

        # Convert the Pillow image into a Tk image object for canvas display.
        self._photo_image = ImageTk.PhotoImage(resized_image)

        # Draw the image at the top-left corner of the canvas.
        self.create_image(0, 0, anchor="nw", image=self._photo_image)

    def on_canvas_resize(self, event: tk.Event[object]) -> None:
        """Handle canvas resize events by redrawing the current image.

        When the canvas dimensions change, the viewer recomputes the size using
        the existing zoom factor so the image remains visible and proportionate.

        Args:
            event: The Tkinter resize event object.
        """
        # Ignore events that do not provide meaningful canvas dimensions.
        if event.width <= 1 or event.height <= 1:
            return

        # Keep the current zoom factor and re-render the image to fit the new
        # canvas dimensions. The current zoom reflects the previous fit and is
        # reused so the image size remains stable unless a new image is loaded.
        self.redraw()
