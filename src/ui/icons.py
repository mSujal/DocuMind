"""
icons.py — All application SVG icons as string constants.

Usage:
    from src.ui.icons import svg_to_icon, ICON_UPLOAD
    from PyQt5.QtCore import QSize

    btn.setIcon(svg_to_icon(ICON_UPLOAD, color="#94a3b8", size=18))
    btn.setIconSize(QSize(18, 18))
    btn.setText("")

Requires: PyQt5.QtSvg  (ships with PyQt5)
"""

from PyQt5.QtCore import Qt, QByteArray, QRectF
from PyQt5.QtGui import QIcon, QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer


def svg_to_icon(svg_str: str, color: str = None, size: int = 18) -> QIcon:
    """
    Convert an SVG string to a QIcon.

    Args:
        svg_str : Raw SVG markup (use the constants below).
        color   : Hex color string to replace 'currentColor', e.g. '#94a3b8'.
                  Pass None to keep the SVG's own color values.
        size    : Pixel dimensions of the resulting icon (square).

    Returns:
        QIcon ready to be set on any QPushButton / QAction.
    """
    if color:
        svg_str = svg_str.replace("currentColor", color)

    renderer = QSvgRenderer(QByteArray(svg_str.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()

    return QIcon(pixmap)


# ═══════════════════════════════════════════════════════════════════════════ #
#  Top Bar                                                                    #
# ═══════════════════════════════════════════════════════════════════════════ #

# App logo / branding icon
ICON_LOGO = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
    <line x1="16" y1="13" x2="8" y2="13"/>
    <line x1="16" y1="17" x2="8" y2="17"/>
    <polyline points="10 9 9 9 8 9"/>
</svg>"""

# Toggle left file explorer sidebar
ICON_TOGGLE_SIDEBAR = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <rect x="3" y="3" width="18" height="18" rx="2"/>
    <line x1="9" y1="3" x2="9" y2="21"/>
</svg>"""

# Upload / open PDF
ICON_UPLOAD = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="17 8 12 3 7 8"/>
    <line x1="12" y1="3" x2="12" y2="15"/>
</svg>"""

# Print
ICON_PRINT = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <polyline points="6 9 6 2 18 2 18 9"/>
    <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
    <rect x="6" y="14" width="12" height="8"/>
</svg>"""

# Download / save
ICON_DOWNLOAD = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="7 10 12 15 17 10"/>
    <line x1="12" y1="15" x2="12" y2="3"/>
</svg>"""

# Toggle right AI chat sidebar
ICON_TOGGLE_CHAT = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
</svg>"""

# Settings / gear
ICON_SETTINGS = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="12" r="3"/>
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06
             a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09
             A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83
             l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09
             A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83
             l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09
             a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83
             l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09
             a1.65 1.65 0 0 0-1.51 1z"/>
</svg>"""


# ═══════════════════════════════════════════════════════════════════════════ #
#  Explorer Sidebar                                                           #
# ═══════════════════════════════════════════════════════════════════════════ #

# New folder
ICON_NEW_FOLDER = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
    <line x1="12" y1="11" x2="12" y2="17"/>
    <line x1="9" y1="14" x2="15" y2="14"/>
</svg>"""

# Refresh file tree
ICON_REFRESH = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <polyline points="23 4 23 10 17 10"/>
    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
</svg>"""

# Search / magnifier
ICON_SEARCH = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="11" cy="11" r="8"/>
    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
</svg>"""

# Folder (filled, used in file tree)
ICON_FOLDER = """<svg viewBox="0 0 24 24" fill="currentColor" stroke="none">
    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
</svg>"""

# PDF file (outline, used in file tree)
ICON_PDF_FILE = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
</svg>"""

# Chevron right — folder collapse toggle
ICON_CHEVRON_RIGHT = """<svg viewBox="0 0 24 24" fill="currentColor" stroke="none">
    <path d="M9 5l7 7-7 7z"/>
</svg>"""


# ═══════════════════════════════════════════════════════════════════════════ #
#  PDF Toolbar                                                                #
# ═══════════════════════════════════════════════════════════════════════════ #

# Previous page
ICON_PREV_PAGE = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <polyline points="15 18 9 12 15 6"/>
</svg>"""

# Next page
ICON_NEXT_PAGE = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <polyline points="9 18 15 12 9 6"/>
</svg>"""

# Zoom out (magnifier minus)
ICON_ZOOM_OUT = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="11" cy="11" r="8"/>
    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
    <line x1="8" y1="11" x2="14" y2="11"/>
</svg>"""

# Zoom in (magnifier plus)
ICON_ZOOM_IN = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="11" cy="11" r="8"/>
    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
    <line x1="11" y1="8" x2="11" y2="14"/>
    <line x1="8" y1="11" x2="14" y2="11"/>
</svg>"""

# Fit width (arrows pointing out horizontally inside a box)
ICON_FIT_WIDTH = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <rect x="2" y="3" width="20" height="18" rx="2"/>
    <line x1="7" y1="12" x2="17" y2="12"/>
    <polyline points="7 9 4 12 7 15"/>
    <polyline points="17 9 20 12 17 15"/>
</svg>"""

# Fit page / fullscreen corners
ICON_FIT_PAGE = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3M3 16v3a2 2 0 0 0 2 2h3m8 0h3a2 2 0 0 0 2-2v-3"/>
</svg>"""

# Rotate clockwise
ICON_ROTATE = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <polyline points="23 4 23 10 17 10"/>
    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
</svg>"""

# Select / cursor tool
ICON_SELECT = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z"/>
</svg>"""

# Highlight / annotation pen
ICON_HIGHLIGHT = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M12 20h9"/>
    <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
</svg>"""


# ═══════════════════════════════════════════════════════════════════════════ #
#  Chat Sidebar                                                               #
# ═══════════════════════════════════════════════════════════════════════════ #

# Clear / delete chat (trash)
ICON_TRASH = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <polyline points="3 6 5 6 21 6"/>
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
</svg>"""

# Attach file (paperclip)
ICON_ATTACH = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
</svg>"""

# Send message (paper plane)
ICON_SEND = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <line x1="22" y1="2" x2="11" y2="13"/>
    <polygon points="22 2 15 22 11 13 2 9 22 2"/>
</svg>"""


# ═══════════════════════════════════════════════════════════════════════════ #
#  Drop / Upload overlay                                                      #
# ═══════════════════════════════════════════════════════════════════════════ #

# Large upload icon used in drag-drop overlay
ICON_DROP_UPLOAD = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="17 8 12 3 7 8"/>
    <line x1="12" y1="3" x2="12" y2="15"/>
</svg>"""

# Image placeholder (used inside PDF page for missing images)
ICON_IMAGE_PLACEHOLDER = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
    <rect x="3" y="3" width="18" height="18" rx="2"/>
    <circle cx="8.5" cy="8.5" r="1.5"/>
    <polyline points="21 15 16 10 5 21"/>
</svg>"""

# ═══════════════════════════════════════════════════════════════════════════ #
#  MCQ                                                                        #
# ═══════════════════════════════════════════════════════════════════════════ #
ICON_MCQ = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <rect x="3" y="3" width="18" height="18" rx="3"/>
    <circle cx="7.5" cy="8" r="1" fill="currentColor" stroke="none"/>
    <line x1="10" y1="8" x2="18" y2="8"/>
    <circle cx="7.5" cy="12" r="1" fill="currentColor" stroke="none"/>
    <line x1="10" y1="12" x2="18" y2="12"/>
    <circle cx="7.5" cy="16" r="1" fill="currentColor" stroke="none"/>
    <line x1="10" y1="16" x2="18" y2="16"/>
    <polyline points="5 8 6.5 9.5 9 6.5" stroke-width="1.5"/>
</svg>"""