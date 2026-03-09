import customtkinter as ctk
from tkinter import filedialog
import threading
from pathlib import Path
import ctypes
import json
import tkinter as tk
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw
import translte

class main(): 
    global data
    file = Path(__file__).parent
    json_data = file / "config.json"
    with open(rf"{json_data}","r", encoding="utf-8") as datah:
        data = json.load(datah)

    hover_color="#25883E"
    fg_color="#0D852B"
    font = ("Arial", 12, "bold")

    def __init__(self):
        self.file1 = Path(__file__).parent
        self.status =0 
        self.value= 0
        self.clear_files()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        self.frame = ctk.CTk()
        self.frame.geometry("680x350")
        self.frame.title("مترجمي")
        self.frame.resizable(False,False)

        # --- إصلاح الأيقونات (آمن) ---
        try:
            icon_path = self.file1 / "lib" / "photo" / "pdf.png"
            if icon_path.exists():
                icon = tk.PhotoImage(file=str(icon_path))
                self.frame.iconphoto(True, icon)
                self.frame.iconbitmap(rf"{self.file1}\lib\photo\pdf.ico")
        except: pass

        buttun_file = ctk.CTkButton(self.frame,text="اختر الملف" ,command=self.select_file, font=self.font, fg_color=data["fg_color"], hover_color=data["hover_color"])
        buttun_file.place(x=180,y=10)
        
        self.label_file = ctk.CTkLabel(self.frame,text="",font=self.font)
        self.label_file.place(x=180,y=40)
        
        self.label_Page = ctk.CTkLabel(self.frame,text="",font=self.font)
        self.label_Page.place(x=50,y=300)
        
        self.bar_f= ctk.CTkFrame(self.frame,corner_radius=10)
        self.bar_f.place(x=150,y= 300)
        self.bar= ctk.CTkProgressBar(self.bar_f,width=250)
        self.lab= ctk.CTkLabel(self.bar_f,width=20,text=f" % {int(data['bar']*100)} :التقدم",font=self.font)
        self.lab.pack()
        self.bar.pack()
        self.bar.set(0.00)

        # --- المعاينة (آمنة) ---
        try:
            photo = ctk.CTkImage(Image.open(rf"{self.file1}\lib\photo\pdf.png"),size=(150,150))
        except: photo = None

        before = ctk.CTkFrame(self.frame,corner_radius=10)
        before.place(x=300,y= 80)
        ctk.CTkLabel(before,text="قبل",font=self.font).pack() 
        self.before = ctk.CTkLabel(before,image=photo,text="")
        self.before.pack(pady=20)

        after = ctk.CTkFrame(self.frame,corner_radius=10)
        after.place(x=40,y= 80)
        ctk.CTkLabel(after,text="بعد",font=self.font).pack()
        self.after = ctk.CTkLabel(after,image=photo,font=self.font,text="")
        self.after.pack(pady=20)

        # بقية الكود الأصلي كما هو...
        frame_but= ctk.CTkFrame(self.frame,corner_radius=10)
        frame_but.place(x=500,y= 20)
        self.buttun_run = ctk.CTkButton(frame_but,text="تشغيل",command=self.run , font=self.font, fg_color=data["fg_color"], hover_color=data["hover_color"])
        self.buttun_run.pack()

        frame_menu= ctk.CTkFrame(self.frame,corner_radius=10)
        frame_menu.place(x=500,y= 90)
        self.lang = ctk.CTkOptionMenu(frame_menu,values=list(data["lang"].keys()), font=self.font, fg_color=data["fg_color"])
        self.lang.grid(row=1,column=0)
        self.type1 = ctk.CTkOptionMenu(frame_menu,values=list(data["type"].keys()) , font=self.font, fg_color=self.fg_color)
        self.type1.grid(row=3,column=0)
        self.translter = ctk.CTkOptionMenu(frame_menu,values=list(data["translter"].keys()), font=self.font, fg_color=data["fg_color"])
        self.translter.grid(row=5,column=0)

        self.frame.mainloop()

    # (الدوال الأخرى select_file, run, update_bar تبقى كما هي في ملفك الأصلي)
    def clear_files(self):
        data["target_file"], data["target_path"], data["bar"] = "", "", 0.0
        with open(rf"{self.json_data}", "w", encoding="utf-8") as f: json.dump(data, f)
    def select_file(self):
        f = filedialog.askopenfilename(filetypes=[("Only PDF","*.pdf")])
        if f:
            data["target_file"], data["target_path"] = Path(f).name, f
            self.label_file.configure(text=data["target_file"])
            with open(rf"{self.json_data}", "w", encoding="utf-8") as f: json.dump(data, f)
    def run(self):
        if self.status == 0:
            self.status = 1
            data["status"] = 1
            with open(rf"{self.json_data}", "w", encoding="utf-8") as f: json.dump(data, f)
            threading.Thread(target=translte.main).start()
            self.update_bar()
    def update_bar(self):
        with open(rf"{self.json_data}","r", encoding="utf-8") as f: d = json.load(f)
        self.bar.set(d['bar'])
        self.lab.configure(text=f" % {int(d['bar']*100)} :التقدم")
        if self.status == 1: self.frame.after(3000, self.update_bar)