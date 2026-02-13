# -*- coding: utf-8 -*-
"""
Git Clone Tool with GUI
Read Git repository URL from clipboard and execute clone with progress display

Usage:
    python git_clone_gui.py <target_directory>
    python git_clone_gui.py "E:\\path\\to\\"
"""

import sys
import os
import re
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
import pyperclip


class GitCloneGUI:
    def __init__(self, target_dir, repo_url):
        self.target_dir = target_dir
        self.repo_url = repo_url
        self.process = None

        # Create main window
        self.root = tk.Tk()
        self.root.title("Git Clone Progress")
        self.root.geometry("600x400")
        self.root.resizable(True, True)

        # Configure grid weights
        self.root.grid_rowconfigure(4, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Repository URL label
        tk.Label(self.root, text="Repository URL:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky="w", padx=10, pady=(10, 5)
        )

        url_frame = tk.Frame(self.root)
        url_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        url_frame.grid_columnconfigure(0, weight=1)

        self.url_label = tk.Label(
            url_frame,
            text=repo_url,
            font=("Arial", 9),
            fg="blue",
            wraplength=560,
            justify="left"
        )
        self.url_label.grid(row=0, column=0, sticky="w")

        # Target directory label
        tk.Label(self.root, text="Target Directory:", font=("Arial", 10, "bold")).grid(
            row=2, column=0, sticky="w", padx=10, pady=(0, 5)
        )

        dir_frame = tk.Frame(self.root)
        dir_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))
        dir_frame.grid_columnconfigure(0, weight=1)

        self.dir_label = tk.Label(
            dir_frame,
            text=target_dir,
            font=("Arial", 9),
            wraplength=560,
            justify="left"
        )
        self.dir_label.grid(row=0, column=0, sticky="w")

        # Progress bar
        self.progress = ttk.Progressbar(
            self.root,
            mode='determinate',
            length=580,
            maximum=100
        )
        self.progress.grid(row=4, column=0, sticky="ew", padx=10, pady=10)

        # Status label
        self.status_label = tk.Label(
            self.root,
            text="Preparing to clone...",
            font=("Arial", 9),
            fg="gray"
        )
        self.status_label.grid(row=5, column=0, sticky="w", padx=10, pady=(0, 5))

        # Output text area
        output_frame = tk.Frame(self.root)
        output_frame.grid(row=6, column=0, sticky="nsew", padx=10, pady=(0, 10))
        output_frame.grid_rowconfigure(0, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)

        self.root.grid_rowconfigure(6, weight=1)

        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            height=10,
            font=("Consolas", 9),
            wrap=tk.WORD
        )
        self.output_text.grid(row=0, column=0, sticky="nsew")

        # Close button
        self.close_button = tk.Button(
            self.root,
            text="Close",
            command=self.close_window,
            state=tk.DISABLED,
            width=15
        )
        self.close_button.grid(row=7, column=0, pady=10)

        # Center window
        self.center_window()

    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def append_output(self, text):
        """Append text to output area"""
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.root.update_idletasks()

    def update_status(self, text, color="black"):
        """Update status label"""
        self.status_label.config(text=text, fg=color)
        self.root.update_idletasks()

    def clone_repo(self):
        """Execute git clone in a separate thread"""
        original_dir = os.getcwd()

        try:
            os.chdir(self.target_dir)
            self.update_status("Cloning repository...", "blue")
            self.progress['value'] = 0

            # Execute git clone
            self.process = subprocess.Popen(
                ['git', 'clone', '--progress', self.repo_url],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                bufsize=1,
                universal_newlines=True
            )

            # Read output line by line
            line_count = 0
            for line in self.process.stdout:
                self.append_output(line)
                line_count += 1
                # Gradually increase progress (cap at 95 until completion)
                if line_count % 5 == 0:
                    current = self.progress['value']
                    if current < 95:
                        self.progress['value'] = min(current + 5, 95)
                        self.root.update_idletasks()

            # Wait for completion
            return_code = self.process.wait()

            # Set progress to 100 on completion
            self.progress['value'] = 100
            self.root.update_idletasks()

            if return_code == 0:
                self.update_status("✓ Clone successful!", "green")
                self.append_output("\n=== Clone completed successfully ===\n")
            else:
                self.update_status("✗ Clone failed!", "red")
                self.append_output("\n=== Clone failed ===\n")

        except FileNotFoundError:
            self.progress['value'] = 0
            self.update_status("✗ Git command not found!", "red")
            self.append_output("Error: git command not found. Please install Git and add to PATH\n")

        except Exception as e:
            self.progress['value'] = 0
            self.update_status(f"✗ Error: {str(e)}", "red")
            self.append_output(f"Error: {e}\n")

        finally:
            os.chdir(original_dir)
            self.close_button.config(state=tk.NORMAL)

    def start_clone(self):
        """Start cloning in a separate thread"""
        thread = threading.Thread(target=self.clone_repo, daemon=True)
        thread.start()

    def close_window(self):
        """Close the window"""
        if self.process and self.process.poll() is None:
            self.process.terminate()
        self.root.destroy()

    def run(self):
        """Run the GUI"""
        self.start_clone()
        self.root.mainloop()


def is_git_url(text):
    """Check if text is a valid Git repository URL"""
    text = text.strip()

    patterns = [
        r'^https?://[^\s]+\.git$',
        r'^https?://[^\s]+/[^\s]+/[^\s]+$',
        r'^git@[^\s]+:[^\s]+\.git$',
        r'^git@[^\s]+:[^\s]+$',
    ]

    for pattern in patterns:
        if re.match(pattern, text):
            return True

    git_domains = ['github.com', 'gitlab.com', 'gitee.com', 'bitbucket.org']
    if any(domain in text for domain in git_domains):
        return True

    return False


