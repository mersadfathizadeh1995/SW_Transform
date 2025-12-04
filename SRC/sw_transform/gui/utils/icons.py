"""Icon loading utilities for the MASW GUI.

Copied from simple_app.py:
- lines 1327-1347 (_asset_path)
- lines 1349-1378 (_load_icon)
- lines 21-56 (app icon loading logic from __init__)
"""
from __future__ import annotations

import os
import tkinter as tk
from typing import Optional


# Module-level icon cache
_icon_cache: dict[str, tk.PhotoImage] = {}


def get_asset_path(name: str, base_dir: str | None = None) -> str:
    """Locate asset file, handling both exact names and @NxN suffixed variants.
    
    Copied from simple_app.py lines 1327-1347.
    
    Args:
        name: Asset filename (e.g., "ic_open.png")
        base_dir: Optional base directory. Defaults to assets_big folder.
    
    Returns:
        Full path to the asset file.
    """
    if base_dir is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets_big"))
    
    if not os.path.isdir(base_dir):
        return os.path.join(base_dir, name)  # return path anyway
    
    # Try exact match first
    p = os.path.join(base_dir, name)
    if os.path.isfile(p):
        return p
    
    # fallback: pick the largest file that starts with the prefix
    prefix = os.path.splitext(name)[0]
    try:
        best = None
        best_area = -1
        for fn in os.listdir(base_dir):
            # Match prefix (e.g., "ic_open" matches "ic_open@180x180.png")
            if fn.lower().startswith(prefix.lower()) and fn.lower().endswith('.png'):
                cand = os.path.join(base_dir, fn)
                try:
                    from PIL import Image
                    with Image.open(cand) as im:
                        w, h = im.size
                        if w * h > best_area:
                            best = cand
                            best_area = w * h
                except Exception:
                    continue
        if best:
            return best
    except Exception:
        pass
    return p


def load_icon(name: str, size: int, cache: dict | None = None) -> tk.PhotoImage | None:
    """Load and cache an icon, maintaining aspect ratio with proper scaling.
    
    Copied from simple_app.py lines 1349-1378.
    
    Args:
        name: Icon filename (e.g., "ic_open.png")
        size: Target size in pixels (icon will be fitted within size x size)
        cache: Optional cache dict. Defaults to module-level cache.
    
    Returns:
        PhotoImage or None if loading fails.
    """
    if cache is None:
        cache = _icon_cache
    
    try:
        key = f"{name}:{size}"
        if key in cache:
            return cache[key]
        
        from PIL import Image, ImageTk
        
        p = get_asset_path(name)
        if not os.path.isfile(p):
            return None
        
        im = Image.open(p).convert("RGBA")

        # Auto-crop transparent margins
        alpha = im.split()[-1]
        bbox = alpha.getbbox()
        if bbox:
            im = im.crop(bbox)

        # Calculate scaling to fit within size x size while maintaining aspect ratio
        orig_w, orig_h = im.size
        scale = min(size / orig_w, size / orig_h)
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)

        # Resize maintaining aspect ratio with high-quality resampling
        im = im.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Create transparent background and center the icon
        bg = Image.new("RGBA", (size, size), (255, 255, 255, 0))
        offset_x = (size - new_w) // 2
        offset_y = (size - new_h) // 2
        bg.paste(im, (offset_x, offset_y), im)

        tkimg = ImageTk.PhotoImage(bg)
        cache[key] = tkimg
        return tkimg
    except Exception:
        return None


def load_app_icon(root: tk.Tk, base_assets: str | None = None) -> Optional[tk.PhotoImage]:
    """Load and set the application icon for a Tk root window.
    
    Copied from simple_app.py lines 21-56.
    
    Args:
        root: The Tk root window
        base_assets: Optional path to assets folder. Defaults to assets_big.
    
    Returns:
        The PhotoImage used for iconphoto (if used), or None.
    """
    if base_assets is None:
        base_assets = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets_big"))
    
    # Search for the largest icon_app*.png
    src_png = None
    max_size = -1
    
    if os.path.isdir(base_assets):
        for fn in os.listdir(base_assets):
            if fn.lower().startswith("icon_app") and fn.lower().endswith(".png"):
                p = os.path.join(base_assets, fn)
                try:
                    from PIL import Image
                    with Image.open(p) as im:
                        w, h = im.size
                        if w * h > max_size:
                            max_size = w * h
                            src_png = p
                except Exception:
                    continue
    
    if src_png is None:
        return None
    
    app_icon = None
    try:
        from PIL import Image
        import tempfile
        
        ico_tmp = os.path.join(tempfile.gettempdir(), "sw_transform_icon_tmp.ico")
        with Image.open(src_png) as im:
            # Build ICO with multiple sizes for better scaling
            sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            im.save(ico_tmp, format='ICO', sizes=sizes)
        
        try:
            root.iconbitmap(ico_tmp)
        except Exception:
            # Fallback to iconphoto PNG
            app_icon = tk.PhotoImage(file=src_png)
            root.iconphoto(True, app_icon)
    except Exception:
        pass
    
    return app_icon


def clear_cache():
    """Clear the icon cache."""
    _icon_cache.clear()
