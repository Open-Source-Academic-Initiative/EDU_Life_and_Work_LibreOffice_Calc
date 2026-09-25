"""Helpers to drive a real LibreOffice instance through UNO.

Used by capture_screenshots.py (real UI screenshots) and
make_practice_files.py (downloadable .ods exercises).

LibreOffice runs with a throwaway user profile (never your personal one),
the Spanish UI and the X11 backend, so windows can be captured with
ImageMagick's `import`. Requirements (Fedora package names):
    libreoffice-calc libreoffice-langpack-es python3-libreoffice
    ImageMagick wmctrl
On Wayland desktops the windows are rendered through XWayland; they will
briefly appear on screen while the capture runs.
"""

import os
import subprocess
import sys
import tempfile
import threading
import time

try:
    import uno
    from com.sun.star.beans import PropertyValue
except ImportError:  # pragma: no cover - depends on the system python
    sys.exit("Python-UNO not found. Install python3-libreoffice (Fedora) "
             "or python3-uno (Debian/Ubuntu) and run with the system python3.")

PORT = 2099
UI_LOCALE = "es_CO"  # decides the UI language, currency and ; separator


def props(**kwargs):
    """Build a tuple of PropertyValue from keyword arguments."""
    out = []
    for name, value in kwargs.items():
        p = PropertyValue()
        p.Name, p.Value = name, value
        out.append(p)
    return tuple(out)


def url(path):
    return uno.systemPathToFileUrl(os.path.abspath(path))


class Office:
    """A running soffice process plus its UNO desktop."""

    def __init__(self, profile_dir=None, display=None):
        self.profile_dir = profile_dir or tempfile.mkdtemp(prefix="lo-profile-")
        self.display = display or os.environ.get("DISPLAY", ":0")
        self.proc = None
        self.ctx = None
        self.desktop = None

    # ---------------------------------------------------------------- start
    def start(self):
        env = dict(os.environ)
        env.update({
            "DISPLAY": self.display,
            "SAL_USE_VCLPLUGIN": "gtk3",
            "GDK_BACKEND": "x11",
            "LANG": f"{UI_LOCALE}.UTF-8",
            "LC_ALL": f"{UI_LOCALE}.UTF-8",
            "LANGUAGE": "es",
        })
        env.pop("WAYLAND_DISPLAY", None)
        self.proc = subprocess.Popen(
            ["soffice", "--norestore", "--nologo", "--nodefault",
             f"-env:UserInstallation={url(self.profile_dir)}",
             f"--accept=socket,host=127.0.0.1,port={PORT};urp;"],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        local = uno.getComponentContext()
        resolver = local.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", local)
        for _ in range(60):
            try:
                self.ctx = resolver.resolve(
                    f"uno:socket,host=127.0.0.1,port={PORT};urp;"
                    "StarOffice.ComponentContext")
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError("Could not connect to soffice")
        smgr = self.ctx.ServiceManager
        self.desktop = smgr.createInstanceWithContext(
            "com.sun.star.frame.Desktop", self.ctx)
        self.dispatcher = smgr.createInstanceWithContext(
            "com.sun.star.frame.DispatchHelper", self.ctx)
        self._quiet_profile()
        return self

    def _quiet_profile(self):
        """Turn off first-run noise (tip of the day, infobars, autocomplete)."""
        settings = {
            "/org.openoffice.Office.Common/Misc": {"ShowTipOfTheDay": False},
            "/org.openoffice.Setup/Product": {"LastTimeGetInvolvedShown": 2**40,
                                              "LastTimeDonateShown": 2**40},
            "/org.openoffice.Office.Calc/Input": {"AutoInput": False},
            "/org.openoffice.Office.Linguistic/SpellChecking": {"IsSpellAuto": False},
        }
        provider = self.ctx.ServiceManager.createInstanceWithContext(
            "com.sun.star.configuration.ConfigurationProvider", self.ctx)
        for node, values in settings.items():
            try:
                access = provider.createInstanceWithArguments(
                    "com.sun.star.configuration.ConfigurationUpdateAccess",
                    props(nodepath=node))
                for k, v in values.items():
                    try:
                        access.setPropertyValue(k, v)
                    except Exception:
                        pass
                access.commitChanges()
            except Exception:
                pass

    def stop(self):
        try:
            self.desktop.terminate()
        except Exception:
            pass
        if self.proc:
            try:
                self.proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    # ------------------------------------------------------------ documents
    def new_calc(self, hidden=False):
        return self.desktop.loadComponentFromURL(
            "private:factory/scalc", "_blank", 0, props(Hidden=hidden))

    def open(self, path, hidden=False):
        return self.desktop.loadComponentFromURL(
            url(path), "_blank", 0, props(Hidden=hidden))

    def dispatch(self, doc, command, **args):
        frame = doc.CurrentController.Frame
        return self.dispatcher.executeDispatch(frame, command, "", 0, props(**args))

    def dispatch_async(self, doc, command, **args):
        """Fire a command that opens a modal dialog without blocking us."""
        t = threading.Thread(target=self.dispatch, args=(doc, command),
                             kwargs=args, daemon=True)
        t.start()
        return t


# ------------------------------------------------------------ window tools
def list_windows():
    out = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True).stdout
    wins = []
    for line in out.splitlines():
        parts = line.split(None, 3)
        if len(parts) == 4:
            wins.append((parts[0], parts[3]))
    return wins


def wait_window(match, timeout=15, exclude=()):
    """Return the X window id whose title contains `match`."""
    end = time.time() + timeout
    while time.time() < end:
        for wid, title in list_windows():
            if match in title and wid not in exclude:
                return wid
        time.sleep(0.3)
    raise TimeoutError(f"No window titled like {match!r}; "
                       f"open windows: {[t for _, t in list_windows()]}")


def place_window(wid, x, y, w, h):
    subprocess.run(["wmctrl", "-i", "-r", wid, "-b",
                    "remove,maximized_vert,maximized_horz"], check=False)
    time.sleep(0.3)
    subprocess.run(["wmctrl", "-i", "-r", wid, "-e", f"0,{x},{y},{w},{h}"],
                   check=False)


def close_window(wid):
    subprocess.run(["wmctrl", "-i", "-c", wid], check=False)


def grab(wid, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    subprocess.run(["import", "-window", wid, path], check=True)
    return path
