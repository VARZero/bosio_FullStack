#!/usr/bin/env python3
"""Deploy and operate the complete BOSIO stack on a PYNQ-Z2."""

from __future__ import annotations

import argparse
import importlib.util
import os
import posixpath
import time
from pathlib import Path

import paramiko


ROOT = Path(__file__).resolve().parents[1]
WM = ROOT / "components" / "bosio_SphericalWM"
BOAYO = ROOT / "components" / "BoAYO" / "boayo"
REMOTE_ROOT = "/home/xilinx/bosio_v2"
REMOTE_APP = REMOTE_ROOT + "/boayo"
REMOTE_STAGE = "/tmp/bosio-fullstack-stage"
PYTHON = "/usr/local/share/pynq-venv/bin/python3"

WM_FILES = (
    "bosio_wm_daemon.py", "bosio_window_manager.py", "bosio_native_compositor.py",
    "bosio_mouse_input.py", "bosio_buttons.py", "bosio_driver_v2.py",
    "bosio_geometry_v2.py", "bosio_wm_client.py", "bosio-window-manager.service",
    "install_bosio_boot.sh", "native/bosio_compositor.cpp", "native/build_pynq.sh",
    "bitstream/bosio_output_disp.bit", "bitstream/bosio_output_disp.hwh",
)
def command(ssh, text, check=True):
    _, stdout, stderr = ssh.exec_command(text)
    output = stdout.read().decode(errors="replace").strip()
    error = stderr.read().decode(errors="replace").strip()
    status = stdout.channel.recv_exit_status()
    if check and status:
        raise RuntimeError(f"remote command failed ({status}): {error or output}")
    return output


def connect():
    host = os.environ.get("BOSIO_PYNQ_HOST", "192.168.2.99")
    user = os.environ.get("BOSIO_PYNQ_USER", "xilinx")
    password = os.environ.get("BOSIO_PYNQ_PASSWORD")
    options = {"username": user, "timeout": 10}
    if password:
        options["password"] = password
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, **options)
    return client


def require_sources():
    required = ([WM / "sw" / name for name in WM_FILES] +
                [BOAYO / name for name in boayo_deployer().FILES] +
                [BOAYO / "deploy_boayo.py"])
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("missing submodule files; run git submodule update --init --recursive: " + ", ".join(missing))


def boayo_deployer():
    """Use BoAYo's own deployment list, modes, symlinks, and service setup."""
    path = BOAYO / "deploy_boayo.py"
    if not path.is_file():
        raise RuntimeError("BoAYo submodule is missing; run git submodule update --init --recursive")
    spec = importlib.util.spec_from_file_location("fullstack_boayo_deploy", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def upload_files(ssh, source, destination, names):
    command(ssh, f"mkdir -p {destination}")
    sftp = ssh.open_sftp()
    try:
        for name in names:
            local = source / name
            remote = posixpath.join(destination, name.replace('\\', '/'))
            command(ssh, f"mkdir -p {posixpath.dirname(remote)}")
            sftp.put(str(local), remote)
    finally:
        sftp.close()


def deploy(ssh):
    require_sources()
    upload_files(ssh, WM / "sw", REMOTE_STAGE, WM_FILES)
    command(ssh, f"cd {REMOTE_STAGE} && chmod +x install_bosio_boot.sh && sudo -n sh install_bosio_boot.sh")
    boayo_deployer().deploy(ssh)
    print("BOSIO_STACK_DEPLOYED")


def start(ssh):
    boayo_deployer().start(ssh)
    for _ in range(15):
        time.sleep(1)
        launcher = command(
            ssh,
            f"cd {REMOTE_ROOT} && {PYTHON} -c \"from bosio_wm_client import BosioWMClient; "
            "c=BosioWMClient('stack-start'); s=c.get_state(); "
            "print(any(w['title']=='BoAYO Launcher' for w in s['windows'])); c.close()\"",
            check=False,
        )
        if launcher == "True":
            print("BOAYO_STARTED")
            return
    raise RuntimeError("BoAYo launcher window was not registered; inspect boayo-desktop.service")


def status(ssh):
    service = command(ssh, "systemctl is-active boayo-desktop.service", check=False)
    text = command(ssh, f"cd {REMOTE_ROOT} && {PYTHON} -c \"from bosio_wm_client import BosioWMClient; c=BosioWMClient('stack-status'); s=c.get_state(); o=s.get('output') or {{}}; print({{'compositor':s.get('compositor'),'boayo_service':'{service}','launcher_present':any(w['title']=='BoAYO Launcher' for w in s['windows']),'app_windows':sum(w['title']!='BoAYO Launcher' for w in s['windows']),'scene_valid':o.get('scene_valid'),'error':o.get('error'),'sensor_active':o.get('sensor_active'),'aa_enabled':o.get('aa_enabled'),'aa_strength':o.get('aa_strength'),'fclk0_mhz':o.get('fclk0_mhz')}}); c.close()\"")
    print(text)


def main():
    parser = argparse.ArgumentParser(description="BOSIO full-stack PYNQ-Z2 runner")
    parser.add_argument("action", choices=("deploy", "start", "status", "deploy-start"))
    args = parser.parse_args()
    ssh = connect()
    try:
        if args.action in ("deploy", "deploy-start"):
            deploy(ssh)
        if args.action in ("start", "deploy-start"):
            start(ssh)
        status(ssh)
    finally:
        ssh.close()


if __name__ == "__main__":
    main()
