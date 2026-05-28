# Module 1 Assignment — Protocol Comparison Report

**Student Name:** Bayan Sayyadifar
**Student ID:** 101035809
**Date:** 2026-05-28

---

## 5.1 QoS Comparison Results Table

> Run `pytest tests/mqtt/test_qos_loss.py -v -s` and paste the output table here.

| Protocol / QoS      | Sent | Received | Lost (%) | Duplicates | Avg Latency (ms) |
| ------------------- | ---- | -------- | -------- | ---------- | ---------------- |
| MQTT QoS 0          | 100  | 100      | 0.0%     | 0          | 0.9              |
| MQTT QoS 1          | 100  | 100      | 0.0%     | 0          | 1.0              |
| MQTT QoS 2          | 100  | 100      | 0.0%     | 0          | 3.3              |
| CoAP NON            | N/A  | N/A      | N/A      | N/A        | N/A              |
| CoAP CON            | N/A  | N/A      | N/A      | N/A        | N/A              |
| AMQP (confirms off) | N/A  | N/A      | N/A      | N/A        | N/A              |

**Analysis Questions:**

1. **Why does QoS 0 lose messages while QoS 1 and 2 do not?** _(2–3 sentences)_

   > QoS 0 does not use acknowledgments or retransmissions, so messages may be lost if packets are dropped during transmission. QoS 1 and QoS 2 include acknowledgment and retry mechanisms, which ensure reliable delivery even when packet loss occurs.

2. **QoS 1 may show duplicates. Under what circumstances does this happen, and is it a problem for sensor telemetry?** _(2–3 sentences)_

   > QoS 1 may produce duplicate messages if the sender retransmits a packet before receiving the PUBACK acknowledgment. For sensor telemetry, occasional duplicates are usually acceptable because telemetry systems can often tolerate repeated measurements.

3. **QoS 2 has higher latency than QoS 1. What causes this, and when is the trade-off worth it?** _(2–3 sentences)_

   > QoS 2 requires a four-step handshake between the sender and receiver, which increases protocol overhead and latency. The trade-off is worth it for critical applications where duplicate delivery is unacceptable, such as financial transactions or safety-critical actuator commands.

---

## 5.2 CoAP–HTTP Proxy Mapping

This section was not evaluated because the provided repository did not include tests/coap/test_proxy.py. When I attempted to run the proxy test, pytest returned that the file or directory was not found. Therefore, no HTTP response headers were available to map to CoAP options.

AMQP was also excluded based on the assignment instruction to ignore AMQP for this version.

## 5.3 Protocol Selection Recommendation

_(500–700 words. Justify each recommendation with specific technical evidence from your implementation and packet captures.)_

### Data Path Recommendations

| Data Path                                          | Recommended Protocol         | Justification                                                                                                                                                         |
| -------------------------------------------------- | ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Sensor → Cloud (high frequency, <100 ms latency)   | MQTT QoS 0 or QoS 1          | MQTT had very low latency in my test results. QoS 0 had the lowest average latency at 0.9 ms, while QoS 1 was only slightly higher at 1.0 ms and adds acknowledgment. |
| Actuator commands (safety-critical, exactly-once)  | MQTT QoS 2                   | QoS 2 had higher latency at 3.3 ms, but it provides the strongest delivery guarantee using the PUBREC, PUBREL, and PUBCOMP exchange.                                  |
| Backend service-to-service routing                 | Not evaluated / AMQP ignored | AMQP would normally be suitable for backend routing, but it was not implemented or analyzed because the assignment instruction said to ignore AMQP.                   |
| OTA firmware delivery to constrained MCU (Class 2) | CoAP                         | CoAP is lightweight and supports block-wise transfer, which fits constrained devices and larger payloads such as firmware manifests.                                  |

### Detailed Justification

Based on my implementation and packet captures, MQTT is the best fit for the high-frequency sensor telemetry part of this system. In the QoS experiment, MQTT QoS 0 delivered 100 out of 100 messages with an average latency of 0.9 ms. QoS 1 also delivered 100 out of 100 messages with an average latency of 1.0 ms. Since the difference was very small, I would choose QoS 0 for non-critical high-frequency readings where the newest value matters more than every single individual message. However, for temperature data that may trigger alerts, QoS 1 is a safer choice because it still keeps latency low while adding acknowledgment through PUBACK.

For actuator commands, I would choose MQTT QoS 2. In my results, QoS 2 had the highest latency at 3.3 ms, but the extra overhead is reasonable for commands that should not be lost or duplicated. In Wireshark, QoS 2 traffic showed the extra handshake messages such as PUBREC, PUBREL, and PUBCOMP. This makes the protocol slower than QoS 0 and QoS 1, but it provides stronger delivery semantics. For a cooling fan or another safety-related actuator, reliability is more important than saving a few milliseconds.

For backend service-to-service routing, I would normally consider AMQP because it supports exchanges, queues, routing keys, acknowledgments, and durable messaging. However, AMQP was not implemented in this assignment because the instruction said to ignore it. Therefore, I did not use AMQP packet captures or test results as evidence. Within the implemented scope, MQTT topic routing already worked well for organizing telemetry by production line and sensor type, such as `factory/line1/temperature`.

For OTA firmware delivery to a constrained MCU, I would choose CoAP. In my CoAP implementation, the server exposed resources such as `/factory/line1/temperature` and `/factory/manifest`, and the observer client received live temperature updates. CoAP also handled the large firmware manifest response, which was around 19 KB in my run, using block-wise transfer. This is important because constrained devices often cannot receive large payloads in one packet. CoAP’s compact binary header, token matching, confirmable messages, and Observe option make it suitable for resource-constrained IoT devices.

Overall, my recommendation is to use MQTT for live telemetry, MQTT QoS 2 for critical actuator commands, and CoAP for constrained-device resource access and firmware delivery. AMQP was not evaluated because it was excluded from this assignment version.

---

## 5.4 Reflection

### Technical Challenge

One technical challenge I experienced was getting the environment and tests to work correctly on Windows. At first, some commands did not run because the virtual environment was not activated, and PowerShell blocked script execution. I fixed this by using `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` before activating `.venv`. I also ran into CoAP issues related to the loopback address and port binding. The CoAP server worked manually, but the tests initially failed until I adjusted the binding and event loop setup. After that, the CoAP tests passed successfully.

### Most Surprising Protocol Difference

The most surprising difference I observed was how much the protocol behavior changed depending on reliability level. MQTT QoS 0 was very simple and fast, while QoS 2 required several extra packets to complete one delivery. In Wireshark, I could clearly see the difference between a normal PUBLISH/PUBACK exchange and the longer QoS 2 flow with PUBREC, PUBREL, and PUBCOMP. This made the trade-off between latency and reliability much more obvious than just reading about QoS levels.

### Most Complex Protocol to Implement

The most complex protocol for me was CoAP. MQTT was easier to understand because the publisher and subscriber model was straightforward: publish to topics and subscribe with wildcards. CoAP required more attention to request/response behavior, tokens, confirmable messages, Observe notifications, and block-wise transfer. The observer client was especially tricky because it had to receive updates asynchronously, track sequence numbers, deregister after 60 seconds, and then fetch the manifest. Once I captured the packets in Wireshark, the relationship between GET requests, ACK responses, Observe sequence numbers, and payloads became clearer.

---

_Module 1 Assignment — Real-Time Data Analytics for IoT_
