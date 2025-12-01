import socket
import threading
import json
import time
import random
from settings import MAPA, TILE_SIZE

HOST = '127.0.0.1'
PORT = 5555

# --- VARIÁVEIS GLOBAIS ---
clientes_conectados = 0 
start_player_pos = [0, 0]
start_villain_pos = [0, 0]
lista_orbes = []  
lista_pocoes = [] 

print("--- INICIALIZANDO MUNDO ---")
for y, linha in enumerate(MAPA):
    for x, bloco in enumerate(linha):
        px, py = x * TILE_SIZE, y * TILE_SIZE
        if bloco == 3: 
            start_player_pos = [px, py]
        elif bloco == 4: 
            start_villain_pos = [px, py]
        elif bloco == 2: 
            lista_orbes.append({"x": px, "y": py}) # Orbe (Ponto)
        elif bloco == 5: 
            lista_pocoes.append({"x": px, "y": py}) # Poção (Energizador)

print(f"Orbes (Pontos) carregados: {len(lista_orbes)}")
print(f"Poções (Energizadores) carregadas: {len(lista_pocoes)}")

estado_jogo = {
    "player": {
        "x": start_player_pos[0], 
        "y": start_player_pos[1],
        "destino_x": start_player_pos[0],
        "destino_y": start_player_pos[1],
    },
    "villains": [
        {"id": 0, "tipo": "fogo",  "x": start_villain_pos[0],      "y": start_villain_pos[1], "direcao": "esquerda"},
        {"id": 1, "tipo": "agua",  "x": start_villain_pos[0] + 30, "y": start_villain_pos[1], "direcao": "direita"},
        {"id": 2, "tipo": "terra", "x": start_villain_pos[0] - 30, "y": start_villain_pos[1], "direcao": "cima"},
        {"id": 3, "tipo": "ar",    "x": start_villain_pos[0],      "y": start_villain_pos[1] + 30, "direcao": "baixo"},
    ],
    "orbes": lista_orbes,     
    "pocoes": lista_pocoes,   
    "pontuacao": 0,
    "vidas": 3,
    "invencivel_ate": 0,       
    "i_frames_ate": 0,         
    "status": "JOGANDO"
}

def resetar_posicoes():
    """Reseta posições do jogador e vilões após colisão."""
    estado_jogo["player"]["x"] = start_player_pos[0]
    estado_jogo["player"]["y"] = start_player_pos[1]
    estado_jogo["player"]["destino_x"] = start_player_pos[0]
    estado_jogo["player"]["destino_y"] = start_player_pos[1]
    
    vx, vy = start_villain_pos
    estado_jogo["villains"][0].update({"x": vx,      "y": vy})
    estado_jogo["villains"][1].update({"x": vx + 30, "y": vy})
    estado_jogo["villains"][2].update({"x": vx - 30, "y": vy})
    estado_jogo["villains"][3].update({"x": vx,      "y": vy + 30})
    
    estado_jogo["i_frames_ate"] = time.time() + 2  
    estado_jogo["invencivel_ate"] = 0 
    
    time.sleep(0.5)

