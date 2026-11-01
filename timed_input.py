import os
import sys
import time


def timed_input(prompt: str, deadline: float) -> str | None:
    """Lit une ligne jusqu'à `deadline` (time.monotonic). Retourne None si le temps est écoulé."""
    if not sys.stdin.isatty():
        return input(prompt)

    def render(buf: str) -> None:
        left = max(0, int(deadline - time.monotonic() + 0.99))
        sys.stdout.write(f"\r\033[K⏱  {left:2d}s  {prompt}{buf}")
        sys.stdout.flush()

    buf = ""
    if os.name == "nt":
        import msvcrt
        os.system("")
        while time.monotonic() < deadline:
            render(buf)
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in "\r\n":
                    print()
                    return buf
                buf = buf[:-1] if ch == "\b" else buf + ch
            else:
                time.sleep(0.05)
    else:
        import select
        import termios
        import tty
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            while time.monotonic() < deadline:
                render(buf)
                ready, _, _ = select.select([sys.stdin], [], [], 0.1)
                if ready:
                    ch = sys.stdin.read(1)
                    if ch in "\r\n":
                        print()
                        return buf
                    buf = buf[:-1] if ch in "\x7f\b" else buf + ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    print()
    return None