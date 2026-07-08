# Specification

## Overview

JpgLosslessCrop is a Windows-only desktop application for opening JPEG images, defining a crop region, and exporting a cropped version without introducing lossy recompression artifacts.

## Goals

- Provide a simple Tkinter-based user experience
- Support opening a JPEG file and displaying it in a canvas or preview area
- Allow the user to define a crop region visually
- Save the cropped result in a lossless or minimally lossy-friendly workflow
- Move the original file to the Recycle Bin when requested

## Non-goals for this initial scaffold

- No full implementation yet
- No production-ready image-processing pipeline yet
- No packaging or installer workflow yet
