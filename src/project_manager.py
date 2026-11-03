import os
import sys
import json
import shutil
import string
import hashlib
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional


PROJECT_MARKER_FILENAME = "coralscop_project.json"
PROJECT_SCHEMA = "coralscop-bioclip-project"
PROJECT_VERSION = 1

PROJECT_SUBDIRS = {
    "raw_images": "raw_images",
    "filtered_images": "filtered_images",
    "polygons": "polygons",
    "exports": "exports",
}

VALID_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def compute_file_sha256(filepath: str, chunk_size: int = 65536) -> str:
    """
    Computes the full 64-character lowercase SHA-256 hex digest of a file on disk.
    Used to bind polygon/classification files strictly to the exact raw image content,
    so replacing an image with a different file of the same name is immediately detected.
    """
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            block = f.read(chunk_size)
            if not block:
                break
            sha.update(block)
    return sha.hexdigest()


def _norm_abs_path(path: str) -> str:
    return os.path.normcase(os.path.realpath(os.path.abspath(path)))


def is_inside_repository(target_path: str, repo_base_dir: str) -> bool:
    """
    Returns True if `target_path` is equal to or nested inside `repo_base_dir`.
    User projects must be created outside the repository directory.
    """
    try:
        norm_target = _norm_abs_path(target_path)
        norm_repo = _norm_abs_path(repo_base_dir)
        common = os.path.commonpath([norm_target, norm_repo])
        return common == norm_repo
    except ValueError:
        # Different Windows drives (e.g., C:\ vs D:\) -> definitely outside repository
        return False


def get_sample_images_info(repo_images_dir: str) -> Dict[str, Any]:
    """
    Inspects the built-in suggestion/test photo set shipped inside the repository's `images/` folder.
    """
    if not os.path.isdir(repo_images_dir):
        return {"count": 0, "total_mb": 0.0, "filenames": []}

    filenames: List[str] = []
    total_bytes = 0
    for fname in sorted(os.listdir(repo_images_dir)):
        ext = os.path.splitext(fname)[1].lower()
        if ext in VALID_IMAGE_EXTENSIONS:
            fpath = os.path.join(repo_images_dir, fname)
            if os.path.isfile(fpath):
                filenames.append(fname)
                total_bytes += os.path.getsize(fpath)

    return {
        "count": len(filenames),
        "total_mb": round(total_bytes / (1024 * 1024), 2),
        "filenames": filenames,
    }


def read_project_marker(root_path: str) -> Optional[Dict[str, Any]]:
    """
    Reads and validates `<root_path>/coralscop_project.json`.
    Returns the marker dictionary if valid, or None if missing/invalid.
    """
    if not root_path or not os.path.isdir(root_path):
        return None
    marker_path = os.path.join(root_path, PROJECT_MARKER_FILENAME)
    if not os.path.isfile(marker_path):
        return None
    try:
        with open(marker_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or data.get("schema") != PROJECT_SCHEMA:
            return None
        return data
    except Exception:
        return None


def _ensure_project_subdirs(root_path: str, marker_data: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    dirs_cfg = (marker_data or {}).get("directories") or PROJECT_SUBDIRS
    resolved = {}
    for key, default_rel in PROJECT_SUBDIRS.items():
        rel_name = os.path.basename(str(dirs_cfg.get(key, default_rel)).strip("/\\")) or default_rel
        abs_sub = os.path.join(root_path, rel_name)
        os.makedirs(abs_sub, exist_ok=True)
        resolved[key] = abs_sub
    return resolved


def load_projects_registry(registry_path: str) -> Dict[str, Any]:
    if not os.path.isfile(registry_path):
        return {"active_project_root": None, "recent_projects": []}
    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"active_project_root": None, "recent_projects": []}
        data.setdefault("active_project_root", None)
        if not isinstance(data.get("recent_projects"), list):
            data["recent_projects"] = []
        return data
    except Exception:
        return {"active_project_root": None, "recent_projects": []}


def save_projects_registry(registry_data: Dict[str, Any], registry_path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(registry_path)), exist_ok=True)
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry_data, f, ensure_ascii=False, indent=2)


