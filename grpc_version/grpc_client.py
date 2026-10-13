import sys

import grpc

import inventory_pb2
import inventory_pb2_grpc

ADDRESS = "127.0.0.1:50051"
DEADLINE_SECONDS = 2


def main():
    if len(sys.argv) != 3:
        print("usage: python grpc_client.py <item_id> <quantity>")
        sys.exit(1)

    request = inventory_pb2.CheckRequest(item_id=sys.argv[1], quantity=int(sys.argv[2]))
    print("request:")
    print(f"  item_id: {request.item_id}")
    print(f"  quantity: {request.quantity}")

    with grpc.insecure_channel(ADDRESS) as channel:
        stub = inventory_pb2_grpc.InventoryServiceStub(channel)
        try:
            response = stub.CheckInventory(request, timeout=DEADLINE_SECONDS)
        except grpc.RpcError as e:
            print("error:")
            print(f"  status: {e.code().name}")
            print(f"  details: {e.details()}")
            sys.exit(1)

    print("response:")
    print(f"  item_id: {response.item_id}")
    print(f"  requested: {response.requested}")
    print(f"  in_stock: {response.in_stock}")
    print(f"  available: {response.available}")


if __name__ == "__main__":
    main()
