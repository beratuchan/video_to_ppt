import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import queue
import os
from typing import List
from gui.conversion_controller import ConversionController
from gui.ppt_grid_editor_frame import PPTGridEditorFrame
from gui.progress_bar import ProgressBar
from utils.settings_manager import SettingsManager

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube2Slides - Video'dan Slayt ve PPT Düzenleme")
        self.state('zoomed')
        self.bind('<Escape>', lambda e: self._on_close())
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._create_menu()

        self.msg_queue = queue.Queue()
        self.controller = ConversionController(self.msg_queue)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.conversion_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.conversion_tab, text="Video ➔ Slayt")

        self.editor_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.editor_tab, text="PPT Düzenleme")
        self.editor_frame = PPTGridEditorFrame(self.editor_tab, temp_video_path=None)
        self.editor_frame.pack(fill=tk.BOTH, expand=True)

        self._create_conversion_widgets()
        self._poll_queue()

    def _create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        ayarlar_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayarlar", menu=ayarlar_menu)
        ayarlar_menu.add_command(label="Video Depolama Klasörü Seç", command=self._choose_video_folder)
        ayarlar_menu.add_separator()
        ayarlar_menu.add_command(label="Çıkış", command=self._on_close)

    def _choose_video_folder(self):
        current = SettingsManager.get_video_storage_folder()
        folder = filedialog.askdirectory(
            title="Videoların kaydedileceği varsayılan klasörü seçin",
            initialdir=current if current else os.path.expanduser("~")
        )
        if folder:
            SettingsManager.set_video_storage_folder(folder)
            messagebox.showinfo("Başarılı", f"Video depolama klasörü:\n{folder}")
            self._update_video_folder_label()
            self._update_video_folder_path_label()

    def _create_conversion_widgets(self):
        tk.Label(self.conversion_tab, text="YouTube URL (tek veya satır satır):").pack(pady=5)
        self.url_text = tk.Text(self.conversion_tab, height=8)
        self.url_text.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)

        # Keep video frame - satırda checkbox, buton ve etiket
        keep_frame = tk.Frame(self.conversion_tab)
        keep_frame.pack(pady=5, fill=tk.X, padx=10)
        
        self.keep_video_var = tk.BooleanVar(value=False)
        self.keep_check = tk.Checkbutton(keep_frame, text="Videoyu kalıcı olarak kaydet", variable=self.keep_video_var)
        self.keep_check.pack(side=tk.LEFT)
        
        self.select_folder_btn = tk.Button(keep_frame, text="Klasör Seç", command=self._choose_video_folder)
        self.select_folder_btn.pack(side=tk.LEFT, padx=5)
        
        self.video_folder_label = tk.Label(keep_frame, text="", fg="gray", font=("Arial", 8))
        self.video_folder_label.pack(side=tk.LEFT, padx=5)
        
        self._update_video_folder_label()
        self._update_video_folder_path_label()

        btn_frame = tk.Frame(self.conversion_tab)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Listeyi Temizle", command=self._clear_urls).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Dönüştürmeyi Başlat", command=self._start_conversion).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Durdur", command=self._stop_conversion).pack(side=tk.LEFT, padx=5)

        self.progress_bar = ProgressBar(self.conversion_tab, max_value=100)
        self.progress_bar.pack(fill=tk.X, padx=10, pady=10)

        self.status_label = tk.Label(self.conversion_tab, text="Hazır", anchor="w")
        self.status_label.pack(fill=tk.X, padx=10)

        self.result_listbox = tk.Listbox(self.conversion_tab, height=8)
        self.result_listbox.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)

    def _update_video_folder_label(self):
        folder = SettingsManager.get_video_storage_folder()
        if folder:
            self.video_folder_label.config(text=f"(Kayıt klasörü: {folder})")
        else:
            self.video_folder_label.config(text="(Klasör seçilmedi - geçici dosya)")

    def _update_video_folder_path_label(self):
        # İsteğe bağlı: ayrı bir etiketle detaylı yol gösterilebilir
        pass

    def _clear_urls(self):
        self.url_text.delete(1.0, tk.END)

    def _get_urls(self) -> List[str]:
        raw = self.url_text.get(1.0, tk.END).strip().splitlines()
        return [u.strip() for u in raw if u.strip()]

    def _start_conversion(self):
        urls = self._get_urls()
        if not urls:
            messagebox.showerror("Hata", "Lütfen en az bir URL girin.")
            return
        self.result_listbox.delete(0, tk.END)
        self.progress_bar.set_value(0)
        self.status_label.config(text="İşlem başlatılıyor...")
        keep_video = self.keep_video_var.get()
        if keep_video and not SettingsManager.get_video_storage_folder():
            if not messagebox.askyesno("Uyarı", "Varsayılan video depolama klasörü seçilmemiş. Videolar geçici olarak indirilecek. Devam etmek istiyor musunuz?"):
                return
            self.keep_video_var.set(False)
            keep_video = False
        self.controller.start(urls, keep_video=keep_video)

    def _stop_conversion(self):
        if self.controller.is_running:
            self.controller.stop()
            self.status_label.config(text="Durduruluyor...")
        else:
            messagebox.showinfo("Bilgi", "Devam eden işlem yok.")

    def _poll_queue(self):
        try:
            while True:
                msg = self.msg_queue.get_nowait()
                self._handle_message(msg)
        except queue.Empty:
            pass
        finally:
            self.after(100, self._poll_queue)

    def _handle_message(self, msg):
        msg_type = msg[0]
        if msg_type == 'progress':
            _, percent, text = msg
            if percent >= 0:
                self.progress_bar.set_value(percent)
            self.status_label.config(text=text)
        elif msg_type == 'result':
            _, url, pptx_path = msg
            self.result_listbox.insert(tk.END, f"✔ BAŞARILI - {url} -> {pptx_path}")
        elif msg_type == 'error':
            _, url, err = msg
            self.result_listbox.insert(tk.END, f"✘ HATA - {url}: {err}")
        elif msg_type == 'messagebox':
            _, title, text = msg
            messagebox.showwarning(title, text)
        elif msg_type == 'finished':
            _, success, total = msg
            self.status_label.config(text=f"İşlem tamamlandı. Başarılı: {success}/{total}")
            if success == total:
                messagebox.showinfo("Bitti", "Tüm videolar başarıyla dönüştürüldü.\nÇıktılar ana dizinde.")
            else:
                messagebox.showwarning("Bitti", f"{success}/{total} başarılı.\nHatalar için listeye bakın.")
        elif msg_type == 'open_ppt_editor':
            _, pptx_path, video_path = msg
            self.notebook.select(self.editor_tab)
            self.editor_frame.set_pptx_and_video(pptx_path, video_path)

    def _on_close(self):
        if self.controller.is_running:
            if not messagebox.askokcancel("Çıkış", "İşlem devam ediyor. Çıkılsın mı?"):
                return
            self.controller.stop()
        self.destroy()