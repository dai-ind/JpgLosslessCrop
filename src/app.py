"""Application skeleton for JpgLosslessCrop.

This module defines the main Tkinter-based application class. The current
implementation focuses on creating a window skeleton that can be extended
later with image loading, crop selection, and export workflows.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional

from PIL import Image

from src.viewer import ImageViewer


class App:
    """Main application controller for the JpgLosslessCrop desktop UI.

    The class is intentionally lightweight at this stage. It creates the
    Tkinter root window and exposes lifecycle methods that can be expanded
    later with image handling, crop logic, and file-management features.
    """

    def __init__(self) -> None:
        """Initialize the application state and create the main window."""
        # Store the Tk root widget so it can be configured and reused later.
        self.root: Optional[tk.Tk] = None

        # Keep a direct reference to the viewer widget so keyboard shortcuts can
        # be routed to the crop overlay without changing the rest of the UI.
        self.viewer: Optional[ImageViewer] = None

        # Build the window immediately so the app is ready to run.
        self.initialize()

    def initialize(self) -> None:
        """Create and configure the Tkinter root window.

        This method is the central setup point for the application's visual
        shell. It creates the window, sets basic properties, and prepares a
        placeholder area for future UI components.
        """
        # Create the main Tk window that owns all other widgets.
        self.root = tk.Tk()

        # Set the window title so the application is recognizable in the OS.
        self.root.title("JpgLosslessCrop")

        # Give the window an initial size that leaves room for future panels.
        self.root.geometry("800x600")

        # Use a light gray background to provide a neutral, readable canvas.
        self.root.configure(bg="light gray")

        # Allow the user to resize the window as needed for future controls.
        self.root.resizable(True, True)

        # Build the initial UI content after the base window is ready.
        self._build_ui()

    def _build_ui(self) -> None:
        """Create the initial placeholder user interface.

        This helper keeps the UI construction separate from the lifecycle
        methods so future work can add widgets without cluttering the main
        application class.
        """
        if self.root is None:
            return

        # Keep the existing informational label so the window still communicates
        # the purpose of the application while the viewer adds the new crop
        # overlay experience beneath it.
        container = tk.Frame(self.root, bg="light gray")
        container.pack(expand=True, fill="both", padx=20, pady=20)

        placeholder = tk.Label(
            container,
            text="Image crop workflow will be implemented here.",
            bg="light gray",
            anchor="center",
        )
        placeholder.pack(fill="x", pady=(0, 8))

        # Add a viewer widget so the first visual crop rectangle has a place to
        # be rendered. The widget is initialized with a simple placeholder image
        # so the overlay is visible immediately on startup.
        self.viewer = ImageViewer(container, width=760, height=480)
        self.viewer.pack(expand=True, fill="both")
        self.viewer.set_image(self._build_placeholder_image())

        # Route the keyboard shortcut to the viewer so pressing Q toggles the
        # crop rectangle overlay without requiring additional controls.
        if self.root is not None and self.viewer is not None:
            self.root.bind("<KeyPress-q>", self.viewer._toggle_crop_rectangle)
            self.root.bind("<KeyPress-Q>", self.viewer._toggle_crop_rectangle)
            self.viewer.focus_set()

    def _build_placeholder_image(self) -> Image.Image:
        """Create a simple placeholder image for the viewer.

        The image is intentionally decorative and lightweight so the overlay can
        be observed even before real image-loading workflows are added.
        """
        image = Image.new("RGB", (640, 480), color=(240, 240, 240))

        # Add a few simple geometric shapes so the placeholder content has a
        # visible structure rather than being a blank field.
        for x_coordinate in range(0, 640, 80):
            for y_coordinate in range(0, 480, 80):
                image.paste((220, 230, 255), (x_coordinate, y_coordinate, x_coordinate + 40, y_coordinate + 40))

        # Draw a strong central shape that makes the image feel like a real
        # preview rather than an empty canvas.
        image.paste((255, 180, 120), (140, 100, 500, 380))
        image.paste((80, 120, 180), (180, 140, 460, 340))
        return image

    def run(self) -> None:
        """Start the Tkinter event loop.

        Calling this method begins processing user events and keeps the window
        open until the application is closed.
        """
        if self.root is None:
            raise RuntimeError("The application window has not been initialized.")

        # Enter the main loop so the window remains interactive.
        self.root.mainloop()

    def close(self) -> None:
        """Close the application window and free the root widget.

        This method is the cleanup hook for shutting down the UI cleanly.
        """
        if self.root is not None:
            # Destroy the window so the Tk event loop can exit gracefully.
            self.root.destroy()
            self.root = None


def main() -> None:
    """Create an application instance and start the UI."""
    app = App()
    app.run()


if __name__ == "__main__":
    main()
