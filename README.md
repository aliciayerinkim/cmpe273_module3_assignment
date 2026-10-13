# cmpe273_module3_assignment

An Order Service asks an Inventory Service if an order can be filled. I built it with REST and gRPC.

| Service | File | Port |
| --- | --- | --- |
| REST Order | `rest/order_service.py` | 8000 |
| REST Inventory | `rest/inventory_service.py` | 8001 |
| gRPC Order | `grpc_version/order_service.py` | 8002 |
| gRPC Inventory | `grpc_version/inventory_server.py` | 50051 |

The REST timeout and the gRPC deadline are both 2 seconds.

## Setup

Tested with Python 3.11. Run all commands from the repo root.

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Each service needs its own terminal. In every new terminal, run `source .venv/Scripts/activate` first.

Make the gRPC code from the proto file:

```bash
python -m grpc_tools.protoc -I grpc_version --python_out=grpc_version --grpc_python_out=grpc_version grpc_version/inventory.proto
```

## Run the REST version

Terminal 1 (Inventory, port 8001):

```bash
python rest/inventory_service.py
```

Terminal 2 (Order, port 8000):

```bash
python rest/order_service.py
```

Terminal 3 (send an order):

```bash
curl -i -s -X POST http://127.0.0.1:8000/orders -H "Content-Type: application/json" -d '{"item_id": "apple", "quantity": 3}'
```

## Run the gRPC version

Terminal 1 (Inventory, port 50051):

```bash
python grpc_version/inventory_server.py
```

Terminal 2 (Order, port 8002):

```bash
python grpc_version/order_service.py
```

Terminal 3 (call gRPC directly then send an order):

```bash
python grpc_version/grpc_client.py apple 3
curl -i -s -X POST http://127.0.0.1:8002/orders -H "Content-Type: application/json" -d '{"item_id": "apple", "quantity": 3}'
```

## Add the delay

To make the Inventory Service slow, go to Terminal 1, press `Ctrl+C`, and start again with a delay. Do not stop the Order Service in Terminal 2.

REST version:

```bash
INVENTORY_DELAY_SECONDS=5 python rest/inventory_service.py
```

gRPC version:

```bash
INVENTORY_DELAY_SECONDS=5 python grpc_version/inventory_server.py
```

Send the order again from Terminal 3. To remove the delay, stop Terminal 1 again and start it with the normal command.

## Evidence

All outputs are copied from real runs of these commands.

### REST success

Terminal 1:

```bash
python rest/inventory_service.py
```

Terminal 2:

```bash
python rest/order_service.py
```

Terminal 3:

```
$ curl -i -s -X POST http://127.0.0.1:8000/orders -H "Content-Type: application/json" -d '{"item_id": "apple", "quantity": 3}'
HTTP/1.1 201 CREATED
Server: Werkzeug/3.1.9 Python/3.11.0
Date: Mon, 12 Oct 2026 07:27:08 GMT
Content-Type: application/json
Content-Length: 53
Connection: close

{"item_id":"apple","quantity":3,"status":"accepted"}
```

### REST unavailable item

Not enough stock gives 409. An unknown item gives 404.

Terminal 1:

```bash
python rest/inventory_service.py
```

Terminal 2:

```bash
python rest/order_service.py
```

Terminal 3:

```
$ curl -i -s -X POST http://127.0.0.1:8000/orders -H "Content-Type: application/json" -d '{"item_id": "laptop", "quantity": 5}'
HTTP/1.1 409 CONFLICT
Server: Werkzeug/3.1.9 Python/3.11.0
Date: Mon, 12 Oct 2026 07:27:09 GMT
Content-Type: application/json
Content-Length: 67
Connection: close

{"error":"not enough stock for 'laptop': requested 5, in stock 2"}


$ curl -i -s -X POST http://127.0.0.1:8000/orders -H "Content-Type: application/json" -d '{"item_id": "mango", "quantity": 1}'
HTTP/1.1 404 NOT FOUND
Server: Werkzeug/3.1.9 Python/3.11.0
Date: Mon, 12 Oct 2026 07:27:09 GMT
Content-Type: application/json
Content-Length: 35
Connection: close

{"error":"item 'mango' not found"}
```

