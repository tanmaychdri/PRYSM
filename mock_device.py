import asyncio
import base64
import json

import websockets

from prysm.mobile.crypto import MobileCrypto


async def run_mock_device():
    uri = "ws://localhost:9754"

    print("Connecting to PRYSM Desktop...")
    try:
        async with websockets.connect(uri) as ws:
            print("Connected. Type pairing code from desktop:")
            code = input("Code: ").strip()

            # Generate local keypair
            priv, pub = MobileCrypto.generate_keypair()
            pub_b64 = base64.b64encode(pub).decode("utf-8")

            # Request pair
            await ws.send(
                json.dumps(
                    {
                        "type": "pair_request",
                        "code": code,
                        "public_key": pub_b64,
                        "device_info": {
                            "device_name": "Mock Android Phone",
                            "platform": "android",
                        },
                    }
                )
            )

            resp = json.loads(await ws.recv())
            if resp.get("type") == "error":
                print(f"Error: {resp}")
                return

            desktop_pub = base64.b64decode(resp["public_key"])
            device_id = resp["device_id"]
            shared_secret = MobileCrypto.derive_shared_secret(priv, desktop_pub)

            print(f"Paired! Device ID: {device_id}")

            # Now authenticate
            await ws.send(json.dumps({"type": "auth", "device_id": device_id}))

            auth_resp = json.loads(await ws.recv())
            if auth_resp.get("type") == "auth_success":
                print("Authenticated successfully!")

            # Listen for requests
            print("Listening for encrypted requests from desktop...")
            async for raw_msg in ws:
                payload = json.loads(raw_msg)
                if payload.get("type") == "encrypted":
                    dec = MobileCrypto.decrypt_payload(
                        shared_secret, payload["nonce"], payload["ciphertext"]
                    )
                    req = json.loads(dec)
                    print(f"\n[RECEIVED REQUEST] {req}")

                    # Send response back
                    res = {
                        "version": 1,
                        "type": "response",
                        "request_id": req["request_id"],
                        "success": True,
                        "payload": {"status": f"Handled {req['action']} successfully"},
                    }

                    enc_res = MobileCrypto.encrypt_payload(
                        shared_secret, json.dumps(res).encode("utf-8")
                    )
                    await ws.send(json.dumps({"type": "encrypted", **enc_res}))
    except Exception as e:
        print(f"Disconnected: {e}")


if __name__ == "__main__":
    asyncio.run(run_mock_device())
