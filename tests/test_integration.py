#!/usr/bin/env python3
"""Exercise real tmux input on isolated sockets; never switch the real IME."""
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

PROJECT = Path(__file__).resolve().parents[1]
TMUX = shutil.which("tmux")


def run(*args, **kwargs):
    return subprocess.run(args, text=True, capture_output=True, check=True, **kwargs)


def wait_for(predicate, message):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.03)
    raise AssertionError(message)


class Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not TMUX:
            raise unittest.SkipTest("tmux is required")
        run(str(PROJECT / "build.sh"))

    def test_cli_and_staged_install(self):
        binary = str(PROJECT / "build/tmux-ime")
        original = run(binary).stdout.strip()
        self.assertTrue(original)
        self.assertIn("com.apple.keylayout.ABC\t", run(binary, "--list").stdout)
        invalid = subprocess.run([binary, "com.example.invalid"], capture_output=True)
        self.assertEqual(invalid.returncode, 1)
        self.assertEqual(run(binary).stdout.strip(), original)
        self.assertEqual(subprocess.run([binary, "--unknown"], capture_output=True).returncode, 2)
        with tempfile.TemporaryDirectory(prefix="ime staging ") as stage:
            env = dict(os.environ, TMUX_IME_DESTDIR=stage)
            run(str(PROJECT / "install.sh"), "--prefix", "C-a", env=env)
            config = Path(stage) / ".config/tmux-ime/tmux.conf"
            self.assertIn("root C-a", config.read_text())
            run(str(PROJECT / "install.sh"), "--prefix", "C-b", env=env)
            self.assertIn("root C-b", config.read_text())
            self.assertTrue(list(config.parent.glob("tmux.conf.bak.*")))
            self.assertTrue(os.access(Path(stage) / ".local/bin/tmux-ime", os.X_OK))

    def exercise_prefix(self, prefix):
        with tempfile.TemporaryDirectory(prefix="ime bindings ") as work:
            work = Path(work)
            suffix = f"{os.getpid()}-{prefix}"
            inner = [TMUX, "-L", f"ime-inner-{suffix}", "-f", "/dev/null"]
            outer = [TMUX, "-L", f"ime-outer-{suffix}", "-f", "/dev/null"]

            def inside(*args):
                return run(*inner, *args).stdout.strip()

            def press(*keys):
                run(*outer, "send-keys", *keys)

            outcome = work / "outcome"
            outcome.write_text("0")
            helper = work / "helper"
            helper.write_text("#!/bin/sh\nsleep 0.08\nexit \"$(cat " +
                              shlex.quote(str(outcome)) + ")\"\n")
            helper.chmod(0o755)
            template = (PROJECT / f"examples/tmux-{prefix}.conf").read_text()
            template = template.replace('"$HOME/.local/bin/tmux-ime" com.apple.keylayout.ABC',
                                        f'"{helper}"')
            config = work / "tmux.conf"
            config.write_text(template)
            reader = work / "reader.py"
            reader.write_text("import os, tty\ntty.setraw(0)\nwhile True:\n"
                              "    data = os.read(0, 1)\n"
                              "    if not data: break\n"
                              "    os.write(1, data.hex().encode() + bytes([13, 10]))\n")
            command = shlex.join([sys.executable, "-u", str(reader)])
            try:
                inside("new-session", "-d", "-s", "test", "-x", "80", "-y", "24", command)
                inside("set-option", "-g", "default-shell", "/bin/sh")
                inside("source-file", str(config))
                inside("source-file", str(config))  # Reapplying is harmless.
                inside("bind-key", "x", "set-option", "-g", "@probe", "yes")
                run(*outer, "new-session", "-d", "-s", "outer", "-x", "80", "-y", "24",
                    shlex.join(inner + ["attach-session", "-t", "test"]))
                wait_for(lambda: bool(inside("list-clients", "-F", "#{client_name}")),
                         "test client did not attach")
                client = inside("list-clients", "-F", "#{client_name}")

                def table():
                    return inside("display-message", "-p", "-c", client, "#{client_key_table}")

                def probe():
                    inside("set-option", "-g", "@probe", "no")
                    press(prefix, "x")  # Same input batch, while helper deliberately waits.
                    wait_for(lambda: inside("show-option", "-gv", "@probe") == "yes",
                             "prefix command was lost")
                    self.assertEqual(table(), "root")

                probe()
                press(prefix)
                wait_for(lambda: table() == "prefix", "prefix table was not entered")
                press(prefix)
                byte = "01" if prefix == "C-a" else "02"
                wait_for(lambda: byte in inside("capture-pane", "-p"),
                         "double prefix was not delivered to the program")
                self.assertEqual(inside("capture-pane", "-p").split().count(byte), 1)

                for mode in ("emacs", "vi"):
                    inside("set-window-option", "mode-keys", mode)
                    inside("copy-mode")
                    probe()
                    inside("send-keys", "-X", "cancel")

                inside("split-window", "-h", command)
                inside("bind-key", "h", "select-pane", "-L")
                press(prefix, "h")
                wait_for(lambda: inside("display-message", "-p", "#{pane_index}") == "0",
                         "pane movement failed")
                outcome.write_text("1")
                probe()  # Failure must not block entry into the prefix table.
                helper.unlink()
                probe()  # Neither may a missing executable.
            finally:
                for server in (outer, inner):
                    subprocess.run(server + ["kill-server"], capture_output=True)

    def test_ctrl_a(self):
        self.exercise_prefix("C-a")

    def test_ctrl_b(self):
        self.exercise_prefix("C-b")


if __name__ == "__main__":
    unittest.main(verbosity=2)
