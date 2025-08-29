# Configurações de Rede
MULTICAST_GROUP = '224.1.1.1'
MULTICAST_PORT = 5007
HEARTBEAT_INTERVAL = 2  # segundos
HEARTBEAT_TIMEOUT = 3 * HEARTBEAT_INTERVAL

# Configurações dos Grupos
GROUP_A_NODES = {
    1: {'host': 'localhost', 'port': 50051},
    2: {'host': 'localhost', 'port': 50052},
    3: {'host': 'localhost', 'port': 50053},
}

GROUP_B_NODES = {
    4: {'host': 'localhost', 'port': 9091},
    5: {'host': 'localhost', 'port': 9092},
    6: {'host': 'localhost', 'port': 9093},
}

# Nomes para o Pyro5
def get_pyro_name(node_id):
    return f"Simula.NodeB.{node_id}"

# Configurações de Autenticação
TOKEN_SECRET_KEY = "uma-chave-secreta-muito-forte"
TOKEN_EXPIRATION_SECONDS = 3600 # 1 hora
