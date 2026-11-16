"""Time spent in desktop apps you add yourself (Windows only).

Every few seconds, checks which app window is in front. If it belongs to a
custom tool (for example ``Cursor.exe`` or ``Claude.exe``) and you've
touched the keyboard or mouse recently, that time is credited to the tool.
The window title is kept (on this PC only) so it can be matched to a job.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass


@dataclass
class Foreground:
    exe: str
    title: str
    idle_seconds: float


def sample() -> Foreground | None:
    if sys.platform != "win32":
        return None
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]

    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetLastInputInfo.argtypes = [ctypes.POINTER(LASTINPUTINFO)]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                    ctypes.POINTER(wintypes.DWORD)]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.GetTickCount64.restype = ctypes.c_ulonglong

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(max(1, length + 1))
    user32.GetWindowTextW(hwnd, buf, length + 1)
    title = buf.value

    exe = ""
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if handle:
        try:
            size = wintypes.DWORD(1024)
            path = ctypes.create_unicode_buffer(size.value)
            if kernel32.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(size)):
                exe = path.value.replace("\\", "/").split("/")[-1].lower()
        finally:
            kernel32.CloseHandle(handle)

    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(LASTINPUTINFO)
    idle = 0.0
    if user32.GetLastInputInfo(ctypes.byref(info)):
        now = kernel32.GetTickCount64() & 0xFFFFFFFF
        idle = ((now - info.dwTime) & 0xFFFFFFFF) / 1000.0
    return Foreground(exe=exe, title=title, idle_seconds=idle)


def chat_key(title: str) -> str:
    """Window titles become 'chats'. Drop the trailing app name to group better."""
    t = " ".join(title.split())[:120]
    for sep in (" - ", " — ", " | "):
        if sep in t:
            t = t.rsplit(sep, 1)[0]
            break
    return t or "(untitled window)"
