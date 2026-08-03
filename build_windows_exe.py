"""
SI Filings Pro — Comprehensive Windows App & Extension Builder
==============================================================
Automates compilation of the desktop application into a standalone Windows Executable (.exe),
bundles the Chrome Extension (mca-extension) for offline developer loading,
and generates an Inno Setup script to compile 'SI_Filings_Pro_Setup_v1.0.0.exe'.
"""

import os
import sys
import subprocess
import shutil
from PIL import Image, ImageDraw, ImageFont

APP_NAME = "SI Filings Pro"
APP_VERSION = "1.0.0"
COMPANY_NAME = "Sharp Intell Technologies"
ICON_FILENAME = "app_icon.ico"
MAIN_SCRIPT = "app.py"
EXTENSION_DIR_NAME = "mca-extension"

def create_app_icon():
    """Generate a premium multi-resolution Windows application icon (.ico)."""
    print(f"🎨 Synthesizing branded application icon: {ICON_FILENAME}...")
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    images = []
    
    for w, h in sizes:
        img = Image.new("RGBA", (w, h), color=(15, 23, 42, 255))
        draw = ImageDraw.Draw(img)
        
        margin = max(1, w // 16)
        radius = max(2, w // 5)
        draw.rounded_rectangle(
            [margin, margin, w - margin, h - margin],
            radius=radius,
            fill=(56, 189, 248, 255),
            outline=(14, 165, 233, 255),
            width=max(1, w // 20)
        )
        
        try:
            font_size = int(w * 0.45)
            font = ImageFont.truetype("arialbd.ttf", font_size)
        except IOError:
            try:
                font_size = int(w * 0.45)
                font = ImageFont.truetype("arial.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()
                
        text = "SI"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = (w - tw) // 2 - bbox[0]
        ty = (h - th) // 2 - bbox[1] - (h // 20)
        
        draw.text((tx, ty), text, fill=(15, 23, 42, 255), font=font)
        images.append(img)
        
    images[0].save(
        ICON_FILENAME,
        format="ICO",
        sizes=sizes,
        append_images=images[1:]
    )
    print("✅ Application Icon created successfully!")

def build_executable():
    """Invoke PyInstaller to build a standalone, windowed application executable."""
    print("\n📦 Starting PyInstaller compilation process...")
    try:
        import PyInstaller
    except ImportError:
        print("⚡ PyInstaller not detected. Installing via pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    folder_name = APP_NAME.replace(" ", "_")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=" + folder_name,
        "--icon=" + os.path.abspath(ICON_FILENAME),
        "--noconfirm",
        "--clean",
        "--windowed",
        "--collect-all", "customtkinter",
        "--collect-all", "google.generativeai",
        "--collect-all", "google.genai",
        "--collect-all", "pymupdf",
        "--hidden-import=win32com.client",
        "--hidden-import=win32timezone",
        "--hidden-import=openpyxl",
        "--hidden-import=PIL",
        "--hidden-import=requests",
        "--hidden-import=flask",
        "--hidden-import=flask_cors",
        MAIN_SCRIPT
    ]
    
    print(f"Executing PyInstaller build command...")
    subprocess.check_call(cmd)
    
    dist_folder = os.path.abspath(os.path.join("dist", folder_name))
    
    # Secure & Clean Chrome Extension Bundle (Exclude dev tools, strip comments)
    ext_src = os.path.abspath(EXTENSION_DIR_NAME)
    ext_dest = os.path.join(dist_folder, "chrome_extension")
    if os.path.exists(ext_src):
        if os.path.exists(ext_dest):
            shutil.rmtree(ext_dest)
        os.makedirs(ext_dest, exist_ok=True)

        import re
        whitelist_files = {"manifest.json", "background.js", "content.js", "popup.html", "popup.js"}
        
        for fname in os.listdir(ext_src):
            src_file = os.path.join(ext_src, fname)
            if os.path.isfile(src_file) and (fname in whitelist_files or fname.endswith(".ico") or fname.endswith(".png")):
                dest_file = os.path.join(ext_dest, fname)
                if fname.endswith(".js"):
                    # Apply automated IP protection & comment stripping
                    with open(src_file, "r", encoding="utf-8", errors="ignore") as in_f:
                        content = in_f.read()
                    # Strip multi-line /* ... */ comments
                    content = re.sub(r'/\*[\s\S]*?\*/', '', content)
                    # Strip standalone single-line // comments & empty lines
                    lines = []
                    for line in content.splitlines():
                        stripped = line.strip()
                        if stripped.startswith("//") or not stripped:
                            continue
                        lines.append(line)
                    with open(dest_file, "w", encoding="utf-8") as out_f:
                        out_f.write("/* Copyright (C) 2026 Sharp Intell Technologies LLP - Protected & Proprietary Statutory Engine */\n" + "\n".join(lines))
                else:
                    shutil.copy2(src_file, dest_file)
                    
        print(f"✅ Securely processed and bundled clean Chrome Extension into: {ext_dest}")
    
    # Generate interactive offline onboarding HTML & TXT guides in distribution folder
    html_guide_path = os.path.join(dist_folder, "🚀_QUICK_START_&_EXTENSION_SETUP.html")
    with open(html_guide_path, "w", encoding="utf-8") as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SI Filings Pro — Quick Start & Chrome RPA Setup Guide</title>
<style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; padding: 40px; line-height: 1.6; max-width: 800px; margin: auto; }
    .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 30px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    h1 { color: #38bdf8; margin-top: 0; }
    h2 { color: #10b981; margin-top: 0; }
    code { background: #0e1422; color: #f59e0b; padding: 4px 8px; border-radius: 6px; font-size: 15px; border: 1px solid #334155; font-weight: bold; }
    .step { background: #0e1422; padding: 15px 20px; border-radius: 8px; margin-bottom: 12px; border-left: 4px solid #38bdf8; font-size: 15px; }
    a { color: #38bdf8; text-decoration: none; font-weight: bold; }
    a:hover { text-decoration: underline; }
</style>
</head>
<body>
<div class="card">
    <h1>🚀 Welcome to SI Filings Pro v1.0.0</h1>
    <p>Thank you for choosing Sharp Intell Technologies for your statutory corporate filing automation. Follow the simple steps below to initialize your application and activate the Chrome RPA bridge.</p>
</div>

<div class="card">
    <h2>Step 1: Launch the Software & Activate License</h2>
    <div class="step">1️⃣ Double-click <code>SI_Filings_Pro.exe</code> located inside this folder.</div>
    <div class="step">2️⃣ If you don't have a license key yet, visit our official website at <a href="https://si-filings.pages.dev" target="_blank">https://si-filings.pages.dev</a> and click <strong>🎁 Claim 10 Free Filings</strong> to instantly receive your 100 Free Trial Credits!</div>
    <div class="step">3️⃣ Paste your firm email and license key into the login screen and click Activate.</div>
</div>

<div class="card">
    <h2>Step 2: Install the Bundled Chrome RPA Extension (30-Second Setup)</h2>
    <p>Our automation bridge runs safely via local computer loopback (<code>http://127.0.0.1:8765</code>), ensuring your hardware USB Digital Signature Certificates (DSC) remain 100% locally secure without external web transmission.</p>
    
    <div class="step">1️⃣ Open Google Chrome and copy-paste <code>chrome://extensions</code> into your top browser address bar.</div>
    <div class="step">2️⃣ Turn ON the <strong>"Developer mode"</strong> toggle switch at the top-right corner of Chrome.</div>
    <div class="step">3️⃣ Click the <strong>"Load unpacked"</strong> button at the top-left, select the <code>chrome_extension</code> folder located inside this directory, and click Select Folder!</div>
    
    <p style="margin-top: 15px; color: #a7f3d0; font-size: 14px;">💡 <strong>Pro Tip:</strong> Inside the Windows application, open the <em>"⚡ Chrome RPA"</em> tab and click <strong>"📂 Open Extension Folder in Windows Explorer"</strong> to open this folder directly without searching!</p>
</div>

<div class="card" style="text-align: center; background: #0e1422;">
    <p style="color: #94a3b8; font-size: 13px; margin: 0;">Need technical guidance or enterprise volume support?<br>Email our compliance engineering team at <a href="mailto:pnriyas50@gmail.com">pnriyas50@gmail.com</a></p>
</div>
</body>
</html>""")

    txt_guide_path = os.path.join(dist_folder, "📖_README_SETUP_INSTRUCTIONS.txt")
    with open(txt_guide_path, "w", encoding="utf-8") as f:
        f.write("""================================================================================
SI FILINGS PRO v1.0.0 — QUICK START & CHROME EXTENSION SETUP GUIDE
by Sharp Intell Technologies LLP
================================================================================

STEP 1: LAUNCH THE SOFTWARE
---------------------------
1. Double-click "SI_Filings_Pro.exe" to start the application.
2. If you need a firm license key, get 100 Free Trial Credits instantly at:
   https://si-filings.pages.dev
3. Paste your license key into the login screen to unlock all features.

STEP 2: INSTALL THE CHROME RPA EXTENSION (30-Second Setup)
----------------------------------------------------------
To enable 1-click auto-filling directly on the MCA V3 Web Portal while keeping
your hardware USB Digital Signature Certificates (DSC) 100% secure offline:

1. Open Google Chrome and type in the address bar: chrome://extensions
2. Turn ON the "Developer mode" toggle switch at the top-right corner.
3. Click "Load unpacked" at the top-left and select the "chrome_extension"
   folder located inside this software directory.

TIP: Inside SI Filings Pro, open the "⚡ Chrome RPA" tab and click
"📂 Open Extension Folder in Windows Explorer" for instant 1-click access!

================================================================================
For technical & billing support: pnriyas50@gmail.com
================================================================================
""")
    print(f"✅ Generated onboarding HTML & TXT setup guide files in distribution folder!")
    print(f"🎉 Build Complete! Standalone application folder generated at:\n   {dist_folder}")

def generate_inno_setup_script():
    """Create a professional setup installer script (.iss) for Inno Setup compiler."""
    print("\n📜 Generating Inno Setup script (build_installer.iss)...")
    
    folder_name = APP_NAME.replace(" ", "_")
    exe_name = folder_name + ".exe"
    dist_dir = os.path.abspath(os.path.join("dist", folder_name))
    
    iss_content = f"""[Setup]
AppName={APP_NAME}
AppVersion={APP_VERSION}
AppPublisher={COMPANY_NAME}
AppPublisherURL=https://si-filings.pages.dev
AppSupportURL=https://si-filings.pages.dev/contact.html
AppUpdatesURL=https://si-filings.pages.dev/#download-section
DefaultDirName={{autopf}}\\{APP_NAME}
DefaultGroupName={APP_NAME}
AllowNoIcons=yes
LicenseFile=
OutputBaseFilename={folder_name}_Setup_v{APP_VERSION}
SetupIconFile={os.path.abspath(ICON_FILENAME)}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"

[Files]
Source: "{dist_dir}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\{APP_NAME}"; Filename: "{{app}}\\{exe_name}"; IconFilename: "{{app}}\\{ICON_FILENAME}"
Name: "{{group}}\\Uninstall {APP_NAME}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\{APP_NAME}"; Filename: "{{app}}\\{exe_name}"; Tasks: desktopicon; IconFilename: "{{app}}\\{ICON_FILENAME}"

[Run]
Filename: "{{app}}\\{exe_name}"; Description: "{{cm:LaunchProgram,{APP_NAME}}}"; Flags: nowait postinstall skipifsilent
"""
    with open("build_installer.iss", "w", encoding="utf-8") as f:
        f.write(iss_content)
        
    print("✅ Inno Setup script created: build_installer.iss")
    print("\n" + "="*70)
    print("🚀 DISTRIBUTION INSTRUCTIONS:")
    print("1. Test application locally: dist/SI_Filings_Pro/SI_Filings_Pro.exe")
    print("2. Chrome extension bundled at: dist/SI_Filings_Pro/chrome_extension")
    print("3. To build redistributable installer (.exe setup):")
    print("   - Open 'build_installer.iss' with Inno Setup and click 'Compile'.")
    print("   - Output: 'SI_Filings_Pro_Setup_v1.0.0.exe' ready for distribution!")
    print("="*70)

if __name__ == "__main__":
    create_app_icon()
    build_executable()
    generate_inno_setup_script()