### gRPC success

Terminal 1:

```bash
python grpc_version/inventory_server.py
```

Terminal 2:

```bash
python grpc_version/order_service.py
```

Terminal 3 (the first command calls the gRPC server directly, the second one goes through the Order Service):

```
$ .venv/Scripts/python.exe grpc_version/grpc_client.py apple 3
request:
  item_id: apple
  quantity: 3
response:
  item_id: apple
  requested: 3
  in_stock: 10
  available: True


$ curl -i -s -X POST http://127.0.0.1:8002/orders -H "Content-Type: application/json" -d '{"item_id": "apple", "quantity": 3}'
HTTP/1.1 201 CREATED
Server: Werkzeug/3.1.9 Python/3.11.0
Date: Mon, 12 Oct 2026 07:27:20 GMT
Content-Type: application/json
Content-Length: 53
Connection: close

{"item_id":"apple","quantity":3,"status":"accepted"}
```

### gRPC unavailable item

Not enough stock gives `FAILED_PRECONDITION` (409). An unknown item gives `NOT_FOUND` (404).

Terminal 1:

```bash
python grpc_version/inventory_server.py
```

Terminal 2:

```bash
python grpc_version/order_service.py
```

Terminal 3:

```
$ .venv/Scripts/python.exe grpc_version/grpc_client.py laptop 5
request:
  item_id: laptop
  quantity: 5
error:
  status: FAILED_PRECONDITION
  details: not enough stock for 'laptop': requested 5, in stock 2


$ .venv/Scripts/python.exe grpc_version/grpc_client.py mango 1
request:
  item_id: mango
  quantity: 1
error:
  status: NOT_FOUND
  details: item 'mango' not found


$ curl -i -s -X POST http://127.0.0.1:8002/orders -H "Content-Type: application/json" -d '{"item_id": "laptop", "quantity": 5}'
HTTP/1.1 409 CONFLICT
Server: Werkzeug/3.1.9 Python/3.11.0
Date: Mon, 12 Oct 2026 07:27:21 GMT
Content-Type: application/json
Content-Length: 103
Connection: close

{"error":"not enough stock for 'laptop': requested 5, in stock 2","grpc_status":"FAILED_PRECONDITION"}


$ curl -i -s -X POST http://127.0.0.1:8002/orders -H "Content-Type: application/json" -d '{"item_id": "mango", "quantity": 1}'
HTTP/1.1 404 NOT FOUND
Server: Werkzeug/3.1.9 Python/3.11.0
Date: Mon, 12 Oct 2026 07:27:21 GMT
Content-Type: application/json
Content-Length: 61
Connection: close

{"error":"item 'mango' not found","grpc_status":"NOT_FOUND"}
```

### REST timeout

The Inventory Service was set to wait 5 seconds before answering. The Order Service only waits 2 seconds (the timeout), so it stopped waiting and returned 504.

Terminal 1 (`Ctrl+C` then start with delay):

```bash
INVENTORY_DELAY_SECONDS=5 python rest/inventory_service.py
```

Terminal 2: Leave `python rest/order_service.py` running.

Terminal 3:

```
$ curl -i -s -X POST http://127.0.0.1:8000/orders -H "Content-Type: application/json" -d '{"item_id": "apple", "quantity": 3}' -w "\ntime_total: %{time_total}s\n"
HTTP/1.1 504 GATEWAY TIMEOUT
Server: Werkzeug/3.1.9 Python/3.11.0
Date: Mon, 12 Oct 2026 07:27:13 GMT
Content-Type: application/json
Content-Length: 40
Connection: close

{"error":"inventory service timed out"}

time_total: 2.046085s
```

Terminal 2 (Order Service prints this log):

```
2026-10-12 00:27:13,303 ERROR inventory call timed out after 2s, payload={'item_id': 'apple', 'quantity': 3}
```

### gRPC deadline

The Inventory server was set to wait 5 seconds before answering. The Order Service only waits 2 seconds (the deadline), so the gRPC call failed with `DEADLINE_EXCEEDED` and the Order Service returned 504.

