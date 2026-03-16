from __future__ import annotations

try:
    import mido
except Exception as exc:  # pragma: no cover
    mido = None
    _IMPORT_ERR = exc
else:
    _IMPORT_ERR = None


class MidiOutput:
    def __init__(self, port):
        self.port = port

    def send(self, msg) -> None:
        self.port.send(msg)

    def close(self) -> None:
        self.port.close()


class DummyOutput:
    def __init__(self):
        self.sent = []

    def send(self, msg) -> None:
        self.sent.append(msg)

    def close(self) -> None:
        pass


def open_output(port_name: str = "MidiAgentOut", virtual: bool = True):
    if mido is None:
        print(f"[midi_io] mido unavailable, fallback to DummyOutput: {_IMPORT_ERR}")
        return DummyOutput()

    if virtual:
        try:
            port = mido.open_output(port_name, virtual=True)
            print(f"[midi_io] opened virtual port: {port_name}")
            return MidiOutput(port)
        except Exception as exc:
            print(f"[midi_io] virtual port not available: {exc}")

    try:
        names = mido.get_output_names()
    except Exception as exc:
        print(f"[midi_io] failed to enumerate ports, fallback DummyOutput: {exc}")
        return DummyOutput()
    if not names:
        print("[midi_io] no MIDI output ports, fallback DummyOutput")
        return DummyOutput()

    try:
        port = mido.open_output(names[0])
    except Exception:
        return DummyOutput()
    print(f"[midi_io] opened physical port: {names[0]}")
    return MidiOutput(port)
