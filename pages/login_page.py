import os
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image

from services.auth_service import login_api
from pages.signup_page import SignUpPage
from utils.theme import *
from utils.resource_manager import resource_manager


class LoginPage(ctk.CTkFrame):
    def __init__(self, parent, on_login_success):
        super().__init__(parent, fg_color=BG_MAIN)
        self.parent = parent
        self.on_login_success = on_login_success

        self.logo_image = None
        self.user_icon = None
        self.lock_icon = None

        self.build_ui()

    def build_ui(self):
        self.user_icon = resource_manager.load_icon("user.png", (20, 20))
        self.lock_icon = resource_manager.load_icon("lock.png", (20, 20))

        container = ctk.CTkFrame(
            self,
            width=450,
            height=650,
            corner_radius=26,
            fg_color=BG_PANEL,
            border_width=1,
            border_color=BORDER,
        )
        container.place(relx=0.5, rely=0.5, anchor="center")
        container.pack_propagate(False)

        self.logo_image = resource_manager.load_icon("logo.png", (160, 160))

        if self.logo_image:
            logo_label = ctk.CTkLabel(container, image=self.logo_image, text="")
            logo_label.pack(pady=(18, 6))
        else:
                fallback_logo = ctk.CTkLabel(
                    container,
                    text="DA",
                    font=ctk.CTkFont(size=34, weight="bold"),
                    text_color="#f4e7c1",
                )
                fallback_logo.pack(pady=(24, 12))

        title = ctk.CTkLabel(
            container,
            text="Delta Assistant",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color=TEXT_MUTED,
        )
        title.pack(pady=(2, 12))

        # ===== USERNAME =====
        user_frame = ctk.CTkFrame(
            container, width=300, height=48, corner_radius=14, fg_color=INPUT_BG_ALT
        )
        user_frame.pack(pady=10)
        user_frame.pack_propagate(False)

        ctk.CTkLabel(user_frame, image=self.user_icon, text="").pack(
            side="left", padx=(12, 4)
        )

        ctk.CTkLabel(
            user_frame, text="|", text_color="#8f6b32", font=("Segoe UI", 16, "bold")
        ).pack(side="left")

        self.username_entry = ctk.CTkEntry(
            user_frame,
            border_width=0,
            fg_color="transparent",
            text_color=INPUT_TEXT_ALT,
            placeholder_text="Username",
            placeholder_text_color=INPUT_PLACEHOLDER_ALT,
        )
        self.username_entry.pack(side="left", fill="both", expand=True, padx=8)

        # ===== PASSWORD =====
        pass_frame = ctk.CTkFrame(
            container, width=300, height=48, corner_radius=14, fg_color=INPUT_BG_ALT
        )
        pass_frame.pack(pady=10)
        pass_frame.pack_propagate(False)

        ctk.CTkLabel(pass_frame, image=self.lock_icon, text="").pack(
            side="left", padx=(12, 4)
        )

        ctk.CTkLabel(
            pass_frame, text="|", text_color="#8f6b32", font=("Segoe UI", 16, "bold")
        ).pack(side="left")

        self.password_entry = ctk.CTkEntry(
            pass_frame,
            border_width=0,
            fg_color="transparent",
            text_color=INPUT_TEXT_ALT,
            placeholder_text="Password",
            placeholder_text_color=INPUT_PLACEHOLDER_ALT,
            show="*",
        )
        self.password_entry.pack(side="left", fill="both", expand=True, padx=8)

        # ===== LOGIN BUTTON =====
        login_btn = ctk.CTkButton(
            container,
            text="Login",
            width=300,
            height=46,
            corner_radius=14,
            fg_color=BTN_PRIMARY,
            hover_color=BTN_PRIMARY_HOVER,
            text_color=CONTENT_INNER,
            font=("Segoe UI", 15, "bold"),
            command=self.handle_login,
        )
        login_btn.pack(pady=(22, 12))

        # ===== SIGN UP =====
        signup_btn = ctk.CTkButton(
            container,
            text="Sign Up",
            width=300,
            height=46,
            corner_radius=14,
            fg_color=BTN_IDLE,
            hover_color=BTN_IDLE_HOVER,
            text_color=TEXT_MUTED,
            font=("Segoe UI", 15, "bold"),
            command=self.open_signup,
        )
        signup_btn.pack()

        # ===== VERSION =====
        ctk.CTkLabel(
            self,
            text="DA Application - Ver 0.0.1 - By Hoang T",
            font=ctk.CTkFont(size=11),
            text_color="#bfa36a",
        ).place(relx=0.985, rely=0.975, anchor="se")

        self.username_entry.bind("<Return>", lambda event: self.handle_login())
        self.password_entry.bind("<Return>", lambda event: self.handle_login())

    def handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showwarning(
                "Thiếu thông tin", "Vui lòng nhập username và password."
            )
            return

        result = login_api(username, password)

        if result.get("success"):
            user = {
                "username": result.get("username"),
                "role": result.get("role"),
            }
            print("USER LOGIN:", user)
            self.on_login_success(user)
        else:
            messagebox.showerror(
                "Login Failed", result.get("message", "Sai tài khoản hoặc mật khẩu.")
            )

    def open_signup(self):
        signup_window = SignUpPage(self)
        signup_window.focus()
