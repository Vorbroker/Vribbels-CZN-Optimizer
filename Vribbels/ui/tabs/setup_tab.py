"""Setup tab for first-time configuration and prerequisite checking."""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import ctypes
from pathlib import Path
from capture import setup_certificate, open_certificate
from ..base_tab import BaseTab


class SetupTab(BaseTab):
    """
    Setup tab for configuring prerequisites before using capture feature.

    Displays status of:
    - Python installation
    - mitmproxy installation
    - Certificate generation
    - Administrator privileges
    """

    def __init__(self, parent, context):
        super().__init__(parent, context)

        # Status label widgets
        self.python_status = None
        self.mitmproxy_status = None
        self.cert_status = None
        self.admin_status = None

        self.setup_ui()

        # Auto-check status after UI setup
        self.root.after(1000, self.check_status)

    def setup_ui(self):
        """Setup the Setup tab UI."""
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title
        ttk.Label(main_frame, text="First-Time Setup",
                  font=("Segoe UI", 14, "bold")).pack(anchor=tk.W)
        ttk.Label(main_frame,
                  text="Complete these steps before using the capture feature",
                  foreground=self.colors["fg_dim"]).pack(anchor=tk.W, pady=(0, 10))

        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Setup Status", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        self.python_status = ttk.Label(status_frame, text="Checking Python...",
                                        font=("Segoe UI", 10))
        self.python_status.pack(anchor=tk.W, pady=2)

        self.mitmproxy_status = ttk.Label(status_frame, text="Checking mitmproxy...",
                                           font=("Segoe UI", 10))
        self.mitmproxy_status.pack(anchor=tk.W, pady=2)

        self.cert_status = ttk.Label(status_frame, text="Checking certificate...",
                                      font=("Segoe UI", 10))
        self.cert_status.pack(anchor=tk.W, pady=2)

        self.admin_status = ttk.Label(status_frame, text="Checking admin rights...",
                                       font=("Segoe UI", 10))
        self.admin_status.pack(anchor=tk.W, pady=2)

        # Button frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(btn_frame, text="Check Status",
                   command=self.check_status, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Generate & Install Cert",
                   command=self.setup_cert, width=22).pack(side=tk.LEFT, padx=5)

        # Instructions frame
        instr_frame = ttk.LabelFrame(main_frame, text="Setup Instructions", padding=10)
        instr_frame.pack(fill=tk.BOTH, expand=True)

        instructions = """STEP 1: Generate and install certificate
  - Click "Generate & Install Cert" button
  - When the certificate dialog opens:
    1. Click "Install Certificate"
    2. Select "Local Machine"
    3. Click Next
    4. Select "Place all certificates in the following store"
    5. Click Browse and select "Trusted Root Certification Authorities"
    6. Click OK, Next, then Finish

STEP 2: Verify setup
  - Click "Check Status" to verify all components are ready
  - All items should show green checkmarks [OK]"""

        instr_text = scrolledtext.ScrolledText(
            instr_frame, height=18, wrap=tk.WORD,
            bg=self.colors["bg_light"], fg=self.colors["fg"]
        )
        instr_text.insert("1.0", instructions)
        instr_text.config(state=tk.DISABLED)
        instr_text.pack(fill=tk.BOTH, expand=True)

    def check_status(self):
        """Check status of all prerequisites."""
        # Check Python
        try:
            result = subprocess.run(["python", "--version"],
                                     capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip() or result.stderr.strip()
                self.python_status.config(text=f"[OK] {version}",
                                           foreground=self.colors["green"])
            else:
                raise FileNotFoundError()
        except:
            self.python_status.config(text="[X] Python not found",
                                       foreground=self.colors["red"])

        # Check mitmproxy
        try:
            result = subprocess.run(["mitmdump", "--version"],
                                     capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.split()[1] if result.stdout else "installed"
                self.mitmproxy_status.config(text=f"[OK] mitmproxy {version}",
                                              foreground=self.colors["green"])
            else:
                raise FileNotFoundError()
        except:
            self.mitmproxy_status.config(text="[X] mitmproxy not installed",
                                          foreground=self.colors["red"])

        # Check certificate
        cert_path = Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.cer"
        if cert_path.exists():
            self.cert_status.config(text=f"[OK] Certificate exists",
                                     foreground=self.colors["green"])
        else:
            self.cert_status.config(text="[X] Certificate not generated",
                                     foreground=self.colors["red"])

        # Check admin rights
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if is_admin:
                self.admin_status.config(text="[OK] Running as Administrator",
                                          foreground=self.colors["green"])
            else:
                self.admin_status.config(text="[!] Not running as Administrator",
                                          foreground=self.colors["yellow"])
        except:
            self.admin_status.config(text="? Could not check admin status",
                                      foreground=self.colors["yellow"])

    def setup_cert(self):
        """Generate and open certificate for installation."""
        try:
            cert_path = setup_certificate()
            messagebox.showinfo(
                "Certificate Generated",
                f"Certificate generated at:\n{cert_path}\n\n"
                "Opening certificate installer..."
            )
            open_certificate(cert_path)
            self.check_status()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate certificate: {e}")
