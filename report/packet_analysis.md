# Module 1 Assignment — Packet Analysis

## Task 4: Wire-Level Protocol Annotation

---

## 4.2 MQTT Packet Annotations

### CONNECT Packet

| Field                       | Offset (bytes) | Raw Hex       | Decoded Value                |
| --------------------------- | -------------- | ------------- | ---------------------------- |
| Frame type + flags (byte 1) | 0              | `10`          | Type=CONNECT (1), flags=0000 |
| Remaining length (byte 2)   | 1              | `45`          | 69 bytes                     |
| Protocol name length        | 2–3            | `00 04`       | 4                            |
| Protocol name               | 4–7            | `4D 51 54 54` | "MQTT"                       |
| Protocol version            | 8              | `04`          | 4 (MQTT 3.1.1)               |
| Connect flags               | 9              | `c2`          | See breakdown below          |
| Keep-alive                  | 10–11          | `00 3c`       | 60 seconds                   |
| Client ID length            | 12–13          | `00 1b`       | 27                           |
| Client ID                   | 14–…           | `73 61 6d …`  | "smartfactory-publisher-001" |

**Connect Flags byte breakdown:**

| Bit | Name          | Value | Meaning  |
| --- | ------------- | ----- | -------- |
| 7   | Username flag | 1     | Enabled  |
| 6   | Password flag | 0     | Disabled |
| 5   | Will retain   | 0     | Disabled |
| 4–3 | Will QoS      | 00    | QoS 0    |
| 2   | Will flag     | 0     | Disabled |
| 1   | Clean session | 1     | Enabled  |
| 0   | Reserved      | 0     | —        |

---

### QoS 1 PUBLISH Packet

| Field               | Offset (bytes) | Raw Hex   | Decoded Value                        |
| ------------------- | -------------- | --------- | ------------------------------------ |
| Fixed header byte 1 | 0              | `32`      | Type=PUBLISH, DUP=0, QoS=1, RETAIN=0 |
| Remaining length    | 1              | `a1 01`   | 161 bytes                            |
| Topic length        | 2–3            | `00 19`   | 25                                   |
| Topic string        | 4–28           | `66 61 …` | "factory/line1/temperature"          |
| Packet Identifier   | 29-30          | `22 c6`   | 8902                                 |
| Payload             | 31-…           | `{…}`     | "JSON telemetry payload"             |

**Fixed header byte 1 bit expansion:**

| Bits 7–4 (packet type) | Bit 3 (DUP)         | Bits 2–1 (QoS) | Bit 0 (RETAIN)     |
| ---------------------- | ------------------- | -------------- | ------------------ |
| `0011` = PUBLISH (3)   | `0` = not duplicate | `01` = QoS 1   | `0` = not retained |

---

### PUBACK Packet

| Field             | Offset | Raw Hex | Decoded Value      |
| ----------------- | ------ | ------- | ------------------ |
| Fixed header      | 0      | `40`    | Type=PUBACK (0100) |
| Remaining length  | 1      | `02`    | 2 bytes            |
| Packet Identifier | 2–3    | `28 d4` | 10452              |

**Packet Identifier match:** PUBLISH PKT ID = 10452 ; PUBACK PKT ID = 10452 ; Match? Yes
The PUBACK packet confirms successful delivery of the QoS 1 PUBLISH message from the broker.

---

## 4.3 CoAP Packet Annotations

### CON GET Request

```
Bytes: __ __ __ __  __ __ __ __  __ ...
       [   Header   ] [  Token  ] [Options...]
```

| Field                  | Bits/Bytes | Raw Value | Decoded Value                       |
| ---------------------- | ---------- | --------- | ----------------------------------- |
| Version (bits 7–6)     | 2 bits     | `01`      | Version = 1                         |
| Type (bits 5–4)        | 2 bits     | `00`      | CON                                 |
| TKL (bits 3–0)         | 4 bits     | `4`       | Token length = 4                    |
| Code (byte 1)          | 8 bits     | `01`      | GET                                 |
| Message ID (bytes 2–3) | 16 bits    | `ab f9`   | 43769                               |
| Token (bytes 4–TKL+3)  | TKL bytes  | `d0 7f …` | 0xd07f                              |
| Option Delta           | 4 bits     | `b`       | Delta = 11, Option# = 11 (Uri-Path) |
| Option Length          | 4 bits     | `9`       | 9 bytes                             |
| Option Value           | 9 bytes    | `6c 6f …` | "localhost" (Uri-Path)              |

