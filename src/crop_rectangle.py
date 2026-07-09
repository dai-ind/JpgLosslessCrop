"""Future-ready crop rectangle model for optional crop interactions.

This module introduces a small, self-contained data structure that can later be
used by the viewer and image-processing layers to represent a crop selection.
The class is intentionally standalone so the current application can continue
using its existing behavior without any wiring changes.
"""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass
class CropRectangle:
    """Describe a rectangular crop region with optional display state.

    The rectangle is stored using the same coordinate convention used by many
    image editors: the left and top edges are inclusive bounds, while the right
    and bottom edges are exclusive bounds. This makes it easy to reason about
    width and height as simple differences between coordinates.

    The object also carries presentation and selection state so it can later be
    used by a user interface without introducing a second data structure.
    """

    # Geometry of the rectangle in image-space coordinates.
    left: int = 0
    top: int = 0
    right: int = 0
    bottom: int = 0

    # Optional aspect ratio constraint for future crop behavior.
    aspect_ratio: float | None = None

    # UI state for future rendering and interaction support.
    visible: bool = False
    selected: bool = False

    def width(self) -> int:
        """Return the rectangle's width as a non-negative integer.

        The width is derived from the horizontal distance between the left and
        right edges. Negative values are normalized to zero so the object can
        represent an empty or invalid selection without special casing.
        """
        # A rectangle with a right edge that is still to the left of the left
        # edge would otherwise report a negative width. The application can
        # safely treat that as an empty selection.
        return max(0, self.right - self.left)

    def height(self) -> int:
        """Return the rectangle's height as a non-negative integer.

        The height is derived from the vertical distance between the top and
        bottom edges. Like width(), negative values are normalized to zero for
        consistency and to keep empty selections simple.
        """
        # Keep the value predictable even when the rectangle has been partially
        # defined or has been inverted by later editing logic.
        return max(0, self.bottom - self.top)

    def clear(self) -> None:
        """Reset the rectangle to an empty, non-visible state.

        Clearing the object removes the geometry and resets any future UI state
        that might otherwise make a stale selection appear active.
        """
        # Reset the geometry to a neutral origin and remove the optional aspect
        # ratio and interaction flags so the object behaves like a fresh slate.
        self.left = 0
        self.top = 0
        self.right = 0
        self.bottom = 0
        self.aspect_ratio = None
        self.visible = False
        self.selected = False

    def copy(self) -> "CropRectangle":
        """Return a new rectangle instance with the same values.

        The method is intentionally explicit so future callers can duplicate a
        selection without sharing mutable state with the original object.
        """
        # The dataclass replacement helper creates a new object with the same
        # field values, preserving any future fields automatically.
        return replace(self)

    def is_empty(self) -> bool:
        """Return whether the rectangle has no meaningful size.

        A rectangle is considered empty when either its width or height is zero
        or negative. This makes it straightforward to distinguish an actual crop
        selection from a placeholder or cleared object.
        """
        # A zero-sized selection is still considered empty because it does not
        # describe a usable crop area for image processing.
        return self.width() <= 0 or self.height() <= 0
