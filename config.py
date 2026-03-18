
####################################################
#    PARAMETERS
####################################################
TOP_K = 5
MODEL = "nomic-ai/nomic-embed-text-v1.5"
TOKENIZER = "nomic-ai/nomic-embed-text-v1.5"

DEVICE = "cpu"

PERSIST_DIR = './chroma_db/'
####################################################
#    PANEL PARAMETERS
####################################################

# sidebars (left and right)
SIDEBAR_BG= '#f0f0f0'
SIDEBAR_BORDER_RIGHT= '1px solid #ccc' # immediate value, could be broken or changed at once
SIDEBAR_BORDER_LEFT = SIDEBAR_BORDER_RIGHT
SIDEBAR_TITLE_FONT_SIZE= '16px'
SIDEBAR_TITLE_FONT_WEIGHT= 'bold'
SIDEBAR_TITLE_PADDING= '10px'
SIDEBAR_PADDING= '10px'
SIDEBAR_MIN_WIDTH= 200
SIDEBAR_MAX_WIDTH= 300
SIDEBAR_FONT_SIZE= '10px'
SIDEBAR_FONT_PADDING= '10px'

WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 800
WINDOW_TITLE = "DocView Pro"

# Color scheme - Dark theme matching the screenshot
BG_PRIMARY = "#1e1e1e"          # Main background
BG_SECONDARY = "#252526"        # Sidebar/panel background
BG_TERTIARY = "#2d2d30"         # Toolbar background
BG_QUATERNARY = "#3e3e42"       # Hover states

TEXT_PRIMARY = "#cccccc"        # Main text
TEXT_SECONDARY = "#969696"      # Secondary text
TEXT_ACCENT = "#4ec9b0"         # Accent color (teal/cyan)

BORDER_COLOR = "#3e3e42"        # Border color
SCROLLBAR_BG = "#1e1e1e"
SCROLLBAR_HANDLE = "#424242"

# PDF Viewer
PDF_BG = "#d4d4d4"              # PDF canvas background (light gray)
PDF_PLACEHOLDER_BG = "#2d2d30"

# Top bar
TOPBAR_HEIGHT = 40
TOPBAR_BG = "#2d2d30"

# Toolbar (PDF controls)
TOOLBAR_HEIGHT = 50
# TOOLBAR_BG = "#252526"
TOOLBAR_BG = "1e1e1e"

# Button styles
BUTTON_BG = "transparent"
BUTTON_HOVER_BG = "#3e3e42"
BUTTON_ACTIVE_BG = "#094771"
BUTTON_BORDER_RADIUS = "4px"
BUTTON_PADDING = "6px 12px"

# Icon colors
ICON_COLOR = "#cccccc"
ICON_ACTIVE_COLOR = "#4ec9b0"

# Fonts
FONT_FAMILY = "Segoe UI, Arial, sans-serif"
FONT_SIZE_NORMAL = "13px"
FONT_SIZE_SMALL = "12px"
FONT_SIZE_LARGE = "14px"

# PDF viewer settings
PDF_ZOOM_LEVELS = [25, 50, 75, 100, 125, 150, 200, 300, 400]
PDF_DEFAULT_ZOOM = 75


# Pdf area
CENTER_BG= 'white' # placeholder, need to change 

####################################################
# STATE MANAGEMENT
####################################################
CURRENT_PDF = None # holds the currently loaded pdf 
