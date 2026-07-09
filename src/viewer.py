"""Image viewer widget for JpgLosslessCrop.

This module provides a Tkinter canvas widget that displays a Pillow image,
keeps the original image data intact, and adds scrolling support so large
images can be navigated smoothly without zooming.
"""

from __future__ import annotations

from typing import Optional

import tkinter as tk
from PIL import Image, ImageTk

from src.crop_rectangle import CropRectangle


class ImageViewer(tk.Canvas):
    """A canvas-based image viewer with adaptive scaling and scrolling.

    The viewer keeps the source Pillow image untouched and renders a resized
    copy onto the canvas. Scrollbars are created for navigation when the
    displayed image is larger than the visible viewport. The widget can also
    overlay a first-pass crop rectangle for future editing workflows.
    """

    def __init__(self, master: tk.Misc, **kwargs: object) -> None:
        """Initialize the viewer widget.

        Args:
            master: The parent widget that will own the canvas.
            **kwargs: Additional keyword arguments passed to tkinter.Canvas.
        """
        # Use a neutral background so the image has a clear visual frame.
        kwargs.setdefault("bg", "light gray")
        kwargs.setdefault("highlightthickness", 0)

        # Create the canvas first so the rest of the viewer can attach to it.
        super().__init__(master, **kwargs)

        # Keep the original Pillow image unchanged so the display can be
        # regenerated from the source data whenever needed.
        self._source_image: Optional[Image.Image] = None

        # Store the current zoom factor used to scale the source image.
        self._zoom_factor: float = 1.0

        # Store the most recently generated Tk image object.
        self._photo_image: Optional[ImageTk.PhotoImage] = None

        # Store the canvas item id for the displayed image so it can be
        # updated or replaced later if needed.
        self._image_item_id: Optional[int] = None

        # Keep the crop overlay state in a dedicated model object so it can be
        # extended later without changing the viewer's public API.
        self._crop_rectangle: CropRectangle = CropRectangle()

        # Track the canvas item ids that belong to the crop overlay so they can
        # be safely cleared and redrawn whenever the image is re-rendered.
        self._crop_overlay_item_ids: list[int] = []

        # Create the horizontal and vertical scrollbar widgets that will let
        # the user move around large images. They are attached directly to this
        # canvas widget so the scrolling behavior stays self-contained.
        self._horizontal_scrollbar = tk.Scrollbar(self, orient="horizontal")
        self._vertical_scrollbar = tk.Scrollbar(self, orient="vertical")

        # Connect the canvas to the scrollbars so they react to scrolling.
        self.configure(
            xscrollcommand=self._horizontal_scrollbar.set,
            yscrollcommand=self._vertical_scrollbar.set,
        )
        self._horizontal_scrollbar.config(command=self.xview)
        self._vertical_scrollbar.config(command=self.yview)

        # Place the scrollbars along the lower and right edges of the canvas so
        # they feel like part of the viewer rather than separate controls.
        self._horizontal_scrollbar.place(relx=0.0, rely=1.0, relwidth=1.0, anchor="sw")
        self._vertical_scrollbar.place(relx=1.0, rely=0.0, relheight=1.0, anchor="ne")

        # Re-render the image whenever the visible viewport changes size.
        self.bind("<Configure>", self.on_canvas_resize)

        # Add mouse-wheel based scrolling so navigation feels natural.
        self.bind("<MouseWheel>", self._on_mouse_wheel)
        self.bind("<Shift-MouseWheel>", self._on_mouse_wheel)

        # Bind keyboard shortcuts for zooming so the viewer can be controlled
        # without using a mouse or toolbar. The explicit key-press bindings
        # make the shortcuts easier to extend later if more controls are added.
        self.bind(",", self._on_zoom_out)
        self.bind(".", self._on_zoom_in)
        self.bind("<KeyPress-comma>", self._on_zoom_out)
        self.bind("<KeyPress-period>", self._on_zoom_in)
        self.bind("q", self._toggle_crop_rectangle)
        self.bind("Q", self._toggle_crop_rectangle)
        self.bind("<KeyPress-q>", self._toggle_crop_rectangle)
        self.bind("<KeyPress-Q>", self._toggle_crop_rectangle)

    def set_image(self, image: Image.Image) -> None:
        """Assign a new Pillow image to the viewer.

        The original image is stored unchanged. A resized copy is generated to
        fit the current canvas size while preserving aspect ratio.

        Args:
            image: A Pillow image object to display.
        """
        # Make a copy so the viewer owns its own source state and does not
        # accidentally mutate the caller's image object.
        self._source_image = image.copy()

        # Reset the zoom so the next fit operation uses the current viewport.
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

        # Read the canvas size. Tk may report values that are temporarily zero
        # during initialization, so the viewer should skip fitting in that case.
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1:
            return

        # Calculate the scale needed to fit the entire image inside the canvas.
        image_width, image_height = self._source_image.size
        width_scale = canvas_width / max(image_width, 1)
        height_scale = canvas_height / max(image_height, 1)
        self._zoom_factor = min(width_scale, height_scale)

        # Avoid scaling the image up beyond its natural size when the viewport
        # is much larger than the source image.
        self._zoom_factor = max(self._zoom_factor, 0.1)

        # Redraw using the newly calculated zoom factor.
        self.redraw()

    def redraw(self) -> None:
        """Render the current image onto the canvas.

        The method resizes the source image using Pillow's LANCZOS filter,
        converts it to a Tk-compatible image, and draws it at the top-left
        corner of the canvas. The scroll region is updated so the image can be
        navigated when it exceeds the viewport.
        """
        if self._source_image is None:
            self.delete("all")
            self._image_item_id = None
            self._crop_rectangle.visible = False
            self._update_crop_overlay()
            self._update_scrollbars()
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
        self._image_item_id = self.create_image(
            0,
            0,
            anchor="nw",
            image=self._photo_image,
        )

        # Rebuild the crop overlay after the image has been re-rendered so it
        # stays aligned with the current visible image size.
        self._update_crop_overlay()

        # Update the scrollbar state and the scroll region after drawing.
        self._update_scroll_region()
        self._update_scrollbars()

    def on_canvas_resize(self, event: tk.Event[object]) -> None:
        """Handle canvas resize events by redrawing the current image.

        When the canvas dimensions change, the viewer redraws the current image
        so the visible portion stays appropriately scaled and the scroll region
        remains consistent with the new viewport.

        Args:
            event: The Tkinter resize event object.
        """
        # Ignore events that do not provide a meaningful viewport size.
        if event.width <= 1 or event.height <= 1:
            return

        # Keep the current zoom factor and re-render the image to fit the new
        # canvas dimensions. The current zoom reflects the previous fit and is
        # reused so the image size remains stable unless a new image is loaded.
        self.redraw()

    def _update_scroll_region(self) -> None:
        """Set the canvas scroll region based on the displayed image size."""
        if self._image_item_id is None:
            self.configure(scrollregion=(0, 0, 0, 0))
            return

        # Use the rendered image dimensions to define the scrollable surface.
        image_bbox = self.bbox(self._image_item_id)
        if image_bbox is None:
            self.configure(scrollregion=(0, 0, 0, 0))
            return

        # The bounding box includes the image position and size. This gives us a
        # reliable scroll region that matches the rendered content.
        left, top, right, bottom = image_bbox
        self.configure(scrollregion=(0, 0, max(right, 1), max(bottom, 1)))

    def _update_scrollbars(self) -> None:
        """Enable or disable the scrollbars depending on the image size."""
        canvas_width = max(self.winfo_width(), 1)
        canvas_height = max(self.winfo_height(), 1)
        image_width = int(self._source_image.size[0] * self._zoom_factor) if self._source_image is not None else 0
        image_height = int(self._source_image.size[1] * self._zoom_factor) if self._source_image is not None else 0

        # If the image is smaller than the visible canvas, the viewport does not
        # need to scroll and the scrollbars should return to the start.
        if image_width <= canvas_width:
            self.xview_moveto(0.0)
            self._horizontal_scrollbar.configure(state="disabled")
        else:
            self._horizontal_scrollbar.configure(state="normal")

        if image_height <= canvas_height:
            self.yview_moveto(0.0)
            self._vertical_scrollbar.configure(state="disabled")
        else:
            self._vertical_scrollbar.configure(state="normal")

    def _on_mouse_wheel(self, event: tk.Event[object]) -> str:
        """Scroll the canvas vertically or horizontally with the mouse wheel.

        Windows-style behavior is used: the vertical wheel scrolls content up and
        down, while Shift + wheel scrolls horizontally.

        Args:
            event: The Tkinter mouse-wheel event object.

        Returns:
            A Tkinter event break string to prevent the default browser-like
            scrolling behavior from interfering with the viewer.
        """
        # The wheel delta is usually expressed in units of 120. The sign tells
        # us the direction of the movement.
        delta = getattr(event, "delta", 0)
        if delta == 0:
            if getattr(event, "num", 0) == 4:
                delta = 120
            elif getattr(event, "num", 0) == 5:
                delta = -120

        # Shift + wheel is treated as horizontal movement, while plain wheel is
        # vertical movement.
        if event.state & 0x1:
            direction = -1 if delta > 0 else 1
            self.xview_scroll(direction, "units")
        else:
            direction = -1 if delta > 0 else 1
            self.yview_scroll(direction, "units")

        # Return "break" so the event does not propagate to other widgets.
        return "break"

    def _on_zoom_in(self, event: tk.Event[object]) -> str:
        """Increase the zoom level by 25% while preserving the current view."""
        self._change_zoom(1.25)
        return "break"

    def _on_zoom_out(self, event: tk.Event[object]) -> str:
        """Decrease the zoom level by 25% while preserving the current view."""
        self._change_zoom(0.75)
        return "break"

    def _change_zoom(self, factor: float) -> None:
        """Adjust the zoom level while maintaining the visible center point.

        The current viewport is preserved as much as possible by keeping the
        canvas coordinates under the cursor centered after the redraw.

        Args:
            factor: The zoom multiplier applied to the current zoom level.
        """
        if self._source_image is None:
            return

        # Keep the zoom within the supported bounds.
        new_zoom = self._zoom_factor * factor
        self._zoom_factor = min(max(new_zoom, 0.10), 16.00)

        # Preserve the current view by tracking the visible center in canvas
        # coordinates before redrawing, then restoring that position after the
        # image is re-rendered. The calculations are kept explicit so future
        # maintainers can adjust the behavior more easily.
        viewport_center_x = self.canvasx(self.winfo_width() / 2)
        viewport_center_y = self.canvasy(self.winfo_height() / 2)

        self.redraw()

        # Adjust the scroll position so the same viewport center remains in view.
        bbox = self.bbox("all")
        if bbox is None:
            return

        _, _, content_width, content_height = bbox
        if content_width > 1:
            self.xview_moveto(max(0.0, min(1.0, viewport_center_x / content_width)))
        if content_height > 1:
            self.yview_moveto(max(0.0, min(1.0, viewport_center_y / content_height)))

    def _update_crop_overlay(self) -> None:
        """Draw or clear the crop rectangle overlay for the current image.

        The overlay is drawn in canvas coordinates so it stays visually attached
        to the image even when the view is scrolled, zoomed, or the window is
        resized. The logic is intentionally simple because editing is still
        disabled and this first version only needs to show the selection.
        """
        # Remove any previously drawn overlay items so the canvas stays in sync
        # with the current image size and visibility state.
        for item_id in self._crop_overlay_item_ids:
            self.delete(item_id)
        self._crop_overlay_item_ids.clear()

        # If the crop rectangle is hidden, there is nothing to draw.
        if not self._crop_rectangle.visible or self._source_image is None:
            return

        # The rectangle should cover the full currently displayed image. The
        # scaled dimensions are derived directly from the current zoom factor so
        # the overlay keeps pace with the visible content.
        image_width, image_height = self._source_image.size
        scaled_width = max(1, int(image_width * self._zoom_factor))
        scaled_height = max(1, int(image_height * self._zoom_factor))

        # Reset the crop rectangle to the full-image bounds so the overlay always
        # starts from a coherent state when the user shows it.
        self._crop_rectangle.left = 0
        self._crop_rectangle.top = 0
        self._crop_rectangle.right = scaled_width
        self._crop_rectangle.bottom = scaled_height
        self._crop_rectangle.selected = False
        self._crop_rectangle.aspect_ratio = None

        # Draw the outline of the crop rectangle using the required cyan color
        # and a thin 2-pixel border.
        outline_id = self.create_rectangle(
            self._crop_rectangle.left,
            self._crop_rectangle.top,
            self._crop_rectangle.right,
            self._crop_rectangle.bottom,
            outline="cyan",
            width=2,
        )
        self._crop_overlay_item_ids.append(outline_id)

        # Add the four resize handles in the corners. They are intentionally
        # non-interactive at this stage, so they only communicate the selection
        # region and keep the initial visual experience simple.
        handle_size = 8
        half_size = handle_size // 2
        handle_positions = [
            (self._crop_rectangle.left, self._crop_rectangle.top),
            (self._crop_rectangle.right, self._crop_rectangle.top),
            (self._crop_rectangle.left, self._crop_rectangle.bottom),
            (self._crop_rectangle.right, self._crop_rectangle.bottom),
        ]
        for x_position, y_position in handle_positions:
            handle_id = self.create_rectangle(
                x_position - half_size,
                y_position - half_size,
                x_position + half_size,
                y_position + half_size,
                fill="white",
                outline="black",
                width=1,
            )
            self._crop_overlay_item_ids.append(handle_id)

    def _toggle_crop_rectangle(self, event: tk.Event[object]) -> str:
        """Show or hide the crop rectangle overlay.

        The rectangle is intended to be purely visual at this stage, so this
        method only toggles the overlay state and redraws it without enabling
        any editing behavior such as drag, move, or resize.

        Args:
            event: The Tkinter keyboard event object.

        Returns:
            A Tkinter event break string to prevent the keypress from falling
            through to any other handlers.
        """
        # Toggle the visibility flag and rebuild the overlay so the rectangle
        # appears immediately when the shortcut is used.
        self._crop_rectangle.visible = not self._crop_rectangle.visible
        if self._crop_rectangle.visible:
            self._crop_rectangle.selected = True
        self.redraw()
        return "break"