**Byte 0 full expansion:**

| Bit 7 | Bit 6 | Bit 5 | Bit 4 | Bit 3 | Bit 2 | Bit 1 | Bit 0 |
| ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| Ver   | Ver   | T     | T     | TKL   | TKL   | TKL   | TKL   |
| `0`   | `1`   | `0`   | `0`   | `0`   | `1`   | `0`   | `0`   |

---

### ACK 2.05 Content Response

| Field                  | Bytes | Raw Hex   | Decoded Value                                 |
| ---------------------- | ----- | --------- | --------------------------------------------- |
| Fixed header byte 0    | 0     | `64`      | Ver=01, T=10 (ACK), TKL=4                     |
| Code byte 1            | 1     | `45`      | 2.05 = Content                                |
| Message ID             | 2–3   | `ab f9`   | 43769 (matches request)                       |
| Token                  | 4–…   | `d0 7f …` | 0xd07f (matches request: yes)                 |
| Option: Content-Format | …     | `c1 32`   | Option# = 12, Value = 50 (application/json)   |
| Payload Marker         | …     | `FF`      | 0xFF                                          |
| Payload                | …     | `7b 22 …` | "{"line":"line1","sensor":"temperature",...}" |

---

### Observe Notification

| Field                  | Value        |
| ---------------------- | ------------ |
| Observe option number  | 6            |
| Observe sequence value | 12           |
| Message type           | CON          |
| Response code          | 2.05 Content |

---

## 4.4 AMQP Frame Annotations

AMQP analysis was omitted because the assignment specification marked AMQP as ignored for this assignment version.

### basic.publish Method Frame

```
Bytes: 01  00 01  00 00 00 NN  [payload]  CE
       [T] [Ch] [Payload Sz] [.........] [End]
```

| Field                 | Bytes | Raw Hex       | Decoded Value             |
| --------------------- | ----- | ------------- | ------------------------- |
| Frame Type            | 0     | `__`          | \_\_ = Method             |
| Channel               | 1–2   | `__ __`       | \_\_                      |
| Payload Size          | 3–6   | `__ __ __ __` | \_\_\_                    |
| Class ID              | 7–8   | `__ __`       | \_\_ = basic (60)         |
| Method ID             | 9–10  | `__ __`       | \_\_ = basic.publish (40) |
| Reserved (ticket)     | 11–12 | `00 00`       | —                         |
| Exchange name length  | 13    | `__`          | \_\_                      |
| Exchange name         | 14–…  | `__ …`        | "**\_\_\_**"              |
| Routing key length    | …     | `__`          | \_\_                      |
| Routing key           | …     | `__ …`        | "**\_\_\_**"              |
| Mandatory + Immediate | …     | `__`          | mandatory=_, immediate=_  |
| Frame End             | last  | `CE`          | 0xCE ✓                    |

---

### Content Header Frame

| Field               | Bytes | Raw Hex       | Decoded Value                    |
| ------------------- | ----- | ------------- | -------------------------------- |
| Frame Type          | 0     | `02`          | 2 = Header                       |
| Channel             | 1–2   | `__ __`       | \_\_                             |
| Payload Size        | 3–6   | `__ __ __ __` | \_\_\_                           |
| Class ID            | 7–8   | `__ __`       | 60 = basic                       |
| Weight              | 9–10  | `00 00`       | (unused)                         |
| Body Size           | 11–18 | `__ … __`     | \_\_\_ bytes                     |
| Property Flags      | 19–20 | `__ __`       | bits set: **\*\***\_\_\_**\*\*** |
| delivery_mode       | …     | `__`          | \_\_ (1=transient, 2=persistent) |
| content_type length | …     | `__`          | \_\_                             |
| content_type        | …     | `__ …`        | "**\_\_\_**"                     |
| Frame End           | last  | `CE`          | 0xCE ✓                           |

---

### Heartbeat Frame

| Field        | Value     |
| ------------ | --------- |
| Frame Type   | \_\_      |
| Channel      | \_\_      |
| Payload Size | \_\_      |
| Payload      | _(empty)_ |
| Frame End    | `CE`      |

**Why is the Heartbeat payload empty?**

> Heartbeat frames are used only to keep the AMQP connection alive and verify that both peers are still connected. Since no application data is transmitted, the payload is empty.

---

_Module 1 Assignment — Real-Time Data Analytics for IoT_
