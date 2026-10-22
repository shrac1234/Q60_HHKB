#!/usr/bin/env python3
"""Print an HTML file to PDF with headless Firefox over Marionette (no extra packages).

  python3 print/firefox_pdf.py print/q60-hhkb-print.html q60-hhkb-guide.pdf
"""
import base64, json, os, socket, subprocess, sys, tempfile, time

PORT = 2829


def recv(sock):
    buf = b""
    while b":" not in buf:
        buf += sock.recv(1)
    size, rest = buf.split(b":", 1)
    size = int(size)
    while len(rest) < size:
        rest += sock.recv(size - len(rest))
    return json.loads(rest)


class Marionette:
    def __init__(self, sock):
        self.sock, self.n = sock, 0
        recv(sock)  # greeting

    def call(self, name, params=None):
        self.n += 1
        msg = json.dumps([0, self.n, name, params or {}]).encode()
        self.sock.sendall(str(len(msg)).encode() + b":" + msg)
        _, _, err, result = recv(self.sock)
        if err:
            raise RuntimeError(f"{name}: {err}")
        return result


def main(src, dst):
    profile = tempfile.mkdtemp(prefix="ffpdf-")
    with open(os.path.join(profile, "user.js"), "w") as f:
        f.write(f'user_pref("marionette.port", {PORT});\n')
    ff = subprocess.Popen(["firefox", "--headless", "--marionette", "--no-remote",
                           "--profile", profile],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                sock = socket.create_connection(("127.0.0.1", PORT))
                break
            except OSError:
                time.sleep(0.5)
        else:
            sys.exit("Firefox did not open Marionette")
        m = Marionette(sock)
        m.call("WebDriver:NewSession", {"capabilities": {}})
        m.call("WebDriver:Navigate", {"url": "file://" + os.path.abspath(src)})
        m.call("WebDriver:ExecuteAsyncScript", {
            "script": "const done = arguments[0]; document.fonts.ready.then(() => setTimeout(done, 500));",
            "args": []})
        pdf = m.call("WebDriver:Print", {
            "background": True, "shrinkToFit": False, "orientation": "portrait",
            "page": {"width": 21.0, "height": 29.7},
            "margin": {"top": 0, "bottom": 0, "left": 0, "right": 0}})["value"]
        with open(dst, "wb") as f:
            f.write(base64.b64decode(pdf))
        print("wrote", dst)
        m.call("WebDriver:DeleteSession")
    finally:
        ff.terminate()
        ff.wait(timeout=10)


if __name__ == "__main__":
    main(*sys.argv[1:3])
