import logging

import grpc
from flask import Flask, jsonify, request

import inventory_pb2
import inventory_pb2_grpc

INVENTORY_ADDRESS = "127.0.0.1:50051"
INVENTORY_DEADLINE_SECONDS = 2

GRPC_TO_HTTP = {
    grpc.StatusCode.INVALID_ARGUMENT: 400,
    grpc.StatusCode.NOT_FOUND: 404,
    grpc.StatusCode.FAILED_PRECONDITION: 409,
    grpc.StatusCode.DEADLINE_EXCEEDED: 504,
    grpc.StatusCode.UNAVAILABLE: 503,
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("order-grpc")

app = Flask(__name__)

channel = grpc.insecure_channel(INVENTORY_ADDRESS)
stub = inventory_pb2_grpc.InventoryServiceStub(channel)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "order-grpc"})


@app.post("/orders")
def create_order():
    data = request.get_json(silent=True) or {}
    item_id = data.get("item_id")
    quantity = data.get("quantity")

    # the proto message only takes a string and an int32, so check types first
    if not isinstance(item_id, str):
        return jsonify({"error": "item_id is required"}), 400
    if not isinstance(quantity, int) or isinstance(quantity, bool):
        return jsonify({"error": "quantity must be a positive integer"}), 400

    try:
        check = inventory_pb2.CheckRequest(item_id=item_id, quantity=quantity)
    except ValueError:
        # quantity does not fit in int32
        return jsonify({"error": "quantity is out of range"}), 400

    try:
        result = stub.CheckInventory(check, timeout=INVENTORY_DEADLINE_SECONDS)
    except grpc.RpcError as e:
        code = e.code()
        status = GRPC_TO_HTTP.get(code, 502)
        log.error("inventory gRPC call failed: %s (%s) -> HTTP %s", code.name, e.details(), status)
        return jsonify({"error": e.details(), "grpc_status": code.name}), status
    except Exception as e:
        log.error("inventory gRPC call failed: %s", e)
        return jsonify({"error": "bad response from inventory service"}), 502

    log.info("order accepted, item_id=%s quantity=%s", item_id, quantity)
    return jsonify({
        "status": "accepted",
        "item_id": result.item_id,
        "quantity": result.requested,
    }), 201


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8002)
