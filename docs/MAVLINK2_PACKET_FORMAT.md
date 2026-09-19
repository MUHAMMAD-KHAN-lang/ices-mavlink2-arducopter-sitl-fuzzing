# MAVLink 2 packet model used here

For a MAVLink 2 structured frame, the bytes are arranged as:

```text
FD | LEN | INC_FLAGS | COMP_FLAGS | SEQ | SYSID | COMPID | MSGID(3) | PAYLOAD | CRC(2)
```

Key points used by the scripts:

* `FD` is the MAVLink 2 magic byte.
* `LEN` is the payload length, one byte (`0..255`).
* `SEQ` is an 8-bit sequence number.
* `SYSID` is fixed at `255` in the fuzzing scripts.
* `COMPID` is fixed at `0` in the fuzzing scripts.
* MAVLink 2 uses a three-byte message ID field.
* The CRC is calculated over the MAVLink 2 header (without magic) plus payload and the message-specific CRC extra.

The paper's original MAVLink 1 framing used `FE`. That distinction is intentional: this repository tests the current MAVLink 2 wire format rather than pretending to reproduce the older MAVLink 1 frame format.
