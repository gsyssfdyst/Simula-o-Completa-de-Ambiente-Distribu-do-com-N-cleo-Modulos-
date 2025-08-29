import grpc
import time
import threading
from concurrent import futures

from src.node import Node
from src.config import GROUP_A_NODES, HEARTBEAT_INTERVAL, HEARTBEAT_TIMEOUT
from src.group_a import service_pb2, service_pb2_grpc

class NodeA(Node, service_pb2_grpc.NodeAServicer):
    def __init__(self, node_id):
        super().__init__(node_id, 'A', GROUP_A_NODES)
        self.server = None
        self.active_nodes = {nid: time.time() for nid in self.all_nodes_config if nid != self.node_id}
        self.election_in_progress = False

    # --- gRPC Service Implementation ---
    def ExecuteTask(self, request, context):
        self.clock.update(request.lamport_time)
        print(f"Node {self.node_id} (Clock: {self.clock.get_time()}) received task: {request.task_name}")
        return service_pb2.TaskResponse(status="Task completed", lamport_time=self.clock.increment())

    def Heartbeat(self, request, context):
        self.clock.update(request.lamport_time)
        self.active_nodes[request.sender_id] = time.time()
        return service_pb2.HeartbeatResponse(status=service_pb2.HeartbeatResponse.ALIVE, lamport_time=self.clock.increment())

    def HandleElection(self, request, context):
        self.clock.update(request.lamport_time)
        sender_id = request.sender_id
        
        if request.type == service_pb2.ElectionMessage.ELECTION:
            print(f"Node {self.node_id} received ELECTION from {sender_id}")
            if self.node_id > sender_id:
                self._send_election_response(sender_id, 'OK')
                if not self.election_in_progress:
                    self.start_election()
            return service_pb2.ElectionResponse(status="Handled", lamport_time=self.clock.increment())

        elif request.type == service_pb2.ElectionMessage.COORDINATOR:
            print(f"Node {self.node_id} received COORDINATOR from {sender_id}")
            self.leader_id = sender_id
            self.election_in_progress = False
            return service_pb2.ElectionResponse(status="Acknowledged", lamport_time=self.clock.increment())
        
        return service_pb2.ElectionResponse(status="Unknown type", lamport_time=self.clock.increment())

    # --- Bully Algorithm & Communication ---
    def _send_election_response(self, target_id, message_type):
        # Esta é uma simplificação. Em uma implementação real, o nó que recebe 'ELECTION'
        # responderia 'OK' ao remetente. Aqui, a lógica está focada no iniciador.
        pass

    def start_election(self):
        if self.election_in_progress:
            return
        self.election_in_progress = True
        print(f"Node {self.node_id} starts an ELECTION.")
        
        higher_nodes = [nid for nid in self.all_nodes_config if nid > self.node_id]
        responses = 0
        
        for nid in higher_nodes:
            try:
                with self._create_stub(nid) as stub:
                    request = service_pb2.ElectionMessage(type=service_pb2.ElectionMessage.ELECTION, sender_id=self.node_id, lamport_time=self.clock.increment())
                    stub.HandleElection(request, timeout=1)
                    responses += 1 # Resposta 'OK' implícita
            except grpc.RpcError:
                pass # Nó não respondeu, considerado inativo

        if responses == 0:
            self.announce_coordinator()

    def announce_coordinator(self):
        self.leader_id = self.node_id
        self.election_in_progress = False
        print(f"Node {self.node_id} is the new LEADER.")
        
        for nid in self.all_nodes_config:
            if nid != self.node_id:
                try:
                    with self._create_stub(nid) as stub:
                        request = service_pb2.ElectionMessage(type=service_pb2.ElectionMessage.COORDINATOR, sender_id=self.node_id, lamport_time=self.clock.increment())
                        stub.HandleElection(request)
                except grpc.RpcError:
                    print(f"Node {self.node_id} could not announce leadership to {nid}.")

    # --- Heartbeat & Failure Detection ---
    def _send_heartbeats(self):
        while self.is_running:
            time.sleep(HEARTBEAT_INTERVAL)
            for nid in list(self.active_nodes.keys()):
                try:
                    with self._create_stub(nid) as stub:
                        request = service_pb2.HeartbeatMessage(sender_id=self.node_id, lamport_time=self.clock.increment())
                        response = stub.Heartbeat(request, timeout=1)
                        self.clock.update(response.lamport_time)
                except grpc.RpcError:
                    print(f"Heartbeat to Node {nid} failed.")
                    # A falha é tratada no _check_failures

    def _check_failures(self):
        while self.is_running:
            time.sleep(HEARTBEAT_INTERVAL)
            now = time.time()
            for nid, last_seen in list(self.active_nodes.items()):
                if now - last_seen > HEARTBEAT_TIMEOUT:
                    print(f"Node {self.node_id} detected failure of Node {nid}.")
                    del self.active_nodes[nid]
                    if nid == self.leader_id:
                        print(f"LEADER {nid} failed! Starting new election.")
                        self.start_election()

    # --- Helper & Lifecycle Methods ---
    def _create_stub(self, target_id):
        channel = grpc.insecure_channel(f"{self.all_nodes_config[target_id]['host']}:{self.all_nodes_config[target_id]['port']}")
        return service_pb2_grpc.NodeAServiceStub(channel)

    def run(self):
        print(f"Starting Node {self.node_id} (Group A) on port {self.all_nodes_config[self.node_id]['port']}")
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        service_pb2_grpc.add_NodeAServicer_to_server(self, self.server)
        self.server.add_insecure_port(f"[::]:{self.all_nodes_config[self.node_id]['port']}")
        self.server.start()

        threading.Thread(target=self._send_heartbeats, daemon=True).start()
        threading.Thread(target=self._check_failures, daemon=True).start()
        
        time.sleep(5) # Espera para que outros nós iniciem
        self.start_election()

        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        super().stop()
        if self.server:
            self.server.stop(0)
