import pygame
import sys
import socket
import json
from settings import *
import time 

# --- Inicialização ---
pygame.init()
pygame.font.init()
pygame.mixer.init()

# --- Rede ---
CLIENT_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER_IP = '127.0.0.1'
SERVER_PORT = 5555
CONECTADO = False

# --- Tela ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Guardião do Recanto")

# --- Cores ---
COLOR_FUNDO_ESCURO = (10, 30, 10)
COLOR_TITULO = (230, 220, 190)
COLOR_TEXTO_GERAL = (150, 150, 150)
COLOR_BOTAO_NORMAL = (180, 180, 180)
COLOR_BOTAO_HOVER = (255, 255, 255)
COLOR_VULNERAVEL = (50, 50, 255) 

# --- Assets (Fundo, Fonte, Musica) ---
background_image = None
try:
    background_image = pygame.image.load("images/fundo_menu2.png").convert_alpha()
    background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
except: pass

try:
    caminho_fonte = "assets/fonts/Cinzel-Regular.ttf"
    font_titulo = pygame.font.Font(caminho_fonte, 60)
    font_botao = pygame.font.Font(caminho_fonte, 38)
    font_texto = pygame.font.Font(caminho_fonte, 28)
except:
    font_titulo = pygame.font.Font(None, 60)
    font_botao = pygame.font.Font(None, 38)
    font_texto = pygame.font.Font(None, 28)

try:
    pygame.mixer.music.load("assets/audio/spirit_world.ogg")
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)
except: pass

# --- SPRITES ---
sprites = {} 

def carregar_spritesheet(caminho, largura_frame, altura_frame, tamanho_final):
    try:
        sheet = pygame.image.load(caminho).convert_alpha()
        largura_total = sheet.get_width()
        frames = []
        if largura_total < largura_frame:
            frame = pygame.transform.scale(sheet, (tamanho_final, tamanho_final))
            frames.append(frame)
            return frames

        for x in range(0, largura_total, largura_frame):
            if x + largura_frame > largura_total: break
            rect = pygame.Rect(x, 0, largura_frame, altura_frame)
            frame = sheet.subsurface(rect)
            frame = pygame.transform.scale(frame, (tamanho_final, tamanho_final))
            frames.append(frame)
        return frames
    except Exception as e:
        print(f"Aviso: Imagem não encontrada {caminho}")
        return None
    
print("--- TENTANDO CARREGAR IMAGENS ---")

sprites["player"] = carregar_spritesheet("images/guardioes.png", 32, 32, 45)
sprites["fogo"]   = carregar_spritesheet("images/fogos.png", 32, 32, 45)   
sprites["agua"]   = carregar_spritesheet("images/aguas.png", 32, 32, 45)
sprites["terra"]  = carregar_spritesheet("images/terras.png", 32, 32, 45)
sprites["ar"]     = carregar_spritesheet("images/ares.png", 32, 32, 45)

# Orbes e Poções
sprites["orbe"]   = carregar_spritesheet("images/orbe.png", 32, 32, 10) 
sprites["pocao"]  = carregar_spritesheet("images/pocao.png", 32, 32, 20) 

# --- VERIFICAÇÃO DE ERROS ---
for nome, imagem in sprites.items():
    if imagem is None:
        print(f"❌ ERRO: Não achei a imagem do '{nome}'!")
    else:
        print(f"✅ Sucesso: '{nome}' carregado.")
print("---------------------------------")

# --- Estados ---
ESTADO_MENU = "menu"
ESTADO_JOGANDO = "jogando"
ESTADO_AJUDA = "ajuda"
ESTADO_SOBRE = "sobre"
ESTADO_SAIR = "sair"
estado_atual = ESTADO_MENU
botoes_clicaveis = {}

def criar_botao(texto, pos_y, estado_alvo):
    mouse_pos = pygame.mouse.get_pos()
    rect = pygame.Rect((SCREEN_WIDTH/2 - 200), pos_y, 400, 40)
    cor = COLOR_BOTAO_HOVER if rect.collidepoint(mouse_pos) else COLOR_BOTAO_NORMAL
    txt = f"« {texto} »" if rect.collidepoint(mouse_pos) else texto
    surf = font_botao.render(txt, True, cor)
    screen.blit(surf, surf.get_rect(center=rect.center))
    botoes_clicaveis[texto] = (rect, estado_alvo)

