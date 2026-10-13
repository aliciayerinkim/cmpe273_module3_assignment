import logging

import requests
from flask import Flask, jsonify, request

INVENTORY_URL = "http://127.0.0.1:8001/inventory/check"
INVENTORY_TIMEOUT_SECONDS = 2

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("order-rest")

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "order-rest"})


@app.post("/orders")
def create_order():
    data = request.get_json(silent=True) or {}
    payload = {"item_id": data.get("item_id"), "quantity": data.get("quantity")}

    try:
        resp = requests.post(INVENTORY_URL, json=payload, timeout=INVENTORY_TIMEOUT_SECONDS)
        body = resp.json()
    # ConnectionError goes first: a connect timeout also means we could not reach it
    except requests.exceptions.ConnectionError:
        log.error("inventory service unreachable at %s", INVENTORY_URL)
        return jsonify({"error": "inventory service unavailable"}), 503
    except requests.exceptions.Timeout:
        log.error("inventory call timed out after %ss, payload=%s", INVENTORY_TIMEOUT_SECONDS, payload)
        return jsonify({"error": "inventory service timed out"}), 504
    except (requests.exceptions.RequestException, ValueError) as e:
        log.error("inventory call failed: %s", e)
        return jsonify({"error": "bad response from inventory service"}), 502

    if resp.status_code == 200:
        log.info("order accepted, payload=%s", payload)
        return jsonify({
            "status": "accepted",
            "item_id": body["item_id"],
            "quantity": body["requested"],
        }), 201

    if resp.status_code in (400, 404, 409):
        message = body.get("error", "order rejected")
        log.warning("order rejected with %s: %s", resp.status_code, message)
        return jsonify({"error": message}), resp.status_code

    log.error("unexpected inventory status %s", resp.status_code)
    return jsonify({"error": "bad response from inventory service"}), 502


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
