"""
Setup utilities for capture system prerequisites.
Handles mitmproxy installation, certificate generation, and prerequisite checking.
"""

import subprocess
import ctypes
import time
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class PrerequisiteStatus:
    """Status of capture system prerequisites."""
    is_admin: bool
    has_mitmproxy: bool
    mitmproxy_version: Optional[str]
    has_certificate: bool
    certificate_path: Optional[Path]


def check_prerequisites() -> PrerequisiteStatus:
    """
    Check if all prerequisites for capture system are met.

    Returns:
        PrerequisiteStatus object with current status of all requirements
    """
    # Check admin privileges (Windows only)
    is_admin = False
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        pass

    # Check mitmproxy installation
    has_mitmproxy = False
    mitmproxy_version = None
    try:
        result = subprocess.run(
            ["mitmdump", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            has_mitmproxy = True
            # Extract version from output (e.g., "Mitmproxy 10.1.1")
            mitmproxy_version = result.stdout.split()[1] if result.stdout else "unknown"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Check certificate
    cert_path = Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.cer"
    has_certificate = cert_path.exists()

    return PrerequisiteStatus(
        is_admin=is_admin,
        has_mitmproxy=has_mitmproxy,
        mitmproxy_version=mitmproxy_version,
        has_certificate=has_certificate,
        certificate_path=cert_path if has_certificate else None
    )


def install_mitmproxy(timeout: int = 120) -> bool:
    """
    Install mitmproxy via pip.

    Args:
        timeout: Maximum time in seconds to wait for installation

    Returns:
        True if installation succeeded, False otherwise

    Raises:
        subprocess.TimeoutExpired: If installation takes longer than timeout
        Exception: If installation fails for other reasons
    """
    result = subprocess.run(
        ["pip", "install", "mitmproxy"],
        capture_output=True,
        text=True,
        timeout=timeout
    )

    if result.returncode != 0:
        raise Exception(f"Installation failed: {result.stderr}")

    return True


def setup_certificate() -> Path:
    """
    Generate mitmproxy CA certificate by starting and stopping mitmdump.

    Returns:
        Path to the generated certificate

    Raises:
        FileNotFoundError: If mitmdump is not installed
        Exception: If certificate generation fails
    """
    # Start mitmdump briefly to generate certificate
    process = subprocess.Popen(
        ["mitmdump"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Give it time to generate the certificate
    time.sleep(3)

    # Stop the process
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()

    # Verify certificate was created
    cert_path = Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.cer"
    if not cert_path.exists():
        raise Exception("Certificate was not generated")

    return cert_path


def open_certificate(cert_path: Path) -> None:
    """
    Open certificate file in Windows (for manual installation).

    Args:
        cert_path: Path to certificate file

    Raises:
        Exception: If unable to open certificate
    """
    if not cert_path.exists():
        raise FileNotFoundError(f"Certificate not found: {cert_path}")

    try:
        os.startfile(str(cert_path))
    except Exception as e:
        raise Exception(f"Failed to open certificate: {e}")