def criar_texto_simples(texto, pos_y, font=font_texto, cor=COLOR_TEXTO_GERAL):
    surf = font.render(texto, True, cor)
    screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH/2, pos_y)))

def desenhar_fundo_comum():
    if background_image: screen.blit(background_image, (0, 0))
    else: screen.fill(COLOR_FUNDO_ESCURO)

def desenhar_tela_menu():
    desenhar_fundo_comum()
    criar_texto_simples("Guardião do Recanto", 110, font_titulo, COLOR_TITULO)
    criar_botao("Iniciar Jogo", 260, ESTADO_JOGANDO)
    criar_botao("Ajuda", 320, ESTADO_AJUDA)
    criar_botao("Sobre", 380, ESTADO_SOBRE)
    criar_botao("Sair", 440, ESTADO_SAIR)

def desenhar_tela_ajuda():
    desenhar_fundo_comum()
    criar_texto_simples("Ajuda", 110, font_titulo, COLOR_TITULO)
    criar_texto_simples("Use W, A, S, D para mover um quadrado por vez.", 300)
    criar_botao("Voltar", 480, ESTADO_MENU)

def desenhar_tela_sobre():
    desenhar_fundo_comum()
    criar_texto_simples("Sobre", 110, font_titulo, COLOR_TITULO)
    criar_texto_simples("Criado por: Guilherme, Julia, Paloma", 300)
    criar_botao("Voltar", 530, ESTADO_MENU)

# --- Jogo ---
# Apenas a função desenhar_jogo_online corrigida:

def desenhar_jogo_online(dados):
    screen.fill((15, 20, 15)) 
    
    # 1. Desenhar Paredes (PRIMEIRO)
    for r, row in enumerate(MAPA):
        for c, tile in enumerate(row):
            x, y = c * TILE_SIZE, r * TILE_SIZE
            if tile == 1:
                pygame.draw.rect(screen, (40, 60, 40), (x, y, TILE_SIZE, TILE_SIZE))
                pygame.draw.rect(screen, (20, 30, 20), (x, y, TILE_SIZE, TILE_SIZE), 1)

    # Animação
    idx = (pygame.time.get_ticks() // 200) % 2
    
    offset_char = (45 - 30) // 2
    offset_orbe = (30 - 10) // 2 
    offset_pocao = (30 - 20) // 2 

    if dados:
        # 2. Orbes (Bolinhas) - DESENHO FORÇADO DO CÍRCULO
        if "orbes" in dados:
            for orbe in dados["orbes"]:
                ox, oy = orbe["x"], orbe["y"]
                # Forçamos o desenho de um círculo para garantir que os dados estão chegando.
                pygame.draw.circle(screen, COLOR_ORBE, (ox + 15, oy + 15), 5) 

        # 3. Poções (Energizadores) - DESENHO FORÇADO DO CÍRCULO
        if "pocoes" in dados:
            if int(time.time() * 3) % 2 == 0:
                for pocao in dados["pocoes"]:
                    px, py = pocao["x"], pocao["y"]
                    # Forçamos o desenho de um círculo maior para a poção.
                    pygame.draw.circle(screen, COLOR_POCAO, (px + 15, py + 15), 10) 


        # 4. Jogador (Desenho por cima dos itens)
        px, py = dados["player"]["x"], dados["player"]["y"]
        
        i_frames_fim = dados.get("i_frames_ate", 0)
        agora = time.time()
        
        deve_piscar = agora < i_frames_fim
        desenhar_sprite = not deve_piscar or (int(agora * 10) % 2 == 0)

        if sprites["player"] and desenhar_sprite:
            screen.blit(sprites["player"][idx % len(sprites["player"])], (px - offset_char, py - offset_char))
        elif not sprites["player"]:
            pygame.draw.rect(screen, COLOR_JOGADOR, (px, py, 30, 30))

        # 5. Vilões (Desenho por cima dos itens)
        tempo_invencivel = dados.get("invencivel_ate", 0)
        vilao_vulneravel = time.time() < tempo_invencivel
        
        for v in dados["villains"]:
            vx, vy, tipo = v["x"], v["y"], v["tipo"]
            
            if vilao_vulneravel:
                pygame.draw.rect(screen, COLOR_VULNERAVEL, (vx, vy, 30, 30))
            
            if tipo in sprites and sprites[tipo] and not vilao_vulneravel:
                screen.blit(sprites[tipo][idx % len(sprites[tipo])], (vx - offset_char, vy - offset_char))
            elif not vilao_vulneravel and tipo not in sprites:
                pygame.draw.rect(screen, COLOR_VILAO, (vx, vy, 30, 30))
        
        # 6. Pontuação & Vidas
        pts = dados.get("pontuacao", 0)
        vidas = dados.get("vidas", 3)
        txt_pts = font_texto.render(f"Pontos: {pts}", True, (255, 255, 255))
        txt_vidas = font_texto.render(f"Vidas: {vidas}", True, (255, 50, 50))
        screen.blit(txt_pts, (20, 20))
        screen.blit(txt_vidas, (SCREEN_WIDTH - 150, 20)) 

        # 7. Tela de Fim de Jogo
        status = dados.get("status")
        if status == "GAMEOVER":
             msg = font_titulo.render("GAME OVER", True, (255, 50, 50))
             screen.blit(msg, msg.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2)))
        elif status == "VITORIA":
             msg = font_titulo.render("VITÓRIA!", True, (50, 255, 50))
             screen.blit(msg, msg.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2)))

