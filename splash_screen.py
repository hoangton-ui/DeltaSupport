import os
import customtkinter as ctk
from PIL import Image
from utils.theme import *
from utils.resource_manager import resource_manager


class SplashScreen(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("Delta Assistant")
        self.geometry("440x320")
        self.resizable(False, False)
        self.configure(fg_color=BG_PANEL)
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        self.logo_image = None

        self.update_idletasks()
        width = 440
        height = 320
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        container = ctk.CTkFrame(
            self,
            fg_color=BG_PANEL,
            corner_radius=24,
            border_width=1,
            border_color=BORDER
        )
        container.pack(fill="both", expand=True, padx=2, pady=2)

        self.logo_image = resource_manager.load_icon("logo.png", (150, 150))
        if self.logo_image:
            logo_label = ctk.CTkLabel(container, image=self.logo_image, text="")
            logo_label.pack(pady=(26, 10))
        else:
                fallback = ctk.CTkLabel(
                    container,
                    text="DA",
                    font=ctk.CTkFont(size=42, weight="bold"),
                    text_color=TEXT_MUTED
                )
                fallback.pack(pady=(35, 15))

        title = ctk.CTkLabel(
            container,
            text="Delta Assistant",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=TEXT_MUTED
        )
        title.pack()

        subtitle = ctk.CTkLabel(
            container,
            text="Loading...",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_SUB
        )
        subtitle.pack(pady=(8, 16))

        self.progress = ctk.CTkProgressBar(
            container,
            width=220,
            height=10,
            corner_radius=10,
            fg_color=BTN_IDLE,
            progress_color=BTN_ACTIVE
        )
        self.progress.pack()
        self.progress.start()