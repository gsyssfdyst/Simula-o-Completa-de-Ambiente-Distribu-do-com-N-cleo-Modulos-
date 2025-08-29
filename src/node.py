import threading
from src.common.lamport_clock import LamportClock

class Node(threading.Thread):
    def __init__(self, node_id, group_id, all_nodes_config):
        super().__init__()
        self.node_id = node_id
        self.group_id = group_id
        self.all_nodes_config = all_nodes_config
        self.clock = LamportClock()
        self.leader_id = None
        self.is_running = True
        self.daemon = True # Permite que a thread principal saia mesmo se as threads dos nós estiverem ativas

    def stop(self):
        self.is_running = False
        print(f"Node {self.node_id} is stopping.")

    def __str__(self):
        return f"Node(id={self.node_id}, group='{self.group_id}', clock={self.clock.get_time()}, leader={self.leader_id})"