# --- LOOP PRINCIPAL ---
clock = pygame.time.Clock()

while estado_atual != ESTADO_SAIR:
    enviou_movimento = False 

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            estado_atual = ESTADO_SAIR
            if CONECTADO: CLIENT_SOCKET.close()
        
        if event.type == pygame.MOUSEBUTTONDOWN and estado_atual != ESTADO_JOGANDO:
            if event.button == 1:
                for rect, alvo in botoes_clicaveis.values():
                    if rect.collidepoint(event.pos): estado_atual = alvo

        if event.type == pygame.KEYDOWN and estado_atual == ESTADO_JOGANDO:
            cmd = None
            if event.key in [pygame.K_w, pygame.K_UP]: cmd = {"acao": "mover", "direcao": "cima"}
            elif event.key in [pygame.K_s, pygame.K_DOWN]: cmd = {"acao": "mover", "direcao": "baixo"}
            elif event.key in [pygame.K_a, pygame.K_LEFT]: cmd = {"acao": "mover", "direcao": "esquerda"}
            elif event.key in [pygame.K_d, pygame.K_RIGHT]: cmd = {"acao": "mover", "direcao": "direita"}
            
            if cmd and CONECTADO:
                try:
                    CLIENT_SOCKET.send(json.dumps(cmd).encode('utf-8'))
                    enviou_movimento = True
                except: pass

    botoes_clicaveis.clear()
    
    if estado_atual == ESTADO_MENU: desenhar_tela_menu()
    elif estado_atual == ESTADO_AJUDA: desenhar_tela_ajuda()
    elif estado_atual == ESTADO_SOBRE: desenhar_tela_sobre()
    
    elif estado_atual == ESTADO_JOGANDO:
        if not CONECTADO:
            try:
                CLIENT_SOCKET.connect((SERVER_IP, SERVER_PORT))
                CONECTADO = True
            except:
                desenhar_fundo_comum()
                msg = font_texto.render("Conectando...", True, (255, 100, 100))
                screen.blit(msg, (300, 300))
                pygame.display.flip()
                continue

        try:
            if not enviou_movimento:
                CLIENT_SOCKET.send("GET_STATE".encode('utf-8'))
            
            data = CLIENT_SOCKET.recv(32000).decode('utf-8') 
            if "}{" in data: data = data.split("}{")[0] + "}"
            
            if data:
                estado = json.loads(data)
                desenhar_jogo_online(estado)
        except Exception as e:
            CONECTADO = False
            estado_atual = ESTADO_MENU

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()