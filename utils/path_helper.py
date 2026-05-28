import sys
import os


# def resource_path(relative_path):
#     """
#     Priority:
#     1. External folder beside EXE
#     2. PyInstaller bundled files
#     3. Dev project root
#     """
#
#     # 1️⃣ External config beside EXE
#     exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else None
#     if exe_dir:
#         external_path = os.path.join(exe_dir, relative_path)
#         if os.path.exists(external_path):
#             return external_path
#
#     # 2️⃣ Bundled inside EXE
#     if hasattr(sys, "_MEIPASS"):
#         return os.path.join(sys._MEIPASS, relative_path)
#
#     # 3️⃣ Dev mode
#     project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
#     return os.path.join(project_root, relative_path)



def resource_path(relative_path):

    # Folder beside EXE
    base_path = os.path.dirname(sys.executable)

    external_path = os.path.join(base_path, relative_path)

    # Prefer external editable file
    if os.path.exists(external_path):
        return external_path

    # Fallback to bundled PyInstaller file
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)