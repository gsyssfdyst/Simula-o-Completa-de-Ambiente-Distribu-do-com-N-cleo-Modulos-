import time
import subprocess
import threading
import sys

from src.config import GROUP_A_NODES, GROUP_B_NODES
from src.group_a.node_a import NodeA
from src.group_b.node_b import NodeB
from src.common.token_manager import TokenManager

def start_pyro_ns():
    """Inicia o Pyro Name Server em um processo separado."""
    try:
        # Tenta localizar um NS existente
        import Pyro5.api
        Pyro5.api.locate_ns()
        print("Pyro Name Server já está rodando.")
        return None
    except Pyro5.errors.NamingError:
        print("Iniciando Pyro Name Server...")
        # O comando pode variar dependendo do ambiente (ex: 'pyro5-ns')
        return subprocess.Popen([sys.executable, "-m", "Pyro5.nameserver"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    # Inicia o Pyro Name Server
    pyro_ns_process = start_pyro_ns()
    time.sleep(2) # Dá tempo para o NS iniciar

    nodes = []
    
    # Inicia nós do Grupo A
    for node_id in GROUP_A_NODES:
        node = NodeA(node_id)
        nodes.append(node)
        node.start()

    # Inicia nós do Grupo B
    for node_id in GROUP_B_NODES:
        node = NodeB(node_id)
        nodes.append(node)
        node.start()

    print("\nTodos os nós foram iniciados. A simulação está em execução.")
    print("Eleições de líder em cada grupo começarão em breve.")
    print("Pressione Ctrl+C para encerrar a simulação.\n")

    try:
        # Demonstração de funcionalidades após a eleição
        time.sleep(15) # Espera as eleições terminarem

        print("\n--- DEMONSTRAÇÃO DE FUNCIONALIDADES ---")
        
        # Encontra líderes
        leader_a = None
        leader_b = None
        for node in nodes:
            if node.group_id == 'A' and node.leader_id == node.node_id:
                leader_a = node
            if node.group_id == 'B' and node.leader_id == node.node_id:
                leader_b = node
        
        if leader_a:
            print(f"\nLíder do Grupo A é o Nó {leader_a.node_id}")
            # Demonstração de autenticação
            token = TokenManager.generate_token(leader_a.node_id)
            print(f"Líder {leader_a.node_id} gerou um token.")
            TokenManager.access_sensitive_data(token)
        else:
            print("\nNenhum líder eleito no Grupo A ainda.")

        if leader_b:
            print(f"\nLíder do Grupo B é o Nó {leader_b.node_id}")
            token = TokenManager.generate_token(leader_b.node_id)
            print(f"Líder {leader_b.node_id} gerou um token.")
            TokenManager.access_sensitive_data(token)
        else:
            print("\nNenhum líder eleito no Grupo B ainda.")

        # Eleição do Supercoordenador (simplificado)
        if leader_a and leader_b:
            super_coordinator = max(leader_a, leader_b, key=lambda x: x.node_id)
            print(f"\nEleição de Supercoordenador: Nó {super_coordinator.node_id} foi eleito.")
            # Aqui viria a lógica de snapshot de Chandy-Lamport iniciada pelo supercoordenador
            print("(Lógica de snapshot de Chandy-Lamport a ser implementada aqui)")

        # Mantém a simulação rodando
        while True:
            time.sleep(10)
            print("\n--- Status Atual dos Nós ---")
            for node in nodes:
                if node.is_alive():
                    print(node)
            print("---------------------------\n")


    except KeyboardInterrupt:
        print("\nEncerrando a simulação...")
        for node in nodes:
            node.stop()
        for node in nodes:
            node.join(timeout=2)
        
        if pyro_ns_process:
            pyro_ns_process.terminate()
            pyro_ns_process.wait()
        
        print("Simulação encerrada.")

if __name__ == "__main__":
    main()
