"""
dwsim_bridge.py - load the DWSIM 10 engine into Python (pythonnet + .NET 10).

DWSIM 10.x is a .NET 10 application (not .NET Framework), so pythonnet must use
the "coreclr" runtime. We start the system-wide .NET 10 runtime with a small
runtimeconfig file, then tell .NET where to find DWSIM's assemblies.

Usage
-----
    from dwsim_bridge import load_dwsim
    dw = load_dwsim()                 # returns a namespace with the useful classes
    interf = dw.Automation3()
    sim = interf.CreateFlowsheet()

Set the DWSIM_DIR environment variable if DWSIM is installed elsewhere.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

DEFAULT_DWSIM_DIR = Path(os.environ.get(
    "DWSIM_DIR", Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "DWSIM"))

_LOADED: SimpleNamespace | None = None


def _write_runtimeconfig() -> Path:
    """Minimal runtimeconfig asking for .NET 10 (rolls forward to the latest patch)."""
    cfg = {"runtimeOptions": {
        "tfm": "net10.0",
        "framework": {"name": "Microsoft.NETCore.App", "version": "10.0.0"},
        "rollForward": "LatestPatch",
        "configProperties": {
            "System.Runtime.Serialization.EnableUnsafeBinaryFormatterSerialization": True},
    }}
    path = Path(tempfile.gettempdir()) / "methatwin_dwsim.runtimeconfig.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def load_dwsim(dwsim_dir: Path | str = DEFAULT_DWSIM_DIR) -> SimpleNamespace:
    """Start .NET, load DWSIM assemblies and return the key types (cached)."""
    global _LOADED
    if _LOADED is not None:
        return _LOADED
    dwsim_dir = Path(dwsim_dir)
    if not (dwsim_dir / "DWSIM.Automation.dll").exists():
        raise FileNotFoundError(f"DWSIM.Automation.dll not found in {dwsim_dir}")

    from clr_loader import get_coreclr
    from pythonnet import set_runtime
    set_runtime(get_coreclr(runtime_config=str(_write_runtimeconfig())))
    import clr  # noqa: E402  (must come after set_runtime)

    # Resolve DWSIM's dependencies from its install folder.
    import System  # type: ignore
    from System.Reflection import Assembly  # type: ignore

    def _resolve(_sender, args):
        name = args.Name.split(",")[0]
        candidate = dwsim_dir / f"{name}.dll"
        return Assembly.LoadFrom(str(candidate)) if candidate.exists() else None

    System.AppDomain.CurrentDomain.AssemblyResolve += _resolve
    sys.path.append(str(dwsim_dir))
    os.environ["PATH"] = str(dwsim_dir) + os.pathsep + os.environ.get("PATH", "")
    for asm in ["DWSIM.Interfaces", "DWSIM.GlobalSettings", "DWSIM.SharedClasses",
                "DWSIM.Thermodynamics", "DWSIM.UnitOperations", "DWSIM.FlowsheetBase",
                "DWSIM.Automation"]:
        clr.AddReference(str(dwsim_dir / f"{asm}.dll"))

    from DWSIM.Automation import Automation3  # type: ignore
    from DWSIM.Interfaces.Enums.GraphicObjects import ObjectType  # type: ignore
    from DWSIM.GlobalSettings import Settings  # type: ignore

    _LOADED = SimpleNamespace(Automation3=Automation3, ObjectType=ObjectType,
                              Settings=Settings, System=System, dir=dwsim_dir,
                              resolver=_resolve)
    return _LOADED
