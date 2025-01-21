import os


def get_next_line(fd) -> bytes:
    ln = b""
    while 1:
        x = os.read(fd, 1)
        if b"\n" in x:
            break
        ln += x
    return ln