def pode_mover(x, y):
    """Verifica se a posição (x, y) está em um bloco que não é parede."""
    grid_x = int(x // TILE_SIZE)
    grid_y = int(y // TILE_SIZE)
    if grid_y < 0 or grid_y >= len(MAPA) or grid_x < 0 or grid_x >= len(MAPA[0]): 
        return False
    if MAPA[grid_y][grid_x] == 1: 
        return False
    return True

def checar_regras():
    """Lógica central: coleta de itens, colisão e fim de jogo."""
    if estado_jogo["status"] != "JOGANDO": return

    px, py = estado_jogo["player"]["x"], estado_jogo["player"]["y"]
    cx, cy = px + 15, py + 15 
    
    # 1. Coleta de Orbes (Pontos)
    for i in range(len(estado_jogo["orbes"]) - 1, -1, -1): 
        orbe = estado_jogo["orbes"][i]
        if abs(cx - (orbe["x"]+15)) < 8 and abs(cy - (orbe["y"]+15)) < 8:
            del estado_jogo["orbes"][i]
            estado_jogo["pontuacao"] += 10
            
    # 2. Coleta de Poções (Energizadores)
    for i in range(len(estado_jogo["pocoes"]) - 1, -1, -1):
        pocao = estado_jogo["pocoes"][i]
        if abs(cx - (pocao["x"]+15)) < 15 and abs(cy - (pocao["y"]+15)) < 15:
            del estado_jogo["pocoes"][i]
            estado_jogo["pontuacao"] += 50
            estado_jogo["invencivel_ate"] = time.time() + 8 

    # Checa Vitória
    if len(estado_jogo["orbes"]) == 0 and len(estado_jogo["pocoes"]) == 0: 
        estado_jogo["status"] = "VITORIA"

    # 3. Colisão com Vilões
    tempo_atual = time.time()
    invencivel_pocao = tempo_atual < estado_jogo["invencivel_ate"]
    invencivel_dano = tempo_atual < estado_jogo["i_frames_ate"]

    for v in estado_jogo["villains"]:
        vx, vy = v["x"], v["y"]
        
        if abs(px - vx) < 25 and abs(py - vy) < 25:
            
            if invencivel_pocao:
                estado_jogo["pontuacao"] += 200 
                v["x"], v["y"] = start_villain_pos[0], start_villain_pos[1] 
                v["direcao"] = random.choice(["cima", "baixo", "esquerda", "direita"])
                return
            
            if invencivel_dano:
                return 

            else:
                estado_jogo["vidas"] -= 1
                estado_jogo["invencivel_ate"] = 0 
                estado_jogo["i_frames_ate"] = time.time() + 2
                
                if estado_jogo["vidas"] <= 0:
                    estado_jogo["status"] = "GAMEOVER"
                else:
                    resetar_posicoes()
                return 

def mover_jogador(velocidade_passo=10):
    """Move o jogador em direção ao seu destino_x/y no loop do jogo."""
    px, py = estado_jogo["player"]["x"], estado_jogo["player"]["y"]
    destino_x = estado_jogo["player"]["destino_x"]
    destino_y = estado_jogo["player"]["destino_y"]
    
    if px == destino_x and py == destino_y:
        return

    dx = 0
    dy = 0

    if destino_x > px: 
        dx = min(destino_x - px, velocidade_passo)
    elif destino_x < px: 
        dx = max(destino_x - px, -velocidade_passo)
    
    if destino_y > py: 
        dy = min(destino_y - py, velocidade_passo)
    elif destino_y < py: 
        dy = max(destino_y - py, -velocidade_passo)

    estado_jogo["player"]["x"] += dx
    estado_jogo["player"]["y"] += dy


def mover_viloes():
    """Controla o movimento da IA dos vilões (Com correção de colisão)."""
    velocidade_vilao = 8 
    tempo_atual = time.time()
    invencivel_pocao = tempo_atual < estado_jogo["invencivel_ate"]

    if invencivel_pocao:
        velocidade_vilao = 4 
        
    opcoes = ["cima", "baixo", "esquerda", "direita"]

    for vilao in estado_jogo["villains"]:
        nx, ny = vilao["x"], vilao["y"]
        direcao = vilao["direcao"]

        if direcao == "cima": ny -= velocidade_vilao
        elif direcao == "baixo": ny += velocidade_vilao
        elif direcao == "esquerda": nx -= velocidade_vilao
        elif direcao == "direita": nx += velocidade_vilao

        if pode_mover(nx, ny) and pode_mover(nx + TILE_SIZE - 1, ny + TILE_SIZE - 1): 
            vilao["x"], vilao["y"] = nx, ny
            
            chance_mudar = 10 if invencivel_pocao else 2 
            if random.randint(0, 100) < chance_mudar: 
                vilao["direcao"] = random.choice(opcoes)
        else:
            vilao["direcao"] = random.choice(opcoes)

def loop_do_jogo():
    """Loop principal da lógica do jogo (IA + Regras + Movimento do Jogador)."""
    while True:
        if clientes_conectados > 0 and estado_jogo["status"] == "JOGANDO":
            mover_jogador()
            mover_viloes()
            checar_regras()
        
        time.sleep(0.05)

def handle_client(conn, addr):
    global clientes_conectados
    clientes_conectados += 1
    
    velocidade = TILE_SIZE 
    connected = True
    while connected:
        try:
            msg = conn.recv(4096).decode('utf-8')
            if not msg: break
            if "}{" in msg: msg = msg.split("}{")[0] + "}" 

            if msg.startswith("{") and estado_jogo["status"] == "JOGANDO":
                dados = json.loads(msg)
                
                if dados.get("acao") == "mover":
                    
                    px = estado_jogo["player"]["x"]
                    py = estado_jogo["player"]["y"]
                    
                    if px != estado_jogo["player"]["destino_x"] or py != estado_jogo["player"]["destino_y"]:
                        pass 
                    else:
                        nx, ny = px, py
                        d = dados.get("direcao")
                        
                        if d == "cima": ny -= velocidade
                        elif d == "baixo": ny += velocidade
                        elif d == "esquerda": nx -= velocidade
                        elif d == "direita": nx += velocidade
                        
                        if pode_mover(nx, ny) and pode_mover(nx + TILE_SIZE - 1, ny + TILE_SIZE - 1): 
                            estado_jogo["player"]["destino_x"] = nx
                            estado_jogo["player"]["destino_y"] = ny
                            
            conn.send(json.dumps(estado_jogo).encode('utf-8'))
        except:
            connected = False
    
    conn.close()
    clientes_conectados -= 1

def start():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVIDOR ONLINE] Aguardando em {HOST}:{PORT}")
    
    t = threading.Thread(target=loop_do_jogo)
    t.start()
    
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    start()