def main():
    if len(sys.argv) < 2:
        # Show error in GUI
        root = tk.Tk()
        root.withdraw()
        error_window = tk.Toplevel(root)
        error_window.title("Error")
        error_window.geometry("400x150")

        # Handle window close button
        error_window.protocol("WM_DELETE_WINDOW", lambda: (root.destroy(), sys.exit(1)))

        tk.Label(
            error_window,
            text="Usage Error",
            font=("Arial", 12, "bold")
        ).pack(pady=(20, 10))

        tk.Label(
            error_window,
            text="Usage: python git_clone_gui.py <target_directory>\nExample: python git_clone_gui.py \"E:\\\\path\\\\to\\\\\"",
            justify="left"
        ).pack(pady=10)

        tk.Button(
            error_window,
            text="OK",
            command=lambda: (root.destroy(), sys.exit(1)),
            width=10
        ).pack(pady=10)

        # Center error window
        error_window.update_idletasks()
        x = (error_window.winfo_screenwidth() // 2) - (error_window.winfo_width() // 2)
        y = (error_window.winfo_screenheight() // 2) - (error_window.winfo_height() // 2)
        error_window.geometry(f"+{x}+{y}")

        root.mainloop()
        sys.exit(1)

    target_dir = sys.argv[1]

    # Check if target directory exists
    if not os.path.exists(target_dir):
        root = tk.Tk()
        root.withdraw()
        error_window = tk.Toplevel(root)
        error_window.title("Error")
        error_window.geometry("400x120")

        # Handle window close button
        error_window.protocol("WM_DELETE_WINDOW", lambda: (root.destroy(), sys.exit(1)))

        tk.Label(
            error_window,
            text=f"Target directory does not exist:\n{target_dir}",
            wraplength=380,
            justify="left"
        ).pack(pady=20)

        tk.Button(
            error_window,
            text="OK",
            command=lambda: (root.destroy(), sys.exit(1)),
            width=10
        ).pack(pady=10)

        error_window.update_idletasks()
        x = (error_window.winfo_screenwidth() // 2) - (error_window.winfo_width() // 2)
        y = (error_window.winfo_screenheight() // 2) - (error_window.winfo_height() // 2)
        error_window.geometry(f"+{x}+{y}")

        root.mainloop()
        sys.exit(1)

    # Get clipboard content
    try:
        clipboard_content = pyperclip.paste()
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        error_window = tk.Toplevel(root)
        error_window.title("Error")
        error_window.geometry("400x120")

        # Handle window close button
        error_window.protocol("WM_DELETE_WINDOW", lambda: (root.destroy(), sys.exit(1)))

        tk.Label(
            error_window,
            text=f"Cannot read clipboard: {e}",
            wraplength=380
        ).pack(pady=20)

        tk.Button(
            error_window,
            text="OK",
            command=lambda: (root.destroy(), sys.exit(1)),
            width=10
        ).pack(pady=10)

        error_window.update_idletasks()
        x = (error_window.winfo_screenwidth() // 2) - (error_window.winfo_width() // 2)
        y = (error_window.winfo_screenheight() // 2) - (error_window.winfo_height() // 2)
        error_window.geometry(f"+{x}+{y}")

        root.mainloop()
        sys.exit(1)

    if not clipboard_content:
        root = tk.Tk()
        root.withdraw()
        error_window = tk.Toplevel(root)
        error_window.title("Error")
        error_window.geometry("400x100")

        # Handle window close button
        error_window.protocol("WM_DELETE_WINDOW", lambda: (root.destroy(), sys.exit(1)))

        tk.Label(
            error_window,
            text="Clipboard is empty",
            font=("Arial", 10)
        ).pack(pady=20)

        tk.Button(
            error_window,
            text="OK",
            command=lambda: (root.destroy(), sys.exit(1)),
            width=10
        ).pack(pady=10)

        error_window.update_idletasks()
        x = (error_window.winfo_screenwidth() // 2) - (error_window.winfo_width() // 2)
        y = (error_window.winfo_screenheight() // 2) - (error_window.winfo_height() // 2)
        error_window.geometry(f"+{x}+{y}")

        root.mainloop()
        sys.exit(1)

    # Check if it's a Git URL
    if not is_git_url(clipboard_content):
        root = tk.Tk()
        root.withdraw()
        error_window = tk.Toplevel(root)
        error_window.title("Error")
        error_window.geometry("450x180")

        # Handle window close button
        error_window.protocol("WM_DELETE_WINDOW", lambda: (root.destroy(), sys.exit(1)))

        tk.Label(
            error_window,
            text="Invalid Git URL",
            font=("Arial", 12, "bold")
        ).pack(pady=(20, 10))

        tk.Label(
            error_window,
            text=f"Clipboard content:\n{clipboard_content[:100]}",
            wraplength=430,
            justify="left",
            fg="gray"
        ).pack(pady=5)

        tk.Label(
            error_window,
            text="Supported formats:\n- https://github.com/user/repo.git\n- git@github.com:user/repo.git",
            justify="left"
        ).pack(pady=10)

        tk.Button(
            error_window,
            text="OK",
            command=lambda: (root.destroy(), sys.exit(1)),
            width=10
        ).pack(pady=10)

        error_window.update_idletasks()
        x = (error_window.winfo_screenwidth() // 2) - (error_window.winfo_width() // 2)
        y = (error_window.winfo_screenheight() // 2) - (error_window.winfo_height() // 2)
        error_window.geometry(f"+{x}+{y}")

        root.mainloop()
        sys.exit(1)

    # Create and run GUI
    app = GitCloneGUI(target_dir, clipboard_content.strip())
    app.run()


if __name__ == '__main__':
    main()
