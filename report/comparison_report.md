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

Not applicable. The provided repository did not include tests/coap/test_proxy.py, therefore CoAP–HTTP proxy mapping could not be evaluated.

> Run `pytest tests/coap/test_proxy.py -v -s` and record the observed HTTP headers.

| HTTP Header            | CoAP Option | Your Observed Value |
| ---------------------- | ----------- | ------------------- |
| Content-Type           |             |                     |
| Cache-Control: max-age |             |                     |
| ETag                   |             |                     |
| Location               |             |                     |

---

## 5.3 Protocol Selection Recommendation

_(500–700 words. Justify each recommendation with specific technical evidence from your implementation and packet captures.)_

### Data Path Recommendations

| Data Path                                          | Recommended Protocol | Justification                                                                                                                                |
| -------------------------------------------------- | -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Sensor → Cloud (high frequency, <100 ms latency)   | MQTT QoS 0           | Lowest latency (0.9 ms average) and minimal protocol overhead. Suitable for continuous telemetry where occasional packet loss is acceptable. |
| Actuator commands (safety-critical, exactly-once)  | MQTT QoS 2           | Guarantees exactly-once delivery through a four-step handshake, preventing duplicate or lost commands.                                       |
| Backend service-to-service routing                 | AMQP                 | Provides advanced routing, queues, exchanges, and reliable message delivery between backend services.                                        |
| OTA firmware delivery to constrained MCU (Class 2) | CoAP                 | Lightweight protocol designed for constrained devices and supports efficient block-wise transfers for large firmware images.                 |

### Detailed Justification

Different IoT communication paths have different requirements regarding reliability, latency, bandwidth consumption, and implementation complexity. Based on the implementation, testing, and packet analysis performed in this assignment, different protocols are better suited for different use cases.

For high-frequency sensor-to-cloud telemetry, MQTT QoS 0 is the most appropriate choice. The QoS comparison experiment showed an average latency of approximately 0.9 ms, which was the lowest among all tested MQTT QoS levels. QoS 0 minimizes protocol overhead because it does not require acknowledgments or retransmissions. In many industrial monitoring applications, occasional packet loss is acceptable because new sensor readings are continuously generated. The packet capture also showed a relatively simple frame structure, reducing bandwidth consumption.

For safety-critical actuator commands, MQTT QoS 2 is the preferred option. Although the measured latency increased to approximately 3.3 ms, QoS 2 guarantees exactly-once delivery. Packet captures demonstrated the additional PUBREC, PUBREL, and PUBCOMP handshake messages that eliminate duplicate delivery. This additional overhead is justified when controlling industrial equipment, where duplicate commands could create safety risks or unintended system behavior.

Backend service-to-service communication is best handled by AMQP. Although the AMQP analysis section was excluded in this assignment version, AMQP is specifically designed for enterprise messaging environments. It supports exchanges, routing keys, queues, acknowledgments, and flexible message routing. These features make it more suitable than MQTT for complex backend workflows where messages may need to be routed to multiple services or stored temporarily.

For over-the-air (OTA) firmware delivery to constrained microcontrollers, CoAP is the recommended protocol. During packet analysis, CoAP demonstrated efficient operation using compact binary headers and support for block-wise transfers. The CoAP Observe mechanism also provides an efficient method for receiving updates without repeatedly polling the server. The protocol is specifically optimized for resource-constrained devices with limited memory and bandwidth. Compared to HTTP, CoAP significantly reduces packet overhead while preserving reliability through confirmable (CON) messages.

The packet captures further highlighted the differences between the protocols. MQTT packets included protocol-specific fields such as topic names, packet identifiers, and QoS information. CoAP packets used compact headers, tokens, and options, resulting in significantly smaller message sizes. These observations support selecting MQTT for telemetry streaming and CoAP for constrained-device communication.

Overall, the results demonstrate that no single protocol is optimal for all IoT scenarios. MQTT provides excellent telemetry performance, CoAP offers lightweight communication for constrained devices, and AMQP provides powerful backend messaging capabilities. Selecting the appropriate protocol depends on the reliability, latency, and resource requirements of the specific communication path.

---

## 5.4 Reflection

### Technical Challenge

One of the main technical challenges encountered during this assignment was configuring and troubleshooting the MQTT and CoAP environments. Initially, some tests failed because services were not running or the correct Python virtual environment was not activated. Additionally, packet captures required multiple attempts to ensure that the correct protocol traffic was recorded. These issues were resolved by carefully verifying service status, activating the virtual environment correctly, and repeating packet captures until the required protocol frames were visible in Wireshark.

### Most Surprising Protocol Difference

The most surprising difference observed during packet analysis was the amount of additional communication required by higher MQTT QoS levels. Although QoS 0, QoS 1, and QoS 2 all delivered messages successfully in the experiment, QoS 2 required significantly more protocol exchanges. The packet captures clearly showed additional acknowledgment packets that were not present in QoS 0 communication. This demonstrated how stronger delivery guarantees directly increase protocol overhead and latency.

### Most Complex Protocol to Implement

The most complex protocol to implement correctly was CoAP. Unlike MQTT, which follows a publish-subscribe model and provides relatively straightforward client APIs, CoAP required understanding confirmable messages, acknowledgments, tokens, Observe relationships, and resource-oriented communication. The Observe functionality was particularly challenging because it involved maintaining subscriptions and processing asynchronous notifications. Understanding the relationship between requests, acknowledgments, and notifications required careful packet analysis and testing. However, implementing these features provided valuable insight into how lightweight IoT protocols achieve reliable communication while minimizing network overhead.

---

_Module 1 Assignment — Real-Time Data Analytics for IoT_