def _upsert_recent_project(
    registry_data: Dict[str, Any],
    root_path: str,
    name: str,
    created_at: str = "",
) -> None:
    abs_root = os.path.abspath(root_path)
    norm_root = _norm_abs_path(abs_root)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    kept: List[Dict[str, Any]] = []
    existing_created = created_at or now_str
    for item in registry_data.get("recent_projects", []):
        p = item.get("root_path")
        if not p:
            continue
        if _norm_abs_path(p) == norm_root:
            existing_created = created_at or item.get("created_at") or now_str
            continue
        kept.append(item)

    kept.insert(
        0,
        {
            "name": name,
            "root_path": abs_root,
            "created_at": existing_created,
            "last_opened": now_str,
        },
    )
    registry_data["recent_projects"] = kept[:25]
    registry_data["active_project_root"] = abs_root


def copy_sample_images_to_dir(repo_images_dir: str, dest_raw_dir: str) -> List[str]:
    """
    Copies the default test suggestion images from `repo_images_dir` into `dest_raw_dir`
    (skipping filenames that already exist in `dest_raw_dir`).
    """
    os.makedirs(dest_raw_dir, exist_ok=True)
    copied: List[str] = []
    if not os.path.isdir(repo_images_dir):
        return copied

    for fname in sorted(os.listdir(repo_images_dir)):
        ext = os.path.splitext(fname)[1].lower()
        if ext not in VALID_IMAGE_EXTENSIONS:
            continue
        src = os.path.join(repo_images_dir, fname)
        dst = os.path.join(dest_raw_dir, fname)
        if os.path.isfile(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)
            copied.append(fname)
    return copied


def create_project(
    root_path: str,
    name: str,
    repo_base_dir: str,
    repo_images_dir: str,
    registry_path: str,
    copy_sample_images: bool = False,
) -> Dict[str, Any]:
    """
    Creates a new local CoralSCOP + BioCLIP 2.5 project outside the repository folder:
      <root_path>/
        ├── coralscop_project.json
        ├── raw_images/
        ├── filtered_images/
        ├── polygons/
        └── exports/
    """
    clean_root = (root_path or "").strip()
    if not clean_root:
        raise ValueError("Informe ou selecione uma pasta local para servir como raiz do projeto.")

    abs_root = os.path.abspath(os.path.expanduser(clean_root))
    if is_inside_repository(abs_root, repo_base_dir):
        raise ValueError(
            f"A pasta do projeto deve ficar FORA da pasta do repositório ({repo_base_dir}). "
            f"Escolha outro local no computador (ex.: Documentos ou outro diretório em disco)."
        )

    existing_marker = read_project_marker(abs_root)
    if existing_marker is not None:
        raise ValueError(
            f"A pasta '{abs_root}' já possui um projeto CoralSCOP ('{existing_marker.get('name', 'Sem nome')}'). "
            f"Use a aba 'Abrir Projeto Existente' para carregá-lo."
        )

    try:
        os.makedirs(abs_root, exist_ok=True)
    except Exception as e:
        raise ValueError(f"Não foi possível criar a pasta raiz '{abs_root}': {e}")

    project_name = (name or "").strip() or os.path.basename(abs_root.rstrip("/\\")) or "Novo Projeto Coral"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    marker_data = {
        "schema": PROJECT_SCHEMA,
        "version": PROJECT_VERSION,
        "name": project_name,
        "created_at": now_str,
        "updated_at": now_str,
        "directories": dict(PROJECT_SUBDIRS),
    }

    subdirs = _ensure_project_subdirs(abs_root, marker_data)
    marker_path = os.path.join(abs_root, PROJECT_MARKER_FILENAME)
    with open(marker_path, "w", encoding="utf-8") as f:
        json.dump(marker_data, f, ensure_ascii=False, indent=2)

    copied_files: List[str] = []
    if copy_sample_images:
        copied_files = copy_sample_images_to_dir(repo_images_dir, subdirs["raw_images"])

    reg = load_projects_registry(registry_path)
    _upsert_recent_project(reg, abs_root, project_name, created_at=now_str)
    save_projects_registry(reg, registry_path)

    return {
        "name": project_name,
        "root_path": abs_root,
        "marker_file": marker_path,
        "directories": subdirs,
        "copied_sample_count": len(copied_files),
        "copied_samples": copied_files,
    }


