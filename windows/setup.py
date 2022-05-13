import glob
import os
import re
import ssl
import sys
import tempfile

from pkgutil import walk_packages
from cx_Freeze import Executable, setup


if sys.platform == "win32":
    gui_base = "Win32GUI"
    sys_base = sys.prefix

else:
    raise RuntimeError("Only Windows is supported")

include_files = [('../gtk_switcher/atem.gresource', 'atem.gresource')]
plugin_packages = []

gtk_version = 3
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
sys.path.append(src_path)


def add_files_by_pattern(rel_path, starts_with, ends_with, output_path=None, recursive=False):

    for full_path in glob.glob(os.path.join(sys_base, rel_path, '**'), recursive=recursive):
        short_path = os.path.relpath(full_path, os.path.join(sys_base, rel_path))

        if not short_path.startswith(starts_with):
            continue

        if not short_path.endswith(ends_with):
            continue

        if output_path is None:
            output_path = rel_path

        include_files.append((full_path, os.path.join(output_path, short_path)))

def add_gtk():

    # This also includes all dlls required by GTK
    add_files_by_pattern("bin", "libgtk-" + str(gtk_version), ".dll", output_path="lib")
    add_files_by_pattern("bin", "libhandy-", ".dll", output_path="lib")
    add_files_by_pattern("bin", "libusb-1", ".dll", output_path="lib")

    include_files.append((os.path.join(sys_base, "share/glib-2.0/schemas/gschemas.compiled"),
                         "share/glib-2.0/schemas/gschemas.compiled"))

    # gdbus required for single-instance application
    include_files.append((os.path.join(sys_base, "bin/gdbus.exe"), "lib/gdbus.exe"))

    # Pixbuf loaders
    temp_dir = tempfile.mkdtemp()
    loaders_file = "lib/gdk-pixbuf-2.0/2.10.0/loaders.cache"
    temp_loaders_file = os.path.join(temp_dir, "loaders.cache")

    with open(temp_loaders_file, "w") as file_handle:
        data = open(os.path.join(sys_base, loaders_file)).read()
        data = data.replace("lib\\\\gdk-pixbuf-2.0\\\\2.10.0\\\\loaders\\\\", "lib\\\\")
        file_handle.write(data)

    include_files.append((temp_loaders_file, loaders_file))
    add_files_by_pattern("lib/gdk-pixbuf-2.0/2.10.0/loaders", "libpixbufloader-", ".dll", output_path="lib")

    # Typelibs
    required_typelibs = (
        "Gtk-" + str(gtk_version),
        "Gio-",
        "Gdk-" + str(gtk_version),
        "GLib-",
        "Atk-",
        "HarfBuzz-",
        "Pango-",
        "GObject-",
        "GdkPixbuf-",
        "cairo-",
        "GModule-",
        "Handy-1",
    )
    add_files_by_pattern("lib/girepository-1.0", required_typelibs, ".typelib")


def add_icon_packs():

    required_icon_packs = (
        "Adwaita",
        "hicolor"
    )
    add_files_by_pattern("share/icons", required_icon_packs, (".theme", ".svg"), recursive=True)


def add_themes():

    # "Mac" is required for macOS-specific keybindings in GTK
    required_themes = (
        "Default",
        "Mac"
    )
    add_files_by_pattern("share/themes", required_themes, ".css", recursive=True)


def add_ssl_certs():
    ssl_paths = ssl.get_default_verify_paths()
    include_files.append((ssl_paths.openssl_cafile, "share/ssl/cert.pem"))

def add_locales():
    languages = ["en", "nl", "tr"]
    add_files_by_pattern("share/locale", tuple(languages), "gtk30.mo", recursive=True)
    add_files_by_pattern("share/locale", tuple(languages), "openswitcher.mo", recursive=True)

# GTK
add_gtk()
add_icon_packs()
add_themes()

# SSL
add_ssl_certs()

# Locales
add_locales()

setup(
    name="openswitcher",
    author="Martijn Braam <martijn@brixit.nl>",
    version="0.6.0",
    options={
        "build_exe": dict(
            packages=["gi"] + plugin_packages,
            excludes=["pygtkcompat", "tkinter"],
            include_files=include_files,
            zip_include_packages=["*"],
            zip_exclude_packages=["pynicotine"]
        ),
        "bdist_msi": dict(
            all_users=True,
            install_icon=os.path.join(src_path, "windows/openswitcher.ico"),
            target_name="OpenSwitcher-0.6.0.msi",
            upgrade_code="{1ad65c6a-3492-4940-985f-04d11a28095e}"
        )
    },
    executables=[
        Executable(
            script=os.path.join(src_path, "gtk_switcher/switcher-control"),
            target_name="OpenSwitcher",
            base=gui_base,
            icon=os.path.join(src_path, "windows/openswitcher.ico"),
            shortcut_name="OpenSwitcher",
            shortcut_dir="StartMenuFolder"
        )
    ],
)
