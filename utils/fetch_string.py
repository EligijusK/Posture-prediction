def fetch_string(buffer):
    _str = ""

    char = buffer.read(1)
    while char != b"\x00":
        _str += char.decode("utf-8")
        char = buffer.read(1)

    return _str
