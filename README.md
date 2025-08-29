# Simulação de Ambiente Distribuído com Núcleo Modular

Este projeto é uma implementação de um sistema distribuído simulado, desenvolvido para a disciplina de Sistemas Distribuídos do Instituto Federal da Bahia (IFBA), Campus Santo Antônio de Jesus  objetivo é integrar múltiplos modelos de comunicação (Sockets, Multicast), middleware (gRPC, Pyro5), algoritmos de sincronização (Relógios de Lamport), eleição de líder (Bully, Anel), captura de estado (Chandy-Lamport) e tolerância a falhas (Heartbeat)

## Tecnologias Utilizadas

* **Linguagem:** Python
* **Comunicação Intra-grupo:** Sockets TCP
* **Comunicação Intergrupos:** UDP Multicast 
* **Middleware Grupo A:** gRPC 
* **Middleware Grupo B:** Pyro5 
* **Sincronização:** Relógios de L
* **Eleição:** Algoritmo de Bully e Algoritmo de Anel 
* **Detecção de Falhas:** Heartbeat 
* **Snapshot:** Algoritmo de Chandy-Lamport
* **Segurança:** Autenticação por token com tempo de expiração

## Estrutura do Projeto

```
.
├── grupo_a/
│   ├── no_a.py         # Lógica do nó do Grupo A (gRPC, Bully)
│   └── ...             # Arquivos .proto, stubs, etc.
├── grupo_b/
│   ├── no_b.py         # Lógica do nó do Grupo B (Pyro5, Anel)
│   └── ...
├── shared/
│   ├── lamport_clock.py # Implementação do Relógio de Lamport
│   └── heartbeat.py     # Lógica do Heartbeat
├── multicast_communicator.py # Módulo para comunicação intergrupos
└── main.py             # Script principal para iniciar a simulação
```
**[Nota: Adapte a estrutura de diretórios acima para refletir a organização real do seu código.]**

## Pré-requisitos

Antes de executar, instale todas as dependências necessárias:
```bash
pip install -r requirements.txt
```
**[Nota: Crie um arquivo `requirements.txt` com todas as bibliotecas usadas, como `grpcio`, `grpcio-tools`, `Pyro5`, etc.]**

## Instruções de Execução

1.  **Inicie o Name Server do Pyro5 (necessário para o Grupo B):**
    ```bash
    pyro5-ns
    ```

2.  **Inicie os 3 nós do Grupo A (gRPC):**
    Abra 3 terminais diferentes e execute:
    ```bash
    # Terminal 1
    python grupo_a/no_a.py --id=1 --port=50051

    # Terminal 2
    python grupo_a/no_a.py --id=2 --port=50052

    # Terminal 3
    python grupo_a/no_a.py --id=3 --port=50053
    ```

3.  **Inicie os 3 nós do Grupo B (Pyro5):**
    Abra mais 3 terminais e execute:
    ```bash
    # Terminal 4
    python grupo_b/no_b.py --id=4 --name=NodeB1

    # Terminal 5
    python grupo_b/no_b.py --id=5 --name=NodeB2

    # Terminal 6
    python grupo_b/no_b.py --id=6 --name=NodeB3
    ```
**[Nota: Adapte os comandos acima para refletir como seu programa é realmente iniciado.]**

## Autores
 Amanda Santos Lopes
 João Vitor Rocha Soares
 João Heric Alves Pereira

