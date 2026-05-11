import tkinter.ttk as ttk

class ProgressBar:
    def __init__(self, parent, max_value=100):
        self.bar = ttk.Progressbar(parent, maximum=max_value)
        
    def set_value(self, value):
        self.bar['value'] = value
        
    def set_max(self, value):
        self.bar['maximum'] = value
        
    def pack(self, **kwargs):
        self.bar.pack(**kwargs)