Terminal 1 (`Ctrl+C` then start with delay):

```bash
INVENTORY_DELAY_SECONDS=5 python grpc_version/inventory_server.py
```

Terminal 2: Leave `python grpc_version/order_service.py` running.

Terminal 3:

```
$ .venv/Scripts/python.exe grpc_version/grpc_client.py apple 3
request:
  item_id: apple
  quantity: 3
error:
  status: DEADLINE_EXCEEDED
  details: Deadline Exceeded


$ curl -i -s -X POST http://127.0.0.1:8002/orders -H "Content-Type: application/json" -d '{"item_id": "apple", "quantity": 3}' -w "\ntime_total: %{time_total}s\n"
HTTP/1.1 504 GATEWAY TIMEOUT
Server: Werkzeug/3.1.9 Python/3.11.0
Date: Mon, 12 Oct 2026 07:27:27 GMT
Content-Type: application/json
Content-Length: 64
Connection: close

{"error":"Deadline Exceeded","grpc_status":"DEADLINE_EXCEEDED"}

time_total: 2.010229s
```

Terminal 2 (Order Service prints this log):

```
2026-10-12 00:27:27,179 ERROR inventory gRPC call failed: DEADLINE_EXCEEDED (Deadline Exceeded) -> HTTP 504
```

### Order Service kept running

I did not restart the Order Service. I only restarted the Inventory Service without the delay.

#### REST

Terminal 2: The Order Service is still running from before.

Terminal 3 (right after the 504, REST timeout evidence):

```
$ curl -i -s http://127.0.0.1:8000/health
HTTP/1.1 200 OK
Server: Werkzeug/3.1.9 Python/3.11.0
Date: Mon, 12 Oct 2026 07:27:13 GMT
Content-Type: application/json
Content-Length: 39
Connection: close

{"service":"order-rest","status":"ok"}
```

Terminal 1 (`Ctrl+C` then start without delay):

```bash
python rest/inventory_service.py
```

Terminal 3:

```
$ curl -i -s -X POST http://127.0.0.1:8000/orders -H "Content-Type: application/json" -d '{"item_id": "apple", "quantity": 3}'
HTTP/1.1 201 CREATED
Server: Werkzeug/3.1.9 Python/3.11.0
Date: Mon, 12 Oct 2026 07:27:17 GMT
Content-Type: application/json
Content-Length: 53
Connection: close

{"item_id":"apple","quantity":3,"status":"accepted"}
```

#### gRPC

Terminal 2: The Order Service is still running from before.

Terminal 3 (right after the 504, gRPC deadline evidence):

```
$ curl -i -s http://127.0.0.1:8002/health
HTTP/1.1 200 OK
Server: Werkzeug/3.1.9 Python/3.11.0
Date: Mon, 12 Oct 2026 07:27:27 GMT
Content-Type: application/json
Content-Length: 39
Connection: close

{"service":"order-grpc","status":"ok"}
```

Terminal 1 (`Ctrl+C` then start without delay):

```bash
python grpc_version/inventory_server.py
```

Terminal 3:

```
$ curl -i -s -X POST http://127.0.0.1:8002/orders -H "Content-Type: application/json" -d '{"item_id": "apple", "quantity": 3}'
HTTP/1.1 201 CREATED
Server: Werkzeug/3.1.9 Python/3.11.0
Date: Mon, 12 Oct 2026 07:27:30 GMT
Content-Type: application/json
Content-Length: 53
Connection: close

{"item_id":"apple","quantity":3,"status":"accepted"}
```

## REST vs gRPC

In REST, the two services only share JSON field names, so I had to check the input myself. In gRPC, the `.proto` file sets the field names and types, so both sides follow the same rules.
gRPC had one extra step because I had to run `protoc` to create the Python code.
REST uses HTTP error codes like 404 and 409, while gRPC uses codes like `NOT_FOUND`, so I had to change them into HTTP codes.
Both stops waiting after 2 seconds, but REST gives a timeout error and gRPC gives `DEADLINE_EXCEEDED`.
REST was easy to test with `curl`, but gRPC needed a small client program.
