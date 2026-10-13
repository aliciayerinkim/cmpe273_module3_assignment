import os
import time

from flask import Flask, jsonify, request

app = Flask(__name__)

STOCK = {"apple": 10, "banana": 5, "laptop": 2}

# set this env var to make the service slow (used for the timeout demo)
DELAY_SECONDS = float(os.environ.get("INVENTORY_DELAY_SECONDS", "0"))


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "inventory-rest"})


@app.post("/inventory/check")
def check_inventory():
    if DELAY_SECONDS > 0:
        time.sleep(DELAY_SECONDS)

    data = request.get_json(silent=True) or {}
    item_id = data.get("item_id")
    quantity = data.get("quantity")

    if not isinstance(item_id, str) or not item_id:
        return jsonify({"error": "item_id is required"}), 400
    # bool is a subclass of int in Python, so reject it here
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        return jsonify({"error": "quantity must be a positive integer"}), 400

    if item_id not in STOCK:
        return jsonify({"error": f"item '{item_id}' not found"}), 404

    in_stock = STOCK[item_id]
    if quantity > in_stock:
        return jsonify({
            "error": f"not enough stock for '{item_id}': requested {quantity}, in stock {in_stock}",
            "item_id": item_id,
            "requested": quantity,
            "in_stock": in_stock,
            "available": False,
        }), 409

    return jsonify({
        "item_id": item_id,
        "requested": quantity,
        "in_stock": in_stock,
        "available": True,
    }), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8001)
