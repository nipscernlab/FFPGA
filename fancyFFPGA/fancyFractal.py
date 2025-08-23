import os
import sys
import time
import json
import logging
import argparse
import threading
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any

import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageEnhance, ImageFilter
from scipy import ndimage
# O import de interp2d não é usado, pode ser removido para limpar o código.
# from scipy.interpolate import interp2d 
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox

# Configure modern appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class IconProvider:
    """
    Generates and provides minimalist icons as CTkImage objects using PIL.
    This avoids the need for external icon files.
    """
    _cache: Dict[str, ctk.CTkImage] = {}

    @classmethod
    def get_icon(cls, name: str, size: Tuple[int, int] = (20, 20)) -> Optional[ctk.CTkImage]:
        """
        Get an icon by name. Icons are cached to improve performance.
        """
        if name in cls._cache:
            return cls._cache[name]

        icon_creation_methods = {
            "app_logo": cls._create_app_logo,
            "dimensions": cls._create_dimensions_icon,
            "rendering": cls._create_rendering_icon,
            "enhancement": cls._create_enhancement_icon,
            "actions": cls._create_actions_icon,
            "open_file": cls._create_open_file_icon,
            "save_image": cls._create_save_image_icon,
            "view_log": cls._create_view_log_icon,
            "refresh": cls._create_refresh_icon,
        }

        creation_method = icon_creation_methods.get(name)
        if not creation_method:
            return None

        image = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        creation_method(draw, size)
        
        ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=size)
        cls._cache[name] = ctk_image
        return ctk_image

    @staticmethod
    def _create_app_logo(draw: ImageDraw.ImageDraw, size: Tuple[int, int]):
        """Abstract logo for the application."""
        padding = 2
        draw.rectangle(
            (padding, padding, size[0] - padding, size[1] - padding),
            outline="#8b5cf6",
            width=2
        )
        draw.point((size[0] // 2, size[1] // 2), fill="#a78bfa")
        draw.line(
            (padding * 3, padding * 3, size[0] - padding * 3, size[1] - padding * 3),
            fill="#8b5cf6",
            width=1
        )

    @staticmethod
    def _create_dimensions_icon(draw: ImageDraw.ImageDraw, size: Tuple[int, int]):
        padding = 3
        draw.rectangle(
            (padding, padding, size[0] - padding, size[1] - padding),
            outline="white",
            width=1
        )
        draw.line((padding, size[1] - padding, size[0] - padding, padding), fill="white", width=1)

    @staticmethod
    def _create_rendering_icon(draw: ImageDraw.ImageDraw, size: Tuple[int, int]):
        # A simple artist's palette
        draw.ellipse((2, 2, size[0] - 2, size[1] - 2), outline="white", width=1)
        draw.ellipse((5, 5, 9, 9), fill="white")
        draw.ellipse((size[0] - 9, size[1] - 9, size[0] - 5, size[1] - 5), fill="white")

    @staticmethod
    def _create_enhancement_icon(draw: ImageDraw.ImageDraw, size: Tuple[int, int]):
        # Simple star/sparkle
        cx, cy = size[0] // 2, size[1] // 2
        draw.line((cx, 2, cx, size[1] - 2), fill="white", width=1)
        draw.line((2, cy, size[0] - 2, cy), fill="white", width=1)
        draw.line((5, 5, size[0] - 5, size[1] - 5), fill="white", width=1)
        draw.line((5, size[1] - 5, size[0] - 5, 5), fill="white", width=1)

    @staticmethod
    def _create_actions_icon(draw: ImageDraw.ImageDraw, size: Tuple[int, int]):
        # Simple lightning bolt
        s = size[0]
        draw.polygon([(s*0.6, 2), (s*0.3, s*0.5), (s*0.5, s*0.5), (s*0.4, s-2), (s*0.7, s*0.5), (s*0.5, s*0.5)], fill="white")

    @staticmethod
    def _create_open_file_icon(draw: ImageDraw.ImageDraw, size: Tuple[int, int]):
        # Simple folder icon
        draw.rectangle((2, 6, size[0] - 2, size[1] - 2), outline="white", width=1)
        draw.rectangle((4, 3, 10, 8), outline="white", width=1)

    @staticmethod
    def _create_save_image_icon(draw: ImageDraw.ImageDraw, size: Tuple[int, int]):
        # Simple save/floppy disk icon
        draw.rectangle((3, 3, size[0] - 3, size[1] - 3), outline="white", width=1)
        draw.line((3, 12, size[0] - 3, 12), fill="white", width=1)
        draw.rectangle((size[0] // 2 - 3, 12, size[0] // 2 + 3, size[1] - 3), fill="white")

    @staticmethod
    def _create_view_log_icon(draw: ImageDraw.ImageDraw, size: Tuple[int, int]):
        # Simple bar chart icon
        draw.line((4, 4, 4, size[1] - 4), fill="white", width=2)
        draw.line((9, 8, 9, size[1] - 4), fill="white", width=2)
        draw.line((14, 12, 14, size[1] - 4), fill="white", width=2)

    @staticmethod
    def _create_refresh_icon(draw: ImageDraw.ImageDraw, size: Tuple[int, int]):
        # Simple circular arrow
        padding = 3
        draw.arc((padding, padding, size[0] - padding, size[1] - padding), start=30, end=300, fill="white", width=2)
        draw.polygon([(padding, size[1]//2), (padding+4, size[1]//2-4), (padding+4, size[1]//2+4)], fill="white")


@dataclass
class FractalSettings:
    """Fractal rendering and enhancement settings"""
    width: int = 256
    height: int = 256
    smoothness: float = 2.0
    contrast: float = 1.2
    saturation: float = 1.0
    exposure: float = 1.0
    focus: float = 1.0
    palette: str = "cosmic"
    theme: str = "classic"
    interpolation_method: str = "bicubic"
    gamma_correction: float = 0.8
    edge_enhancement: float = 0.3

@dataclass
class LogEntry:
    """Log entry for fractal generation tracking"""
    timestamp: datetime
    percentage: float
    pixels_processed: int
    elapsed_time: float
    estimated_remaining: Optional[float] = None

class ColorPalette:
    """Advanced color palette generator for fractal visualization"""
    
    @staticmethod
    def generate_palette(name: str, size: int = 1024) -> np.ndarray:
        """Generate color palette with specified size"""
        t = np.linspace(0, 1, size)
        
        palettes = {
            "cosmic": ColorPalette._cosmic_palette(t),
            "fire": ColorPalette._fire_palette(t),
            "ocean": ColorPalette._ocean_palette(t),
            "aurora": ColorPalette._aurora_palette(t),
            "nebula": ColorPalette._nebula_palette(t),
            "solar": ColorPalette._solar_palette(t),
            "ethereal": ColorPalette._ethereal_palette(t),
            "mystic": ColorPalette._mystic_palette(t)
        }
        
        return palettes.get(name, palettes["cosmic"])
    
    @staticmethod
    def _cosmic_palette(t):
        """Deep space inspired palette"""
        r = np.clip(255 * (0.1 + 0.7 * np.power(t, 2.0) + 0.2 * np.sin(8 * np.pi * t)), 0, 255)
        g = np.clip(255 * (0.05 + 0.4 * np.sin(4 * np.pi * t + np.pi/3) + 0.3 * t), 0, 255)
        b = np.clip(255 * (0.3 + 0.6 * np.power(1-t, 0.5) + 0.1 * np.cos(6 * np.pi * t)), 0, 255)
        return np.column_stack([r, g, b]).astype(np.uint8)
    
    @staticmethod
    def _fire_palette(t):
        """Fire and lava inspired palette"""
        r = np.clip(255 * np.power(t, 0.4), 0, 255)
        g = np.clip(255 * np.power(np.maximum(0, t - 0.2), 1.2), 0, 255)
        b = np.clip(255 * np.power(np.maximum(0, t - 0.7), 2.0), 0, 255)
        return np.column_stack([r, g, b]).astype(np.uint8)
    
    @staticmethod
    def _ocean_palette(t):
        """Ocean depths palette"""
        r = np.clip(255 * (0.1 + 0.3 * np.sin(2 * np.pi * t)), 0, 255)
        g = np.clip(255 * (0.3 + 0.5 * t + 0.2 * np.sin(4 * np.pi * t)), 0, 255)
        b = np.clip(255 * (0.6 + 0.4 * np.power(t, 0.8)), 0, 255)
        return np.column_stack([r, g, b]).astype(np.uint8)
    
    @staticmethod
    def _aurora_palette(t):
        """Aurora borealis palette"""
        r = np.clip(255 * (0.2 + 0.6 * np.sin(3 * np.pi * t + np.pi/6)), 0, 255)
        g = np.clip(255 * (0.4 + 0.5 * np.power(t, 0.6)), 0, 255)
        b = np.clip(255 * (0.1 + 0.7 * np.sin(2 * np.pi * t + np.pi/4)), 0, 255)
        return np.column_stack([r, g, b]).astype(np.uint8)
    
    @staticmethod
    def _nebula_palette(t):
        """Nebula inspired palette"""
        r = np.clip(255 * (0.4 + 0.4 * np.power(t, 1.5) + 0.2 * np.sin(6 * np.pi * t)), 0, 255)
        g = np.clip(255 * (0.1 + 0.3 * t + 0.4 * np.sin(4 * np.pi * t)), 0, 255)
        b = np.clip(255 * (0.5 + 0.4 * np.power(1-t, 0.7)), 0, 255)
        return np.column_stack([r, g, b]).astype(np.uint8)
    
    @staticmethod
    def _solar_palette(t):
        """Solar flare palette"""
        r = np.clip(255 * (0.8 + 0.2 * np.sin(8 * np.pi * t)), 0, 255)
        g = np.clip(255 * (0.4 + 0.4 * np.power(t, 0.8)), 0, 255)
        b = np.clip(255 * (0.1 + 0.2 * t), 0, 255)
        return np.column_stack([r, g, b]).astype(np.uint8)
    
    @staticmethod
    def _ethereal_palette(t):
        """Ethereal, otherworldly palette"""
        r = np.clip(255 * (0.6 + 0.3 * np.sin(5 * np.pi * t)), 0, 255)
        g = np.clip(255 * (0.2 + 0.6 * np.power(t, 1.2)), 0, 255)
        b = np.clip(255 * (0.7 + 0.2 * np.cos(3 * np.pi * t)), 0, 255)
        return np.column_stack([r, g, b]).astype(np.uint8)
    
    @staticmethod
    def _mystic_palette(t):
        """Mystic, magical palette"""
        r = np.clip(255 * (0.3 + 0.5 * np.power(t, 0.9) + 0.2 * np.sin(7 * np.pi * t)), 0, 255)
        g = np.clip(255 * (0.1 + 0.4 * np.sin(3 * np.pi * t + np.pi/2)), 0, 255)
        b = np.clip(255 * (0.5 + 0.4 * np.power(1-t, 0.6) + 0.1 * np.cos(5 * np.pi * t)), 0, 255)
        return np.column_stack([r, g, b]).astype(np.uint8)

class FractalTheme:
    """Fractal interpretation themes"""
    
    @staticmethod
    def apply_theme(data: np.ndarray, theme: str, settings: FractalSettings) -> np.ndarray:
        """Apply theme-specific transformations to fractal data"""
        if theme == "classic":
            return FractalTheme._classic_theme(data, settings)
        elif theme == "smooth":
            return FractalTheme._smooth_theme(data, settings)
        elif theme == "dramatic":
            return FractalTheme._dramatic_theme(data, settings)
        elif theme == "organic":
            return FractalTheme._organic_theme(data, settings)
        elif theme == "crystalline":
            return FractalTheme._crystalline_theme(data, settings)
        elif theme == "ethereal":
            return FractalTheme._ethereal_theme(data, settings)
        else:
            return data
    
    @staticmethod
    def _classic_theme(data, settings):
        """Classic Mandelbrot interpretation"""
        # Apply gamma correction
        enhanced = np.power(data, settings.gamma_correction)
        
        # Smooth transitions
        if settings.smoothness > 1.0:
            enhanced = ndimage.gaussian_filter(enhanced, sigma=settings.smoothness * 0.5)
        
        return enhanced
    
    @staticmethod
    def _smooth_theme(data, settings):
        """Ultra-smooth interpretation"""
        # Heavy smoothing
        smoothed = ndimage.gaussian_filter(data, sigma=settings.smoothness)
        
        # Blend with original
        enhanced = 0.7 * smoothed + 0.3 * data
        
        # Apply soft gamma
        enhanced = np.power(enhanced, 0.9)
        
        return enhanced
    
    @staticmethod
    def _dramatic_theme(data, settings):
        """High contrast dramatic interpretation"""
        # Enhance edges
        edges = ndimage.sobel(data)
        enhanced = data + settings.edge_enhancement * edges
        
        # Strong gamma correction
        enhanced = np.power(enhanced, 0.6)
        
        # Increase local contrast
        enhanced = ndimage.rank_filter(enhanced, rank=4, size=3) * settings.contrast
        
        return np.clip(enhanced, 0, 1)
    
    @staticmethod
    def _organic_theme(data, settings):
        """Organic, flowing interpretation"""
        # Multiple scale smoothing
        smooth1 = ndimage.gaussian_filter(data, sigma=0.5)
        smooth2 = ndimage.gaussian_filter(data, sigma=2.0)
        
        # Combine scales
        enhanced = 0.5 * smooth1 + 0.3 * smooth2 + 0.2 * data
        
        # Apply organic gamma curve
        enhanced = np.power(enhanced, 0.85)
        
        return enhanced
    
    @staticmethod
    def _crystalline_theme(data, settings):
        """Sharp, crystalline interpretation"""
        # Edge enhancement
        laplacian = ndimage.laplace(data)
        enhanced = data - 0.2 * laplacian
        
        # Sharpen
        unsharp = data - ndimage.gaussian_filter(data, sigma=1.0)
        enhanced = enhanced + 0.5 * unsharp
        
        # Apply sharp gamma
        enhanced = np.power(np.clip(enhanced, 0, 1), 0.7)
        
        return enhanced
    
    @staticmethod
    def _ethereal_theme(data, settings):
        """Ethereal, dreamy interpretation"""
        # Soft focus effect
        blurred = ndimage.gaussian_filter(data, sigma=1.5)
        enhanced = 0.8 * blurred + 0.2 * data
        
        # Add subtle glow
        glow = ndimage.maximum_filter(enhanced, size=3)
        enhanced = 0.9 * enhanced + 0.1 * glow
        
        # Soft gamma
        enhanced = np.power(enhanced, 1.1)
        
        return enhanced

class LogManager:
    """Manages fractal generation logging and statistics"""
    
    def __init__(self, log_file: str = "fractal_log.json"):
        self.log_file = log_file
        self.current_session: List[LogEntry] = []
        self.session_start_time: Optional[datetime] = None
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("FractalVisualizer")
        logger.setLevel(logging.INFO)
        
        # File handler
        handler = logging.FileHandler("fractal_app.log")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def start_session(self, width: int, height: int, total_pixels: int):
        """Start a new fractal generation session"""
        self.session_start_time = datetime.now()
        self.current_session = []
        self.logger.info(f"Started fractal generation session: {width}x{height} ({total_pixels} pixels)")
    
    def log_progress(self, percentage: float, pixels_processed: int):
        """Log progress milestone"""
        if not self.session_start_time:
            return
        
        current_time = datetime.now()
        elapsed = (current_time - self.session_start_time).total_seconds()
        
        # Estimate remaining time
        estimated_remaining = None
        if percentage > 0:
            estimated_total = elapsed / (percentage / 100)
            estimated_remaining = estimated_total - elapsed
        
        entry = LogEntry(
            timestamp=current_time,
            percentage=percentage,
            pixels_processed=pixels_processed,
            elapsed_time=elapsed,
            estimated_remaining=estimated_remaining
        )
        
        self.current_session.append(entry)
        
        # Log significant milestones
        milestone_percentages = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        if any(abs(percentage - milestone) < 0.5 for milestone in milestone_percentages):
            remaining_str = f"{estimated_remaining:.1f}s remaining" if estimated_remaining else "calculating..."
            self.logger.info(f"Progress: {percentage:.1f}% ({pixels_processed} pixels, {elapsed:.1f}s elapsed, {remaining_str})")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get current session summary"""
        if not self.current_session:
            return {"status": "No active session"}
        
        latest = self.current_session[-1]
        
        return {
            "session_start": self.session_start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "current_progress": f"{latest.percentage:.1f}%",
            "pixels_processed": latest.pixels_processed,
            "elapsed_time": f"{latest.elapsed_time:.1f}s",
            "estimated_remaining": f"{latest.estimated_remaining:.1f}s" if latest.estimated_remaining else "Unknown",
            "average_pixels_per_second": latest.pixels_processed / latest.elapsed_time if latest.elapsed_time > 0 else 0
        }

class EnhancedFractalVisualizer:
    """Modern, minimalist fractal visualizer with advanced rendering"""
    
    # Color scheme
    COLORS = {
        'bg_primary': '#0f0f0f',
        'bg_secondary': '#1a1a1a', 
        'bg_tertiary': '#262626',
        'accent_primary': '#8b5cf6',
        'accent_secondary': '#a78bfa',
        'text_primary': '#ffffff',
        'text_secondary': '#d1d5db',
        'text_muted': '#9ca3af',
        'success': '#10b981',
        'warning': '#f59e0b',
        'error': '#ef4444'
    }
    
    # Preset dimensions
    DIMENSION_PRESETS = [
        ("Tiny", 100, 100),
        ("Small", 256, 256),
        ("HD Ready", 1280, 720),
        ("Full HD", 1920, 1080),
        ("Custom", 0, 0)
    ]
    
    def __init__(self, data_file_path: str):
        self.data_file_path = Path(data_file_path)
        self.settings = FractalSettings()
        self.log_manager = LogManager()
        
        # Core data
        self.fractal_data: Optional[np.ndarray] = None
        self.processed_image: Optional[Image.Image] = None
        self.pixels_read = 0
        self.total_pixels = 0
        self.file_position = 0
        self.last_update_time = 0
        
        # Threading
        self.running = True
        self.file_monitor_thread: Optional[threading.Thread] = None
        
        # UI Components
        self.root: Optional[ctk.CTk] = None
        self.canvas: Optional[tk.Canvas] = None
        self.tk_image: Optional[ImageTk.PhotoImage] = None
        self.placeholder_tk_icon: Optional[ImageTk.PhotoImage] = None

        # Color palettes (1024 values for 0-1023 range)
        self.color_palettes = self._initialize_palettes()
        
        self._setup_ui()
        self._start_file_monitoring()
    
    def _initialize_palettes(self) -> Dict[str, np.ndarray]:
        """Initialize color palettes with 1024 values"""
        palette_names = ["cosmic", "fire", "ocean", "aurora", "nebula", "solar", "ethereal", "mystic"]
        return {name: ColorPalette.generate_palette(name, 1024) for name in palette_names}
    
    def _setup_ui(self):
        """Setup modern, minimalist UI"""
        self.root = ctk.CTk()
        self.root.title("Fractal Visualizer")
        self.root.configure(fg_color=self.COLORS['bg_primary'])
        self.root.geometry("1600x1000")
        self.root.minsize(1200, 800)
        
        # Configure grid weights for responsiveness
        # Reserve a coluna 0 para o sidebar com largura mínima (evita colapso)
        self.root.grid_columnconfigure(0, weight=0, minsize=380)  # Sidebar column (min width)
        self.root.grid_columnconfigure(1, weight=1)               # Main display column (expande)
        self.root.grid_rowconfigure(0, weight=1)

        
        self._create_sidebar()
        self._create_main_display()
        self._create_status_bar()
    
    def _create_sidebar(self):
        """Create control sidebar"""
        sidebar = ctk.CTkScrollableFrame(
            self.root, 
            width=380, 
            corner_radius=0,
            fg_color=self.COLORS['bg_secondary']
        )
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=10)
        
        # Title
        title_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        title_frame.pack(fill="x", pady=(20, 30))
        
        # App icon
        icon_label = ctk.CTkLabel(
            title_frame, 
            text="", 
            image=IconProvider.get_icon("app_logo", (48, 48))
        )
        icon_label.pack()
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="Fractal Visualizer",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.COLORS['text_primary']
        )
        title_label.pack(pady=(10, 0))
        
        # Dimensions Section
        self._create_dimensions_section(sidebar)
        
        # Rendering Section
        self._create_rendering_section(sidebar)
        
        # Enhancement Section
        self._create_enhancement_section(sidebar)
        
        # Actions Section
        self._create_actions_section(sidebar)
    
    def _create_dimensions_section(self, parent):
        """Create dimensions control section"""
        section = self._create_section(parent, "Dimensions", "Set fractal dimensions", "dimensions")
        
        # Preset buttons
        preset_frame = ctk.CTkFrame(section, fg_color=self.COLORS['bg_tertiary'])
        preset_frame.pack(fill="x", pady=(10, 15))
        
        for i, (name, w, h) in enumerate(self.DIMENSION_PRESETS):
            btn = ctk.CTkButton(
                preset_frame,
                text=name if name != "Custom" else f"{name}",
                width=70,
                height=28,
                command=lambda w=w, h=h: self._set_dimensions(w, h),
                fg_color=self.COLORS['bg_primary'] if name != "Custom" else self.COLORS['accent_primary'],
                hover_color=self.COLORS['accent_secondary']
            )
            btn.grid(row=i//2, column=i%2, padx=5, pady=5, sticky="ew")
        
        preset_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Custom dimensions
        custom_frame = ctk.CTkFrame(section, fg_color="transparent")
        custom_frame.pack(fill="x", pady=(10, 0))
        
        dim_input_frame = ctk.CTkFrame(custom_frame, fg_color=self.COLORS['bg_tertiary'])
        dim_input_frame.pack(fill="x", pady=5)
        
        self.width_entry = ctk.CTkEntry(
            dim_input_frame,
            placeholder_text="Width",
            width=80,
            font=ctk.CTkFont(size=12)
        )
        self.width_entry.grid(row=0, column=0, padx=(10, 5), pady=10)
        
        ctk.CTkLabel(dim_input_frame, text="×", font=ctk.CTkFont(size=16)).grid(row=0, column=1, padx=5)
        
        self.height_entry = ctk.CTkEntry(
            dim_input_frame,
            placeholder_text="Height", 
            width=80,
            font=ctk.CTkFont(size=12)
        )
        self.height_entry.grid(row=0, column=2, padx=(5, 10), pady=10)
        
        apply_btn = ctk.CTkButton(
            dim_input_frame,
            text="Apply",
            width=60,
            command=self._apply_custom_dimensions,
            font=ctk.CTkFont(size=12)
        )
        apply_btn.grid(row=0, column=3, padx=(5, 10), pady=10)
    
    def _create_rendering_section(self, parent):
        """Create rendering controls section"""
        section = self._create_section(parent, "Rendering", "Fractal interpretation settings", "rendering")
        
        # Theme selection
        theme_frame = ctk.CTkFrame(section, fg_color=self.COLORS['bg_tertiary'])
        theme_frame.pack(fill="x", pady=(10, 15))
        
        ctk.CTkLabel(
            theme_frame, 
            text="Theme", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        self.theme_var = ctk.StringVar(value=self.settings.theme)
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            variable=self.theme_var,
            values=["classic", "smooth", "dramatic", "organic", "crystalline", "ethereal"],
            command=self._on_theme_change,
            font=ctk.CTkFont(size=12)
        )
        theme_menu.pack(pady=(0, 10), padx=10, fill="x")
        
        # Palette selection  
        ctk.CTkLabel(
            theme_frame,
            text="Color Palette",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        self.palette_var = ctk.StringVar(value=self.settings.palette)
        palette_menu = ctk.CTkOptionMenu(
            theme_frame,
            variable=self.palette_var,
            values=list(self.color_palettes.keys()),
            command=self._on_palette_change,
            font=ctk.CTkFont(size=12)
        )
        palette_menu.pack(pady=(0, 10), padx=10, fill="x")
    
    def _create_enhancement_section(self, parent):
        """Create enhancement controls section"""
        section = self._create_section(parent, "Enhancement", "Visual enhancement controls", "enhancement")
        
        # Enhancement controls
        controls_frame = ctk.CTkFrame(section, fg_color=self.COLORS['bg_tertiary'])
        controls_frame.pack(fill="x", pady=(10, 0))
        
        # Control definitions
        controls = [
            ("Smoothness", "smoothness", 0.5, 5.0, 2.0),
            ("Contrast", "contrast", 0.5, 3.0, 1.2),
            ("Saturation", "saturation", 0.0, 2.0, 1.0),
            ("Exposure", "exposure", 0.1, 3.0, 1.0),
            ("Focus", "focus", 0.1, 3.0, 1.0)
        ]
        
        self.control_vars = {}
        
        for label, attr, min_val, max_val, default in controls:
            # Create control frame
            ctrl_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
            ctrl_frame.pack(fill="x", padx=10, pady=8)
            
            # Label and value
            label_frame = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
            label_frame.pack(fill="x")
            
            ctk.CTkLabel(
                label_frame,
                text=label,
                font=ctk.CTkFont(size=12, weight="bold")
            ).pack(side="left")
            
            # Variable and value label
            var = ctk.DoubleVar(value=getattr(self.settings, attr))
            self.control_vars[attr] = var
            
            value_label = ctk.CTkLabel(
                label_frame,
                text=f"{default:.1f}",
                font=ctk.CTkFont(size=12),
                text_color=self.COLORS['text_muted']
            )
            value_label.pack(side="right")
            
            # Slider
            slider = ctk.CTkSlider(
                ctrl_frame,
                from_=min_val,
                to=max_val,
                variable=var,
                command=lambda val, lbl=value_label, a=attr: self._on_control_change(val, lbl, a)
            )
            slider.pack(fill="x", pady=(5, 0))
    
    def _create_actions_section(self, parent):
        """Create action buttons section"""
        section = self._create_section(parent, "Actions", "File operations and utilities", "actions")
        
        # Progress display
        progress_frame = ctk.CTkFrame(section, fg_color=self.COLORS['bg_tertiary'])
        progress_frame.pack(fill="x", pady=(10, 15))
        
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="Ready",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.pack(pady=(10, 5))
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 10))
        self.progress_bar.set(0)
        
        # Action buttons
        btn_frame = ctk.CTkFrame(section, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))
        
        buttons = [
            ("Open File", self._open_file, "open_file", self.COLORS['accent_primary']),
            ("Save Image", self._save_image, "save_image", self.COLORS['success']),
            ("View Log", self._show_log, "view_log", self.COLORS['warning']),
            ("Refresh", self._refresh_display, "refresh", self.COLORS['bg_primary'])
        ]
        
        for text, command, icon_name, color in buttons:
            btn = ctk.CTkButton(
                btn_frame,
                text=text,
                image=IconProvider.get_icon(icon_name),
                compound="left",
                anchor="w",
                command=command,
                fg_color=color,
                hover_color=self._darken_color(color),
                height=36,
                font=ctk.CTkFont(size=12, weight="bold")
            )
            btn.pack(fill="x", pady=5, padx=10)
    
    def _create_main_display(self):
        """Create main fractal display area"""
        main_frame = ctk.CTkFrame(
            self.root,
            fg_color=self.COLORS['bg_secondary'],
            corner_radius=8
        )
        main_frame.grid(row=0, column=1, sticky="nsew", padx=(2, 10), pady=10)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Canvas for fractal display
        self.canvas = tk.Canvas(
            main_frame,
            bg=self.COLORS['bg_primary'],
            highlightthickness=0,
            bd=0
        )
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self.canvas.bind('<Configure>', self._on_canvas_resize)
        
        # Initial placeholder
        self.root.after_idle(self._show_placeholder)
    
    def _create_status_bar(self):
        """Create bottom status bar"""
        status_frame = ctk.CTkFrame(
            self.root,
            height=40,
            fg_color=self.COLORS['bg_secondary'],
            corner_radius=0
        )
        status_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        status_frame.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text=f"Ready • File: {self.data_file_path.name}",
            font=ctk.CTkFont(size=11),
            text_color=self.COLORS['text_muted']
        )
        self.status_label.pack(side="left", padx=15, pady=10)
        
        # File info on the right
        self.file_info_label = ctk.CTkLabel(
            status_frame,
            text="0 x 0 • 0 pixels",
            font=ctk.CTkFont(size=11),
            text_color=self.COLORS['text_muted']
        )
        self.file_info_label.pack(side="right", padx=15, pady=10)
    
    def _create_section(self, parent, title: str, description: str, icon_name: str) -> ctk.CTkFrame:
        """Create a UI section with title, description, and an icon"""
        section_frame = ctk.CTkFrame(parent, fg_color="transparent")
        section_frame.pack(fill="x", pady=(0, 20), padx=10)
        
        # Header
        header_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))
        
        icon_label = ctk.CTkLabel(
            header_frame,
            text="",
            image=IconProvider.get_icon(icon_name),
        )
        icon_label.pack(side="left", padx=(0, 8), pady=4)
        
        title_desc_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_desc_frame.pack(side="left", fill="x", anchor="w")

        title_label = ctk.CTkLabel(
            title_desc_frame,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.COLORS['text_primary']
        )
        title_label.pack(anchor="w")
        
        desc_label = ctk.CTkLabel(
            title_desc_frame,
            text=description,
            font=ctk.CTkFont(size=11),
            text_color=self.COLORS['text_muted']
        )
        desc_label.pack(anchor="w", pady=(2, 0))
        
        return section_frame
    
    def _darken_color(self, color: str) -> str:
        """Darken a hex color for hover effects"""
        # Simple darkening by reducing each RGB component
        if color.startswith('#'):
            try:
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
                
                # Darken by 20%
                r = max(0, int(r * 0.8))
                g = max(0, int(g * 0.8))
                b = max(0, int(b * 0.8))
                
                return f"#{r:02x}{g:02x}{b:02x}"
            except:
                pass
        return color
    
    def _show_placeholder(self):
        """Show placeholder when no fractal is loaded"""
        self.canvas.delete("all")
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            center_x = canvas_width // 2
            center_y = canvas_height // 2
            
            ctk_icon = IconProvider.get_icon("app_logo", size=(64, 64))
            if ctk_icon:
                pil_image = ctk_icon._light_image 
                self.placeholder_tk_icon = ImageTk.PhotoImage(pil_image)
                self.canvas.create_image(center_x, center_y - 40, image=self.placeholder_tk_icon)

            self.canvas.create_text(
                center_x, center_y + 40,
                text="No fractal loaded",
                font=("Arial", 16, "bold"),
                fill=self.COLORS['text_secondary']
            )
            
            self.canvas.create_text(
                center_x, center_y + 65,
                text="Open a data file to begin visualization",
                font=("Arial", 12),
                fill=self.COLORS['text_muted']
            )
    
    def _start_file_monitoring(self):
        """Start monitoring the data file for changes"""
        if self.file_monitor_thread is None or not self.file_monitor_thread.is_alive():
            self.file_monitor_thread = threading.Thread(target=self._monitor_file, daemon=True)
            self.file_monitor_thread.start()
    
    def _monitor_file(self):
        """Monitor data file for new pixel data"""
        while self.running:
            try:
                if self.data_file_path.exists():
                    self._read_file_data()
                time.sleep(0.05)
            except Exception as e:
                self.log_manager.logger.error(f"File monitoring error: {e}")
                time.sleep(0.5)
    
    def _read_file_data(self):
        """Lê novas linhas de dados do arquivo."""
        try:
            with open(self.data_file_path, 'r') as f:
                f.seek(self.file_position)
                
                new_lines = f.readlines()
                
                if new_lines:
                    new_values = []
                    for line in new_lines:
                        line = line.strip()
                        if line and line.isdigit():
                            value = int(line)
                            if 0 <= value <= 1023:
                                new_values.append(value / 1023.0)
                    
                    if new_values:
                        self._process_new_pixels(new_values)
                    
                    self.file_position = f.tell()
                    
        except Exception as e:
            self.log_manager.logger.error(f"Erro ao ler os dados do arquivo: {e}")
    
    def _process_new_pixels(self, values: List[float]):
        """Process new pixel values"""
        if self.fractal_data is None:
            self._initialize_fractal_data()
        
        for value in values:
            if self.pixels_read >= self.total_pixels:
                break
            
            y, x = divmod(self.pixels_read, self.settings.width)
            if y < self.settings.height:
                self.fractal_data[y, x] = value
                self.pixels_read += 1
        
        current_time = time.time()
        if current_time - self.last_update_time > 0.1:
            self.root.after_idle(self._update_ui)
            self.last_update_time = current_time
    
    def _initialize_fractal_data(self):
        """Initialize fractal data array"""
        self.total_pixels = self.settings.width * self.settings.height
        self.fractal_data = np.zeros((self.settings.height, self.settings.width), dtype=np.float32)
        self.pixels_read = 0
        
        self.log_manager.start_session(self.settings.width, self.settings.height, self.total_pixels)
        self._update_status("Processing fractal data...")
    
    def _update_ui(self):
        """Update UI elements"""
        if self.total_pixels > 0:
            progress = self.pixels_read / self.total_pixels
            self.progress_bar.set(progress)
            
            percentage = progress * 100
            self.progress_label.configure(text=f"{percentage:.1f}% ({self.pixels_read:,} pixels)")
            
            self.log_manager.log_progress(percentage, self.pixels_read)
            
            self.file_info_label.configure(
                text=f"{self.settings.width} × {self.settings.height} • {self.pixels_read:,}/{self.total_pixels:,} pixels"
            )
            
            if self.pixels_read >= self.total_pixels:
                self._update_status("Fractal generation complete")
            else:
                rows_processed = self.pixels_read // self.settings.width
                self._update_status(f"Processing row {rows_processed + 1}/{self.settings.height}")
        
        self._render_fractal()
    
    def _render_fractal(self):
        """Render the current fractal with all enhancements"""
        if self.fractal_data is None or self.pixels_read == 0:
            return
        
        try:
            visible_rows = min(self.settings.height, (self.pixels_read + self.settings.width - 1) // self.settings.width)
            if visible_rows == 0:
                return
            
            data = self.fractal_data[:visible_rows, :].copy()
            enhanced_data = FractalTheme.apply_theme(data, self.settings.theme, self.settings)
            enhanced_data = self._apply_enhancements(enhanced_data)
            indices = np.clip(enhanced_data * 1023, 0, 1023).astype(int)
            
            current_palette = self.color_palettes[self.settings.palette]
            rgb_data = current_palette[indices]
            
            self.processed_image = Image.fromarray(rgb_data, 'RGB')
            self.processed_image = self._apply_image_enhancements(self.processed_image)
            self._update_canvas_display()
            
        except Exception as e:
            self.log_manager.logger.error(f"Error rendering fractal: {e}")
    
    def _apply_enhancements(self, data: np.ndarray) -> np.ndarray:
        """Apply enhancement settings to fractal data"""
        enhanced = data.copy()
        
        try:
            if self.settings.smoothness > 1.0:
                sigma = (self.settings.smoothness - 1.0) * 0.5
                enhanced = ndimage.gaussian_filter(enhanced, sigma=sigma)
            
            if self.settings.contrast != 1.0:
                enhanced = 0.5 + (enhanced - 0.5) * self.settings.contrast
            
            if self.settings.exposure != 1.0:
                enhanced = enhanced * self.settings.exposure
            
            if self.settings.focus > 1.0:
                blurred = ndimage.gaussian_filter(enhanced, sigma=1.0)
                unsharp_strength = (self.settings.focus - 1.0) * 0.5
                enhanced = enhanced + unsharp_strength * (enhanced - blurred)
            
            enhanced = np.clip(enhanced, 0, 1)
            return enhanced
            
        except Exception as e:
            self.log_manager.logger.error(f"Error applying enhancements: {e}")
            return data
    
    def _apply_image_enhancements(self, image: Image.Image) -> Image.Image:
        """Apply PIL-based image enhancements"""
        try:
            if self.settings.saturation != 1.0:
                enhancer = ImageEnhance.Color(image)
                image = enhancer.enhance(self.settings.saturation)
            
            if self.settings.focus > 1.0:
                enhancer = ImageEnhance.Sharpness(image)
                sharpness_factor = 1.0 + (self.settings.focus - 1.0) * 0.5
                image = enhancer.enhance(sharpness_factor)
            
            return image
            
        except Exception as e:
            self.log_manager.logger.error(f"Error applying image enhancements: {e}")
            return image
    
    def _update_canvas_display(self):
        """Update the canvas with the current fractal image"""
        if not self.processed_image:
            return
        
        try:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                return
            
            img_width, img_height = self.processed_image.size
            scale_x = (canvas_width - 20) / img_width
            scale_y = (canvas_height - 20) / img_height
            scale = min(scale_x, scale_y, 1.0)
            
            if scale < 1.0:
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                
                display_image = self.processed_image.resize(
                    (new_width, new_height), 
                    Image.Resampling.LANCZOS
                )
            else:
                display_image = self.processed_image
            
            self.tk_image = ImageTk.PhotoImage(display_image)
            
            self.canvas.delete("all")
            self.canvas.create_image(
                canvas_width // 2,
                canvas_height // 2,
                image=self.tk_image,
                anchor="center"
            )
            
        except Exception as e:
            self.log_manager.logger.error(f"Error updating canvas display: {e}")
    
    def _update_status(self, message: str):
        """Update status bar message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_label.configure(text=f"{message} • {timestamp}")
    
    def _set_dimensions(self, width: int, height: int):
        """Set fractal dimensions from preset"""
        if width == 0 and height == 0:
            self.width_entry.focus()
            return
        
        self.settings.width = width
        self.settings.height = height
        self._reset_fractal_data()
        self._update_status(f"Dimensions set to {width}×{height}")
    
    def _apply_custom_dimensions(self):
        """Apply custom dimensions from entry fields"""
        try:
            width = int(self.width_entry.get())
            height = int(self.height_entry.get())
            
            if 1 <= width <= 8192 and 1 <= height <= 8192:
                self.settings.width = width
                self.settings.height = height
                self._reset_fractal_data()
                self._update_status(f"Custom dimensions set to {width}×{height}")
            else:
                messagebox.showerror("Invalid Dimensions", "Width and height must be between 1 and 8192")
                
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric dimensions")
    
    def _reset_fractal_data(self):
        """Reset fractal data for new dimensions"""
        self.fractal_data = None
        self.processed_image = None
        self.pixels_read = 0
        self.total_pixels = 0
        self.file_position = 0
        self.progress_bar.set(0)
        self.progress_label.configure(text="Ready")
        self.root.after_idle(self._show_placeholder)
    
    def _on_theme_change(self, theme: str):
        """Handle theme change"""
        self.settings.theme = theme
        self._render_fractal()
        self._update_status(f"Theme changed to {theme}")
    
    def _on_palette_change(self, palette: str):
        """Handle palette change"""
        self.settings.palette = palette
        self._render_fractal()
        self._update_status(f"Palette changed to {palette}")
    
    def _on_control_change(self, value: float, label: ctk.CTkLabel, attribute: str):
        """Handle enhancement control changes"""
        setattr(self.settings, attribute, value)
        label.configure(text=f"{value:.1f}")
        self._render_fractal()
    
    def _on_canvas_resize(self, event):
        """Handle canvas resize event"""
        if hasattr(self, 'processed_image') and self.processed_image:
            self.root.after_idle(self._update_canvas_display)
        else:
            self.root.after_idle(self._show_placeholder)
    
    def _open_file(self):
        """Open a new data file"""
        file_path = filedialog.askopenfilename(
            title="Open Fractal Data File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            self.data_file_path = Path(file_path)
            self._reset_fractal_data()
            self._update_status(f"Opened file: {self.data_file_path.name}")
            self.status_label.configure(text=f"Ready • File: {self.data_file_path.name}")
    
    def _save_image(self):
        """Save the current fractal image with simplified logic"""
        try:
            # Check if we have fractal data
            if self.fractal_data is None or self.pixels_read == 0:
                messagebox.showwarning("No Image", "No fractal data available to save")
                return
            
            # Force render the current fractal state
            if self.fractal_data is not None:
                # Get visible rows (even if incomplete)
                visible_rows = min(self.settings.height, (self.pixels_read + self.settings.width - 1) // self.settings.width)
                if visible_rows == 0:
                    messagebox.showwarning("No Image", "No pixel data to save")
                    return
                
                # Create image from current data
                data = self.fractal_data[:visible_rows, :].copy()
                enhanced_data = FractalTheme.apply_theme(data, self.settings.theme, self.settings)
                enhanced_data = self._apply_enhancements(enhanced_data)
                indices = np.clip(enhanced_data * 1023, 0, 1023).astype(int)
                
                current_palette = self.color_palettes[self.settings.palette]
                rgb_data = current_palette[indices]
                
                # Create PIL image
                save_image = Image.fromarray(rgb_data, 'RGB')
                save_image = self._apply_image_enhancements(save_image)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fractal_{self.settings.width}x{self.settings.height}_{self.settings.palette}_{timestamp}.png"
            
            # Save in same directory as input file
            save_path = self.data_file_path.parent / filename
            
            # Save with maximum quality
            save_image.save(str(save_path), "PNG", optimize=False, compress_level=0)
            
            # Update UI
            self._update_status(f"Image saved: {filename}")
            messagebox.showinfo("Success", f"Image saved successfully!\n{filename}\n\nLocation: {save_path}")
            
            # Log the save operation
            self.log_manager.logger.info(f"Image saved: {save_path}")
            
        except Exception as e:
            error_msg = f"Failed to save image: {str(e)}"
            self.log_manager.logger.error(error_msg)
            messagebox.showerror("Save Error", error_msg)
            print(f"Save error: {e}")  # Also print to console for debugging
    
    def _show_log(self):
        """Show the fractal generation log"""
        log_window = ctk.CTkToplevel(self.root)
        log_window.title("Fractal Generation Log")
        log_window.geometry("700x500")
        log_window.configure(fg_color=self.COLORS['bg_primary'])
        
        log_window.transient(self.root)
        log_window.grab_set()
        
        title_frame = ctk.CTkFrame(log_window, fg_color="transparent")
        title_frame.pack(pady=(20, 10))

        title_icon = ctk.CTkLabel(
            title_frame,
            text="",
            image=IconProvider.get_icon("view_log")
        )
        title_icon.pack(side="left", padx=(0, 10))

        title_label = ctk.CTkLabel(
            title_frame,
            text="Fractal Generation Log",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(side="left")
        
        summary_frame = ctk.CTkFrame(log_window, fg_color=self.COLORS['bg_secondary'])
        summary_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        summary_data = self.log_manager.get_session_summary()
        
        if "status" in summary_data:
            summary_text = summary_data["status"]
        else:
            summary_text = f"""Current Session Summary:
Started: {summary_data.get('session_start', 'N/A')}
Progress: {summary_data.get('current_progress', 'N/A')}
Pixels Processed: {summary_data.get('pixels_processed', 0):,}
Elapsed Time: {summary_data.get('elapsed_time', 'N/A')}
Estimated Remaining: {summary_data.get('estimated_remaining', 'N/A')}
Processing Speed: {summary_data.get('average_pixels_per_second', 0):.1f} pixels/sec"""
        
        summary_label = ctk.CTkLabel(
            summary_frame,
            text=summary_text,
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        summary_label.pack(padx=20, pady=15)
        
        log_frame = ctk.CTkFrame(log_window, fg_color=self.COLORS['bg_secondary'])
        log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        log_text = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(size=11, family="Consolas"),
            wrap="word"
        )
        log_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        if self.log_manager.current_session:
            log_content = "Session Log Entries:\n" + "="*50 + "\n\n"
            
            for entry in self.log_manager.current_session[-20:]:
                timestamp = entry.timestamp.strftime("%H:%M:%S.%f")[:-3]
                remaining = f" (ETA: {entry.estimated_remaining:.1f}s)" if entry.estimated_remaining else ""
                log_content += f"[{timestamp}] {entry.percentage:6.1f}% | {entry.pixels_processed:8,} pixels | {entry.elapsed_time:6.1f}s{remaining}\n"
        else:
            log_content = "No active session data available."
        
        log_text.insert("1.0", log_content)
        log_text.configure(state="disabled")
        
        close_btn = ctk.CTkButton(
            log_window,
            text="Close",
            command=log_window.destroy,
            width=100
        )
        close_btn.pack(pady=(0, 20))
    
    def _refresh_display(self):
        """Refresh the fractal display"""
        self._render_fractal()
        self._update_status("Display refreshed")
    
    def run(self):
        """Start the application"""
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        self._update_status("Application started")
        self.root.mainloop()
    
    def _on_closing(self):
        """Handle application closing"""
        self.running = False
        if self.file_monitor_thread:
            self.file_monitor_thread.join()
        self.log_manager.logger.info("Application closing")
        self.root.quit()
        self.root.destroy()

def main():
    """Ponto de entrada principal da aplicação."""
    parser = argparse.ArgumentParser(
        description="Enhanced Fractal Visualizer - Aplicação moderna de renderização de fractais.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  
  # Inicia a interface para depois abrir um arquivo manualmente
  python fancyFractal.py

  # Inicia e carrega imediatamente o arquivo 'meus_dados.txt'
  python fancyFractal.py meus_dados.txt
"""
    )
    
    parser.add_argument(
        'data_file',
        nargs='?',
        default=None,
        help='(Opcional) Caminho para o arquivo de dados do fractal a ser carregado no início.'
    )
    
    args = parser.parse_args()
    
    initial_file_path = "fractal_data.txt"

    if args.data_file:
        if not os.path.exists(args.data_file):
            print(f"Erro: O arquivo de entrada '{args.data_file}' não foi encontrado.")
            sys.exit(1)
        initial_file_path = args.data_file
    
    try:
        visualizer = EnhancedFractalVisualizer(initial_file_path)
        visualizer.run()
        
    except KeyboardInterrupt:
        print("\nAplicação interrompida pelo usuário.")
        sys.exit(0)
    except Exception as e:
        logging.basicConfig(filename="fractal_fatal_error.log", level=logging.ERROR)
        logging.exception(f"Erro fatal durante a inicialização da aplicação: {e}")
        messagebox.showerror(
            "Erro Fatal",
            f"Ocorreu um erro crítico e a aplicação precisa ser fechada.\n\n"
            f"Erro: {e}\n\n"
            "Verifique o arquivo 'fractal_fatal_error.log' para mais detalhes."
        )
        sys.exit(1)

if __name__ == "__main__":
    main()