import os
import ctypes
import customtkinter as ctk
from PIL import Image, ImageTk

from pages.login_page import LoginPage
from main_app import MainAppPage
from splash_screen import SplashScreen

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

GWL_STYLE = -16
WS_MAXIMIZEBOX = 0x00010000
WS_THICKFRAME = 0x00040000
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
SWP_FRAMECHANGED = 0x0020


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.current_user = None
        self.display_mode = "windowed"
        self._native_style_applied = False

        self.title("Delta Assistant")
        self.resizable(True, True)
        self.bind("<Configure>", self._on_window_configure)

        self.set_app_icon()
        self.apply_display_mode("windowed", force=True)
        self.after(150, self.apply_native_window_mode)

        self.withdraw()
        self.after(100, self.show_splash)

    def get_base_path(self):
        return os.path.dirname(os.path.abspath(__file__))

    def set_app_icon(self):
        base_path = self.get_base_path()
        icon_path = os.path.join(base_path, "data", "app.ico")

        if not os.path.exists(icon_path):
            print(f"Không tìm thấy icon: {icon_path}")
            return

        try:
            icon_image = Image.open(icon_path)
            icon_photo = ImageTk.PhotoImage(icon_image)
            self.iconphoto(True, icon_photo)
            self._icon_photo = icon_photo
        except Exception as e:
            print("Không load được icon:", e)

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    def apply_native_window_mode(self):
        if self._native_style_applied:
            return

        try:
            hwnd = self.winfo_id()
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
            style = (style | WS_MAXIMIZEBOX) & ~WS_THICKFRAME
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style)
            ctypes.windll.user32.SetWindowPos(
                hwnd,
                0,
                0,
                0,
                0,
                0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED,
            )
            self._native_style_applied = True
        except Exception:
            pass

    def get_windowed_geometry(self):
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        width = min(max(1240, int(screen_w * 0.7)), max(1240, screen_w - 120))
        height = min(max(760, int(screen_h * 0.72)), max(760, screen_h - 110))
        x = max(20, (screen_w - width) // 2)
        y = max(20, (screen_h - height) // 2)
        return width, height, x, y

    def apply_display_mode(self, mode, force=False):
        mode = "maximized" if str(mode).strip().lower() in ["maximized", "zoomed"] else "windowed"
        if not force and self.display_mode == mode:
            return

        self.display_mode = mode

        if mode == "maximized":
            self.state("zoomed")
        else:
            self.state("normal")
            width, height, x, y = self.get_windowed_geometry()
            self.geometry(f"{width}x{height}+{x}+{y}")

        self.after(30, self.apply_native_window_mode)

    def toggle_display_mode(self):
        next_mode = "windowed" if self.display_mode == "maximized" else "maximized"
        self.apply_display_mode(next_mode)

    def _on_window_configure(self, event=None):
        try:
            current_state = str(self.state()).lower()
        except Exception:
            current_state = "normal"

        if current_state == "zoomed":
            self.display_mode = "maximized"
        else:
            self.display_mode = "windowed"

    def show_splash(self):
        self.splash = SplashScreen(self)
        self.splash.after(2200, self.start_main_window)

    def start_main_window(self):
        if hasattr(self, "splash") and self.splash.winfo_exists():
            self.splash.destroy()

        self.deiconify()
        self.after(50, self.apply_native_window_mode)
        self.show_login()

    def show_login(self):
        self.clear_window()
        login_page = LoginPage(self, self.handle_login_success)
        login_page.pack(fill="both", expand=True)

    def handle_login_success(self, user):
        self.current_user = user
        self.show_main_app()

    def handle_logout(self):
        self.current_user = None
        self.show_login()

    def show_main_app(self):
        self.clear_window()
        main_page = MainAppPage(self, self.handle_logout, self.current_user)
        main_page.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = App()
    app.mainloop()
