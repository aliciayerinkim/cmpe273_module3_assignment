import os
import time
from concurrent import futures

import grpc

import inventory_pb2
import inventory_pb2_grpc

ADDRESS = "127.0.0.1:50051"

STOCK = {"apple": 10, "banana": 5, "laptop": 2}

# set this env var to make the service slow (used for the deadline demo)
DELAY_SECONDS = float(os.environ.get("INVENTORY_DELAY_SECONDS", "0"))


class InventoryService(inventory_pb2_grpc.InventoryServiceServicer):
    def CheckInventory(self, request, context):
        if DELAY_SECONDS > 0:
            time.sleep(DELAY_SECONDS)

        if not request.item_id:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "item_id is required")
        if request.quantity <= 0:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "quantity must be a positive integer")

        if request.item_id not in STOCK:
            context.abort(grpc.StatusCode.NOT_FOUND, f"item '{request.item_id}' not found")

        in_stock = STOCK[request.item_id]
        if request.quantity > in_stock:
            context.abort(
                grpc.StatusCode.FAILED_PRECONDITION,
                f"not enough stock for '{request.item_id}': requested {request.quantity}, in stock {in_stock}",
            )

        return inventory_pb2.CheckResponse(
            item_id=request.item_id,
            requested=request.quantity,
            in_stock=in_stock,
            available=True,
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inventory_pb2_grpc.add_InventoryServiceServicer_to_server(InventoryService(), server)
    server.add_insecure_port(ADDRESS)
    server.start()
    print(f"inventory gRPC server listening on {ADDRESS} (delay={DELAY_SECONDS}s)", flush=True)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
