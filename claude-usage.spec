# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Claude Code Usage Overlay.

Build command:
    pyinstaller claude-usage.spec

This creates a single-file Windows executable (ClaudeUsageOverlay.exe)
that can be distributed without requiring Python installation.
"""

import sys
from pathlib import Path

# Get the project root directory
project_root = Path(SPECPATH)

a = Analysis(
    [str(project_root / 'src' / 'main.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[],
    hiddenimports=[
        # pystray backends for different platforms
        'pystray._win32',
        'pystray._darwin',
        'pystray._xorg',
        'pystray._appindicator',
        # PIL plugins
        'PIL._tkinter_finder',
        # desktop-notifier backends
        'desktop_notifier.backends.winrt',
        'desktop_notifier.backends.macos',
        'desktop_notifier.backends.dbus',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unused modules to reduce size
        'tkinter',
        'unittest',
        'email',
        'html',
        'http',
        'xml',
        'pydoc',
        'doctest',
        'argparse',
        'difflib',
        'inspect',
        'pdb',
        'profile',
        'pstats',
    ],
    noarchive=False,
    optimize=2,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ClaudeUsageOverlay',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Windows-specific options
    icon=None,  # Add icon path here if you have one: 'assets/icon.ico'
    version=None,  # Add version info file here if needed
)

# macOS app bundle (optional)
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='Claude Usage Overlay.app',
        icon=None,  # Add icon path here if you have one: 'assets/icon.icns'
        bundle_identifier='com.claude-usage.overlay',
        info_plist={
            'CFBundleShortVersionString': '2.0.0',
            'CFBundleVersion': '2.0.0',
            'NSHighResolutionCapable': True,
            'LSUIElement': True,  # Hide from Dock (menu bar app)
        },
    )
