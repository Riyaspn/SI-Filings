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
    
    # Copy Chrome extension into distribution bundle
    ext_src = os.path.abspath(EXTENSION_DIR_NAME)
    ext_dest = os.path.join(dist_folder, "chrome_extension")
    if os.path.exists(ext_src):
        if os.path.exists(ext_dest):
            shutil.rmtree(ext_dest)
        shutil.copytree(ext_src, ext_dest)
        print(f"✅ Bundled Chrome Extension into: {ext_dest}")
    
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
AppPublisherURL=https://leadsharp.in/sifilings
AppSupportURL=https://leadsharp.in/sifilings/support
AppUpdatesURL=https://leadsharp.in/sifilings/updates
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
