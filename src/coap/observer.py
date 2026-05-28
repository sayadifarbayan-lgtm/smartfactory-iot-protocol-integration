import asyncio
import json
import logging
from datetime import datetime, timezone

import aiocoap
from aiocoap import Message, Code

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s"
)

log = logging.getLogger(__name__)

SERVER_BASE = "coap://localhost"
OBSERVE_DURATION = 60


class FactoryObserver:

    def __init__(self):
        self._ctx = None
        self._last_seq = {}
        self._stale_count = {}

    async def start(self) -> None:
        self._ctx = await aiocoap.Context.create_client_context()

    async def stop(self) -> None:
        if self._ctx:
            await self._ctx.shutdown()

    async def observe_resource(self, uri: str) -> None:

        request = Message(code=Code.GET, uri=uri)
        request.opt.observe = 0

        pr = self._ctx.request(request)

        try:
            first_response = await pr.response
            self._handle_notification(uri, first_response)

            async def observation_loop():
                async for response in pr.observation:
                    self._handle_notification(uri, response)

            task = asyncio.create_task(observation_loop())

            await asyncio.sleep(OBSERVE_DURATION)

            pr.observation.cancel()
            task.cancel()

            log.info(f"Deregistered from {uri}")

        except asyncio.CancelledError:
            log.info(f"Observation cancelled for {uri}")

    def _handle_notification(self, uri: str, response: Message) -> None:

        seq = response.opt.observe

        if seq is None:
            seq = -1

        last = self._last_seq.get(uri)

        if last is not None and seq <= last:
            self._stale_count[uri] = (
                self._stale_count.get(uri, 0) + 1
            )

            log.warning(
                f"STALE notification on {uri}: "
                f"seq={seq} <= last={last}"
            )
            return

        self._last_seq[uri] = seq

        try:
            payload = json.loads(response.payload.decode("utf-8"))
        except Exception:
            log.error(f"Could not parse payload from {uri}")
            return

        value = payload.get("value")
        unit = payload.get("unit", "")
        timestamp = datetime.now(timezone.utc).isoformat()

        log.info(
            f"[OBSERVE] {uri}  "
            f"seq={seq}  "
            f"val={value} {unit}  "
            f"@ {timestamp}"
        )

    async def fetch_manifest(self) -> None:

        uri = f"{SERVER_BASE}/factory/manifest"

        request = Message(code=Code.GET, uri=uri)

        response = await self._ctx.request(request).response

        payload = response.payload

        log.info(f"Manifest received: {len(payload)} bytes")

        try:
            data = json.loads(payload.decode("utf-8"))
            firmware_entries = data.get("firmware", [])
            count = len(firmware_entries)
        except Exception:
            count = 0

        log.info(f"Firmware entries in manifest: {count}")
        log.info("Block2 transfer complete")

    async def run(self) -> None:

        await self.start()

        try:
            uri1 = f"{SERVER_BASE}/factory/line1/temperature"
            uri2 = f"{SERVER_BASE}/factory/line2/temperature"

            await asyncio.gather(
                self.observe_resource(uri1),
                self.observe_resource(uri2)
            )

            await self.fetch_manifest()

            print("── CoAP Observer Summary ──────────────────────")

            for uri in [uri1, uri2]:
                count = self._stale_count.get(uri, 0)

                print(
                    f"{uri:<55} "
                    f"stale notifications: {count}"
                )

            print("───────────────────────────────────────────────")

        finally:
            await self.stop()


if __name__ == "__main__":
    observer = FactoryObserver()
    asyncio.run(observer.run())