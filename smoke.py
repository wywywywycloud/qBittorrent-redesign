import base64
import hashlib
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import Request, urlopen

exe, label = Path(sys.argv[1]).resolve(), sys.argv[2]
with tempfile.TemporaryDirectory(prefix="qbt-gui-") as tmp:
    profile = Path(tmp)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha512", os.urandom(20), salt, 100000)
    password = ":".join(base64.b64encode(piece).decode() for piece in (salt, digest))
    config = profile / "qBittorrent/config/qBittorrent.conf"
    config.parent.mkdir(parents=True)
    config.write_text(f"[WebUI]\nEnabled=true\nAddress=127.0.0.1\nPort={port}\nLocalHostAuth=false\nPassword_PBKDF2={password}\n[BitTorrent]\nSession\\DHTEnabled=false\nSession\\LSDEnabled=false\n[Network]\nPortForwardingEnabled=false\n[Preferences]\nAdvanced\\updateCheck=false\n")
    api = f"http://127.0.0.1:{port}/api/v2/app/"
    app = subprocess.Popen([str(exe), "--confirm-legal-notice", "--profile="+tmp])
    try:
        for _ in range(100):
            if app.poll() is not None:
                raise RuntimeError(f"GUI exited early with {app.returncode}")
            try:
                with urlopen(api+"version", timeout=1) as response:
                    print(label, "Qt GUI ready", response.read().decode(), flush=True)
                break
            except OSError:
                time.sleep(.25)
        else:
            raise RuntimeError("GUI did not become ready")
        with urlopen(Request(api+"shutdown",data=b""),timeout=3):
            pass
        assert app.wait(timeout=15)==0
    finally:
        if app.poll() is None:
            app.terminate()
            app.wait(timeout=10)