def open_existing_project(
    root_path: str,
    repo_base_dir: str,
    registry_path: str,
) -> Dict[str, Any]:
    """
    Validates `<root_path>/coralscop_project.json` and activates the project.
    """
    clean_root = (root_path or "").strip()
    if not clean_root:
        raise ValueError("Informe ou selecione a pasta raiz do projeto existente.")

    abs_root = os.path.abspath(os.path.expanduser(clean_root))
    if not os.path.isdir(abs_root):
        raise ValueError(f"A pasta '{abs_root}' não existe neste computador.")

    if is_inside_repository(abs_root, repo_base_dir):
        raise ValueError(
            "Projetos de trabalho devem ficar fora da pasta do repositório. "
            "Para usar as fotos padrão do repositório, selecione o 'Conjunto Padrão de Teste (Demo)'."
        )

    marker = read_project_marker(abs_root)
    if marker is None:
        raise ValueError(
            f"A pasta '{abs_root}' não foi reconhecida como um projeto válido "
            f"(arquivo identificador '{PROJECT_MARKER_FILENAME}' ausente ou inválido)."
        )

    subdirs = _ensure_project_subdirs(abs_root, marker)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    marker["updated_at"] = now_str
    marker_path = os.path.join(abs_root, PROJECT_MARKER_FILENAME)
    try:
        with open(marker_path, "w", encoding="utf-8") as f:
            json.dump(marker, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    project_name = marker.get("name") or os.path.basename(abs_root.rstrip("/\\")) or "Projeto Coral"
    reg = load_projects_registry(registry_path)
    _upsert_recent_project(reg, abs_root, project_name, created_at=marker.get("created_at", now_str))
    save_projects_registry(reg, registry_path)

    return {
        "name": project_name,
        "root_path": abs_root,
        "marker_file": marker_path,
        "directories": subdirs,
    }


def activate_demo_workspace(registry_path: str) -> None:
    """
    Switches active workspace back to the built-in Demo/Test Suggestion Set.
    """
    reg = load_projects_registry(registry_path)
    reg["active_project_root"] = None
    save_projects_registry(reg, registry_path)


def remove_recent_project(root_path: str, registry_path: str) -> Dict[str, Any]:
    """
    Removes a project path from the recent projects list without deleting any user files on disk.
    """
    reg = load_projects_registry(registry_path)
    target_norm = _norm_abs_path(root_path) if root_path else ""
    reg["recent_projects"] = [
        item for item in reg.get("recent_projects", [])
        if item.get("root_path") and _norm_abs_path(item["root_path"]) != target_norm
    ]
    if reg.get("active_project_root") and _norm_abs_path(reg["active_project_root"]) == target_norm:
        reg["active_project_root"] = None
    save_projects_registry(reg, registry_path)
    return reg


def resolve_active_workspace(
    repo_base_dir: str,
    repo_images_dir: str,
    repo_output_dir: str,
    default_memory_path: str,
    registry_path: str,
) -> Dict[str, Any]:
    """
    Resolves the currently active workspace (either an external user Project with a valid
    `coralscop_project.json` marker, or the built-in Demo/Test Suggestion Set).
    """
    reg = load_projects_registry(registry_path)
    active_root = reg.get("active_project_root")

    if active_root:
        marker = read_project_marker(active_root)
        if marker is not None and not is_inside_repository(active_root, repo_base_dir):
            subdirs = _ensure_project_subdirs(active_root, marker)
            return {
                "mode": "project",
                "is_demo": False,
                "name": marker.get("name") or os.path.basename(active_root.rstrip("/\\")),
                "root_path": os.path.abspath(active_root),
                "marker_file": os.path.join(os.path.abspath(active_root), PROJECT_MARKER_FILENAME),
                "created_at": marker.get("created_at", ""),
                "raw_images_dir": subdirs["raw_images"],
                "filtered_dir": subdirs["filtered_images"],
                "polygons_dir": subdirs["polygons"],
                "exports_dir": subdirs["exports"],
                "legacy_output_dir": None,
                "fewshot_memory_path": os.path.join(subdirs["polygons"], "bioclip_fewshot_memory.json"),
            }
        else:
            # Active project folder was moved/unmounted -> fall back cleanly to Demo mode
            reg["active_project_root"] = None
            save_projects_registry(reg, registry_path)

    os.makedirs(repo_images_dir, exist_ok=True)
    os.makedirs(repo_output_dir, exist_ok=True)
    return {
        "mode": "demo",
        "is_demo": True,
        "name": "Conjunto Padrão de Teste (Demo)",
        "root_path": None,
        "marker_file": None,
        "created_at": "",
        "raw_images_dir": repo_images_dir,
        "filtered_dir": repo_output_dir,
        "polygons_dir": repo_output_dir,
        "exports_dir": repo_output_dir,
        "legacy_output_dir": repo_output_dir,
        "fewshot_memory_path": default_memory_path,
    }


def list_recent_projects_with_status(registry_path: str, repo_base_dir: str) -> List[Dict[str, Any]]:
    reg = load_projects_registry(registry_path)
    active_norm = _norm_abs_path(reg["active_project_root"]) if reg.get("active_project_root") else ""
    out: List[Dict[str, Any]] = []

    for item in reg.get("recent_projects", []):
        rpath = item.get("root_path")
        if not rpath:
            continue
        marker = read_project_marker(rpath)
        valid = bool(marker is not None and not is_inside_repository(rpath, repo_base_dir))
        raw_count = 0
        if valid:
            raw_dir = os.path.join(rpath, (marker.get("directories") or {}).get("raw_images", "raw_images"))
            if os.path.isdir(raw_dir):
                raw_count = sum(
                    1 for f in os.listdir(raw_dir)
                    if os.path.splitext(f)[1].lower() in VALID_IMAGE_EXTENSIONS
                )
        out.append({
            "name": (marker or {}).get("name") or item.get("name") or os.path.basename(rpath.rstrip("/\\")),
            "root_path": rpath,
            "last_opened": item.get("last_opened", ""),
            "created_at": (marker or {}).get("created_at") or item.get("created_at", ""),
            "exists": os.path.isdir(rpath),
            "valid_marker": valid,
            "is_active": bool(active_norm and _norm_abs_path(rpath) == active_norm),
            "image_count": raw_count,
        })
    return out


def get_default_projects_parent_dir(repo_base_dir: str) -> str:
    """
    Suggests a sensible default parent directory outside the repository (e.g., parent of repo or ~/Documents).
    """
    repo_parent = os.path.dirname(os.path.abspath(repo_base_dir))
    if repo_parent and not is_inside_repository(repo_parent, repo_base_dir) and os.path.isdir(repo_parent):
        return repo_parent
    home = os.path.expanduser("~")
    docs = os.path.join(home, "Documents")
    return docs if os.path.isdir(docs) else home


def browse_local_directories(
    target_path: Optional[str],
    repo_base_dir: str,
    create_subfolder: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Lists local drives / folders for the built-in web directory picker so users can easily
    navigate, inspect existing `coralscop_project.json` folders, and create new project folders.
    """
    if not target_path or str(target_path).strip() in ("", "__DRIVES__"):
        if os.name == "nt":
            drives = []
            for letter in string.ascii_uppercase:
                drv = f"{letter}:\\"
                if os.path.exists(drv):
                    drives.append({
                        "name": f"Disco Local ({letter}:)",
                        "path": drv,
                        "is_project": False,
                        "is_inside_repo": False,
                    })
            return {
                "current_path": "",
                "parent_path": None,
                "is_drives_root": True,
                "is_current_project": False,
                "is_current_inside_repo": False,
                "SuggestedParent": get_default_projects_parent_dir(repo_base_dir),
                "entries": drives,
            }
        target_path = os.path.expanduser("~")

    abs_path = os.path.abspath(os.path.expanduser(str(target_path).strip()))
    if not os.path.isdir(abs_path):
        raise ValueError(f"Diretório não encontrado: '{abs_path}'")

    if create_subfolder:
        clean_sub = os.path.basename(create_subfolder.strip().strip("/\\"))
        if not clean_sub:
            raise ValueError("Nome de nova pasta inválido.")
        new_dir = os.path.join(abs_path, clean_sub)
        if is_inside_repository(new_dir, repo_base_dir):
            raise ValueError("Não é permitido criar pastas de projeto dentro do repositório.")
        os.makedirs(new_dir, exist_ok=True)
        abs_path = new_dir

    parent = os.path.dirname(abs_path)
    if parent == abs_path:
        parent_out = "__DRIVES__" if os.name == "nt" else None
    else:
        parent_out = parent

    entries: List[Dict[str, Any]] = []
    try:
        with os.scandir(abs_path) as it:
            subdirs = [e for e in it if e.is_dir(follow_symlinks=False) and not e.name.startswith("$")]
        subdirs.sort(key=lambda e: (e.name.startswith("."), e.name.lower()))
        for entry in subdirs[:250]:
            if entry.name.startswith("."):
                continue
            full_sub = os.path.abspath(entry.path)
            marker = read_project_marker(full_sub)
            entries.append({
                "name": entry.name,
                "path": full_sub,
                "is_project": marker is not None,
                "project_name": (marker or {}).get("name", ""),
                "is_inside_repo": is_inside_repository(full_sub, repo_base_dir),
            })
    except PermissionError:
        pass

    curr_marker = read_project_marker(abs_path)
    return {
        "current_path": abs_path,
        "parent_path": parent_out,
        "is_drives_root": False,
        "is_current_project": curr_marker is not None,
        "current_project_name": (curr_marker or {}).get("name", ""),
        "is_current_inside_repo": is_inside_repository(abs_path, repo_base_dir),
        "entries": entries,
    }


def pick_folder_native_dialog(
    initial_dir: Optional[str] = None,
    title: str = "Selecione a pasta raiz do projeto CoralSCOP",
) -> Optional[str]:
    """
    Launches a native Windows OS folder selection dialog in an isolated subprocess
    (so tkinter never conflicts with Flask worker threads and always pops up topmost in front of Opera/Chrome).
    Returns the chosen absolute path, or None if the user cancelled.
    """
    start_dir = initial_dir if (initial_dir and os.path.isdir(initial_dir)) else os.path.expanduser("~")
    script = (
        "import sys, os, tkinter as tk\n"
        "from tkinter import filedialog\n"
        "root = tk.Tk()\n"
        "root.withdraw()\n"
        "try:\n"
        "    root.attributes('-topmost', True)\n"
        "    root.lift()\n"
        "    root.focus_force()\n"
        "except Exception:\n"
        "    pass\n"
        "chosen = filedialog.askdirectory(parent=root, initialdir=sys.argv[1], title=sys.argv[2], mustexist=False)\n"
        "root.destroy()\n"
        "if chosen:\n"
        "    sys.stdout.buffer.write(chosen.encode('utf-8'))\n"
    )
    try:
        proc = subprocess.run(
            [sys.executable, "-c", script, start_dir, title],
            capture_output=True,
            timeout=180,
        )
        if proc.returncode == 0:
            raw = proc.stdout.decode("utf-8", errors="replace").strip()
            if raw and os.path.isdir(raw):
                return os.path.abspath(raw)
    except Exception:
        pass

    # Fallback to Windows PowerShell FolderBrowserDialog
    if os.name == "nt":
        try:
            ps_script = (
                "$ErrorActionPreference = 'Stop'; "
                "[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; "
                "$f = New-Object System.Windows.Forms.FolderBrowserDialog; "
                f"$f.Description = '{title}'; "
                "$f.ShowNewFolderButton = $true; "
                f"$f.SelectedPath = '{start_dir}'; "
                "if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { "
                "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
                "[Console]::WriteLine($f.SelectedPath); "
                "}"
            )
            proc_ps = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True,
                timeout=180,
            )
            if proc_ps.returncode == 0:
                raw_ps = proc_ps.stdout.decode("utf-8", errors="replace").strip()
                if raw_ps and os.path.isdir(raw_ps):
                    return os.path.abspath(raw_ps)
        except Exception:
            pass

    return None
