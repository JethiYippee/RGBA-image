import tkinter as tk
from tkinter import filedialog, Menu
from PIL import Image, ImageTk, ImageDraw
import pyperclip

class RGBAViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("RGBA Viewer")

        # Enable Dark Mode
        self.dark_mode = True
        bg_color = "#222222" if self.dark_mode else "#FFFFFF"

        self.root.configure(bg=bg_color)
        self.canvas = tk.Canvas(root, bg=bg_color)
        self.canvas.pack(fill="both", expand=True)

        # Create Menu Bar
        menu_bar = Menu(root)
        file_menu = Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_file)
        menu_bar.add_cascade(label="File", menu=file_menu)

        converter_menu = Menu(menu_bar, tearoff=0)
        converter_menu.add_command(label="PNG to RGBA", command=lambda: self.convert_to_rgba("png"))
        converter_menu.add_command(label="JPG to RGBA", command=lambda: self.convert_to_rgba("jpg"))
        converter_menu.add_command(label="WebP to RGBA", command=lambda: self.convert_to_rgba("webp"))
        converter_menu.add_separator()
        converter_menu.add_command(label="RGBA to PNG", command=lambda: self.convert_from_rgba("png"))
        converter_menu.add_command(label="RGBA to JPG", command=lambda: self.convert_from_rgba("jpg"))
        converter_menu.add_command(label="RGBA to WebP", command=lambda: self.convert_from_rgba("webp"))
        menu_bar.add_cascade(label="Converter", menu=converter_menu)

        root.config(menu=menu_bar)

        self.file_path = None
        self.scale = 1
        self.offset_x = 0
        self.offset_y = 0
        self.dragging = False

        # Fixed Buttons (Zoom)
        btn_frame = tk.Frame(root, bg=bg_color)
        btn_frame.pack(fill="x")
        tk.Button(btn_frame, text="Zoom In", command=self.zoom_in).pack(side="left")
        tk.Button(btn_frame, text="Zoom Out", command=self.zoom_out).pack(side="left")

        # Scroll to Zoom
        self.canvas.bind("<MouseWheel>", self.scroll_zoom)

        # Dragging Support
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag_image)

        # Right-Click Context Menu for Color Picker
        self.menu = Menu(root, tearoff=0)
        self.menu.add_command(label="Color Picker", command=self.pick_color)
        self.canvas.bind("<Button-3>", self.show_menu)

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("RGBA Images", "*.RGBA")])
        if file_path:
            self.file_path = file_path
            self.img = self.load_rgba(self.file_path)
            self.scale = 1
            self.offset_x = 0
            self.offset_y = 0
            self.display_image()

    def convert_to_rgba(self, file_type):
        file_path = filedialog.askopenfilename(filetypes=[(f"{file_type.upper()} Images", f"*.{file_type}")])
        if not file_path:
            return

        suggested_name = filedialog.asksaveasfilename(defaultextension=".RGBA", filetypes=[("RGBA Format", "*.RGBA")])
        if not suggested_name:
            return

        img = Image.open(file_path).convert("RGBA")
        width, height = img.size

        with open(suggested_name, "w") as f:
            for y in range(height):
                row_pixels = [f"#{r:02x}{g:02x}{b:02x}{a:02x}" for r, g, b, a in [img.getpixel((x, y)) for x in range(width)]]
                f.write(" ".join(row_pixels) + "\n")

        self.file_path = suggested_name
        self.img = self.load_rgba(suggested_name)
        self.display_image()

    def convert_from_rgba(self, file_type):
        file_path = filedialog.askopenfilename(filetypes=[("RGBA Images", "*.RGBA")])
        if not file_path:
            return

        suggested_name = filedialog.asksaveasfilename(defaultextension=f".{file_type}", filetypes=[(f"{file_type.upper()} Format", f"*.{file_type}")])
        if not suggested_name:
            return

        img = self.load_rgba(file_path)
        img.save(suggested_name, format=file_type.upper())

    def load_rgba(self, filename):
        with open(filename, "r") as f:
            pixel_lines = [line.strip().split() for line in f.readlines()]

        width = len(pixel_lines[0])
        height = len(pixel_lines)
        img = Image.new("RGBA", (width, height))

        # Create Checkerboard Background
        checkerboard = Image.new("RGBA", (width, height), (200, 200, 200, 255))
        draw = ImageDraw.Draw(checkerboard)
        tile_size = 10
        for y in range(0, height, tile_size):
            for x in range(0, width, tile_size):
                if (x // tile_size + y // tile_size) % 2 == 0:
                    draw.rectangle([x, y, x + tile_size, y + tile_size], fill=(255, 255, 255, 255))

        for y, row in enumerate(pixel_lines):
            for x, pixel in enumerate(row):
                r = int(pixel[1:3], 16)
                g = int(pixel[3:5], 16)
                b = int(pixel[5:7], 16)
                a = int(pixel[7:9], 16)
                img.putpixel((x, y), (r, g, b, a))

        return Image.alpha_composite(checkerboard, img)

    def display_image(self):
        zoomed_img = self.img.resize(
            (self.img.width * self.scale, self.img.height * self.scale),
            Image.NEAREST  # Keeps pixels sharp
        )
        self.tk_img = ImageTk.PhotoImage(zoomed_img)
        self.canvas.delete("all")
        self.canvas.create_image(self.offset_x, self.offset_y, anchor="center", image=self.tk_img)

    def zoom_in(self):
        self.scale += 1
        self.display_image()

    def zoom_out(self):
        if self.scale > 1:
            self.scale -= 1
            self.display_image()

    def scroll_zoom(self, event):
        if event.delta > 0:
            self.zoom_in()
        elif event.delta < 0:
            self.zoom_out()

    def start_drag(self, event):
        self.dragging = True
        self.start_x, self.start_y = event.x, event.y

    def drag_image(self, event):
        if self.dragging:
            dx = event.x - self.start_x
            dy = event.y - self.start_y
            self.offset_x += dx
            self.offset_y += dy
            self.start_x, self.start_y = event.x, event.y
            self.display_image()

    def show_menu(self, event):
        self.menu.post(event.x_root, event.y_root)
        self.color_x, self.color_y = event.x, event.y

    def pick_color(self):
        if hasattr(self, "color_x") and hasattr(self, "color_y"):
            pixel = self.img.getpixel((self.color_x // self.scale, self.color_y // self.scale))
            hex_code = f"#{pixel[0]:02x}{pixel[1]:02x}{pixel[2]:02x}{pixel[3]:02x}"
            pyperclip.copy(hex_code)
            tk.messagebox.showinfo("Color Picker", f"HEX Code copied to clipboard: {hex_code}")

# Start Viewer
root = tk.Tk()
RGBAViewer(root)
root.mainloop()
