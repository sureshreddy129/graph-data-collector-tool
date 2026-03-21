import time
from tkinter import Label, StringVar
from tkinter import ttk


class ProgressManager:
    def __init__(self, parent):
        self.parent = parent

        self.progress_var = StringVar(value="")

        self.progress_label = Label(
            parent,
            textvariable=self.progress_var,
            fg="blue",
            font=("Consolas", 10),
            anchor="w",
            width=100,
            bg=parent.cget("bg")
        )

        self.progress_bar = ttk.Progressbar(
            parent,
            orient="horizontal",
            length=400,
            mode="indeterminate"
        )

    # ----------------------------------------
    # Show progress UI
    # ----------------------------------------
    def start(self, message):
        self.progress_var.set(message.ljust(100))

        self.progress_label.grid(
            row=20, column=0, columnspan=2, pady=(10, 2)
        )
        self.progress_bar.grid(
            row=21, column=0, columnspan=2, pady=(0, 10)
        )

        self.progress_bar.start(10)
        self.progress_label.update()

    # ----------------------------------------
    # Update progress text
    # delay = seconds (for human visibility)
    # ----------------------------------------
    def update(self, message, delay=0.0):
        self.progress_var.set(message.ljust(100))
        self.progress_label.update()

        if delay > 0:
            time.sleep(delay)

    # ----------------------------------------
    # Stop progress UI
    # ----------------------------------------
    def stop(self, message=None):
        self.progress_bar.stop()
        self.progress_bar.grid_remove()

        if message:
            self.progress_var.set(message.ljust(100))
            self.progress_label.update()
        else:
            self.progress_label.grid_remove()

    # def thread_safe_progress(self, message, delay=0.0):
    #
    #     # Schedule progress update on UI thread
    #     self.window.after(
    #         0,
    #         lambda: self.update(message, delay)
    #     )
