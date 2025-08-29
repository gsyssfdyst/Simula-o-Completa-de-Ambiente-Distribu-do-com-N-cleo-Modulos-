import Pyro5.api
import time
import threading

from src.node import Node
from src.config import GROUP_B_NODES, get_pyro_name, HEARTBEAT_INTERVAL, HEARTBEAT_TIMEOUT

@Pyro5.api.expose
class NodeB(Node):
    def __init__(self, node_id):
        super().__init__(node_id, 'B', GROUP_B_NODES)
        self.active_nodes = {nid: time.time() for nid in self.all_nodes_config if nid != self.node_id}
        self.election_in_progress = False
        self.next_node_id = self._get_next_node_id()
        self.next_node_proxy = None

    def _get_next_node_id(self):
        sorted_ids = sorted(self.all_nodes_config.keys())
        my_index = sorted_ids.index(self.node_id)
        next_index = (my_index + 1) % len(sorted_ids)
        return sorted_ids[next_index]

    def _connect_to_next_node(self):
        while self.is_running and self.next_node_proxy is None:
            try:
                pyro_name = get_pyro_name(self.next_node_id)
                self.next_node_proxy = Pyro5.api.Proxy(f"PYRONAME:{pyro_name}")
                self.next_node_proxy._pyroTimeout = 2
                print(f"Node {self.node_id} connected to next node {self.next_node_id}")
            except Pyro5.errors.NamingError:
                print(f"Node {self.node_id} waiting for next node {self.next_node_id}...")
                time.sleep(2)

    # --- Remote Methods (Pyro5) ---
    def execute_task(self, task_name, lamport_time):
        self.clock.update(lamport_time)
        print(f"Node {self.node_id} (Clock: {self.clock.get_time()}) received task: {task_name}")
        return "Task completed", self.clock.increment()

    def handle_election_message(self, message):
        self.clock.update(message['lamport_time'])
        
        if message['type'] == 'ELECTION':
            if self.node_id in message['participants']:
                # Eleição completou um ciclo
                self.leader_id = max(message['participants'])
                self.election_in_progress = False
                print(f"Node {self.node_id} completed election. New leader is {self.leader_id}")
                # Propaga a mensagem de COORDENADOR
                self.pass_message({
                    'type': 'COORDINATOR',
                    'leader_id': self.leader_id,
                    'lamport_time': self.clock.increment()
                })
            else:
                # Adiciona a si mesmo e passa adiante
                print(f"Node {self.node_id} participates in election.")
                message['participants'].append(self.node_id)
                message['lamport_time'] = self.clock.increment()
                self.pass_message(message)
        
        elif message['type'] == 'COORDINATOR':
            if self.leader_id != message['leader_id']:
                self.leader_id = message['leader_id']
                self.election_in_progress = False
                print(f"Node {self.node_id} acknowledges new leader: {self.leader_id}")
                self.pass_message(message) # Continua propagando para fechar o anel

    def heartbeat(self, sender_id, lamport_time):
        self.clock.update(lamport_time)
        self.active_nodes[sender_id] = time.time()
        return "ALIVE", self.clock.increment()

    # --- Ring Algorithm & Communication ---
    def start_election(self):
        if self.election_in_progress:
            return
        self.election_in_progress = True
        print(f"Node {self.node_id} starts an ELECTION.")
        message = {
            'type': 'ELECTION',
            'participants': [self.node_id],
            'lamport_time': self.clock.increment()
        }
        self.pass_message(message)

    def pass_message(self, message):
        if not self.next_node_proxy:
            print(f"Node {self.node_id}: Cannot pass message, no proxy to next node.")
            return

        try:
            self.next_node_proxy.handle_election_message(message)
        except Pyro5.errors.CommunicationError:
            print(f"Node {self.node_id} could not pass message to {self.next_node_id}. It may be down.")
            # Em uma implementação completa, aqui se tentaria pular o nó falho.
            # Por simplicidade, a detecção de falha do heartbeat irá tratar isso.

    # --- Heartbeat & Failure Detection ---
    def _send_heartbeats(self):
        while self.is_running:
            time.sleep(HEARTBEAT_INTERVAL)
            for nid in list(self.active_nodes.keys()):
                try:
                    pyro_name = get_pyro_name(nid)
                    with Pyro5.api.Proxy(f"PYRONAME:{pyro_name}") as proxy:
                        proxy._pyroTimeout = 1
                        _, remote_time = proxy.heartbeat(self.node_id, self.clock.increment())
                        self.clock.update(remote_time)
                except Exception:
                    pass # Falha tratada no _check_failures

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
                    if nid == self.next_node_id:
                        print(f"Next node {nid} failed. Re-calculating ring.")
                        self.next_node_proxy = None
                        self.next_node_id = self._get_next_node_id() # Simplificação, assume que a lista de nós é estática
                        self._connect_to_next_node()

    # --- Lifecycle Methods ---
    def run(self):
        host = self.all_nodes_config[self.node_id]['host']
        port = self.all_nodes_config[self.node_id]['port']
        pyro_name = get_pyro_name(self.node_id)
        
        daemon = Pyro5.api.Daemon(host=host, port=port)
        uri = daemon.register(self, objectId=pyro_name)
        ns = Pyro5.api.locate_ns()
        ns.register(pyro_name, uri)

        print(f"Starting Node {self.node_id} (Group B) as {pyro_name}")
        
        threading.Thread(target=daemon.requestLoop, args=(lambda: self.is_running,), daemon=True).start()
        
        self._connect_to_next_node()
        threading.Thread(target=self._send_heartbeats, daemon=True).start()
        threading.Thread(target=self._check_failures, daemon=True).start()

        time.sleep(5) # Espera para que outros nós iniciem
        self.start_election()

        while self.is_running:
            time.sleep(1)
        
        ns.remove(pyro_name)
        daemon.shutdown()

    def stop(self):
        super().stop()
