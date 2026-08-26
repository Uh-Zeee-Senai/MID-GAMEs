import pygame
import random
import time
import math
import os

try:
    from PIL import Image, ImageSequence
except Exception:
    Image = None
    ImageSequence = None

from core.arduino_controller import enviar_comando
from core.database import obter_ou_criar_jogador, salvar_partida_space_invaders

# --- CONFIGURAÇÕES E CONSTANTES (SEM NÚMEROS MÁGICOS) ---
TELEPORT_CHANCE = 0.50
FREEZE_CHANCE = 0.40

BOSS_FIRST_SPAWN_SCORE = 500
BOSS_SPAWN_CHANCE = 0.012
BOSS_HITS_REQUIRED = 16
BOSS_TIME_MULTIPLIER_ON_DEFEAT = 1.1
BOSS_TIME_DIVISOR_ON_ESCAPE = 1.6

CHARGED_MIN_SCORE = 500
CHARGED_SPAWN_CHANCE = 0.35
CHARGED_BUFF_DURATION = 3.5

BONUS_DURATION = 10.0
BONUS_DROP_CHANCE = 0.05
VELOCIDADE_INIMIGO_MAX = 2.0

MAX_INIMIGOS_TELA = 15 # Limite de horda reduzido (máx 15 por vez)
PODER_UP_TYPES = ['tiro_duplo', 'ataque_area', 'escudo', 'tiro_rapido', 'duplicacao']
POWERUP_META = {
    'tiro_duplo': {'label': 'Tiro Duplo', 'cor': (241, 196, 15)},
    'ataque_area': {'label': 'Área', 'cor': (155, 89, 182)},
    'escudo': {'label': 'Escudo', 'cor': (79, 195, 255)},
    'tiro_rapido': {'label': 'Rapidez', 'cor': (46, 204, 113)},
    'duplicacao': {'label': 'Duplicação', 'cor': (255, 124, 196)},
}

# SISTEMA DE RARIDADE DE MOBS (SUBCHEFE CREEPER MAIS RARO = PESO 6)
MOB_RARITY = {
    'default':  {'nome': 'Comum',                 'peso': 45, 'pontos': 10, 'dano_fuga': 5.0},
    'verde':    {'nome': 'Creeper (Subchefe)',    'peso': 6,  'pontos': 50, 'dano_fuga': 15.0}, # Raro Subchefe (5 HP)
    'gelo':     {'nome': 'Gelo',                  'peso': 18, 'pontos': 20, 'dano_fuga': 10.0},
    'zangado':  {'nome': 'Zangado',               'peso': 15, 'pontos': 20, 'dano_fuga': 10.0},
    'teleport': {'nome': 'Teleport',              'peso': 10, 'pontos': 30, 'dano_fuga': 15.0},
    'charged':  {'nome': 'Charged',               'peso': 6,  'pontos': 35, 'dano_fuga': 15.0},
}

# --- CARREGAMENTO DE SPRITES ---
SPRITES = {}
EXPLOSION_FRAMES = []


def carregar_animacao_explosao():
    """Carrega o GIF de explosão como sequência de frames animados."""
    global EXPLOSION_FRAMES
    if EXPLOSION_FRAMES:
        return EXPLOSION_FRAMES

    caminho = os.path.join(os.path.dirname(__file__), 'sprites', 'explosion.gif')
    if not os.path.exists(caminho):
        EXPLOSION_FRAMES = []
        return EXPLOSION_FRAMES

    try:
        if Image is not None and ImageSequence is not None:
            imagem = Image.open(caminho)
            frames = []
            for frame in ImageSequence.Iterator(imagem):
                frame_rgba = frame.convert('RGBA')
                surface = pygame.image.frombuffer(frame_rgba.tobytes(), frame_rgba.size, 'RGBA')
                frames.append(surface)
            if frames:
                EXPLOSION_FRAMES = frames
                return EXPLOSION_FRAMES
    except Exception:
        pass

    try:
        img = pygame.image.load(caminho).convert_alpha()
        EXPLOSION_FRAMES = [img]
    except Exception:
        EXPLOSION_FRAMES = []

    return EXPLOSION_FRAMES


def carregar_sprites():
    """Carrega e redimensiona os sprites da pasta 'sprites'."""
    pasta_sprites = os.path.join(os.path.dirname(__file__), 'sprites')
    carregar_animacao_explosao()
    
    tamanhos = {
        'nave': (48, 48),
        'tiro': (12, 24),
        'enemy-default': (48, 48),
        'enemy-verde': (72, 72),            # Subchefe Creeper verde (72x72)
        'enemy-especial-verde': (72, 72),
        'enemy-gelo': (48, 48),
        'enemy-yellow': (48, 48),
        'enemy-charged': (48, 48),
        'charged-attack': (80, 80),         # Sprite de raio do Charged
        'enemy-teleport': (48, 48),
        'enemy-zangado': (48, 48),
        'enemy-boss-malware': (96, 96),     # Boss Malware (96x96)
        'explosion': (110, 110),
        'bonus': (32, 32)                   # Item bônus raro (bonus.png)
    }

    files = {
        'nave': 'nave.png',
        'tiro': 'tiro.png',
        'enemy-default': 'enemy-default.png',
        'enemy-verde': 'enemy-especial-verde.png',
        'enemy-especial-verde': 'enemy-especial-verde.png',
        'enemy-gelo': 'enemy-gelo.png',
        'enemy-yellow': 'enemy-yellow.png',
        'enemy-charged': 'enemy-charged.png',
        'charged-attack': 'charged-attack.png',
        'enemy-teleport': 'enemy-teleport.png',
        'enemy-zangado': 'enemy-zangado.png',
        'enemy-boss-malware': 'enemy-boss-malware.png',
        'explosion': 'explosion.gif',
        'bonus': 'bonus.png'
    }

    for key, filename in files.items():
        filepath = os.path.join(pasta_sprites, filename)
        if os.path.exists(filepath):
            try:
                img = pygame.image.load(filepath).convert_alpha()
                SPRITES[key] = pygame.transform.scale(img, tamanhos[key])
            except Exception as e:
                print(f"[Sprite Error] Erro ao carregar {filename}: {e}")
                SPRITES[key] = None
        else:
            SPRITES[key] = None

def novo_inimigo(colunas_x, tipo_forçado=None, pontuacao=0, inimigos_existentes=None):
    """Cria um inimigo respeitando a raridade, tamanho e HP de Subchefe (Creeper Verde = 5 HP)."""
    if tipo_forçado:
        tipo = tipo_forçado
    else:
        if pontuacao >= CHARGED_MIN_SCORE and random.random() < CHARGED_SPAWN_CHANCE:
            tipo = 'charged'
        else:
            tipos_candidatos = ['default', 'verde', 'gelo', 'zangado', 'teleport']
            pesos = [MOB_RARITY[t]['peso'] for t in tipos_candidatos]
            tipo = random.choices(tipos_candidatos, weights=pesos, k=1)[0]

    col_idx = random.randint(0, len(colunas_x) - 1)
    if inimigos_existentes:
        coluna_occup = [a for a in inimigos_existentes if int(a.get('coluna', 0)) == col_idx]
        offset = min(len(coluna_occup) * 38, 120)
        base_y = -100 - random.randint(0, 2) * 30 - offset
    else:
        base_y = random.uniform(-140, -30)

    is_subchefe = (tipo == 'verde')
    w = 72 if is_subchefe else 48
    h = 72 if is_subchefe else 48
    hp = 5 if is_subchefe else 1

    return {
        "tipo": tipo,
        "coluna": col_idx,
        "x": float(colunas_x[col_idx]),
        "x_base": float(colunas_x[col_idx]),
        "y": float(base_y),
        "dx": 0.0,
        "largura": w,
        "altura": h,
        "hp": hp,
        "hp_max": hp,
        "dash_timer": random.uniform(2.0, 4.0),
        "em_dash": False,
        "congelado_ate": 0.0
    }

def novo_boss_malware(colunas_x):
    """Cria o Boss Malware: Reúne TODAS as habilidades (dash, zig-zag, teleporte) e possui 25 HP."""
    col_idx = random.randint(0, len(colunas_x) - 1)
    return {
        "tipo": "boss_malware",
        "coluna": col_idx,
        "x": float(colunas_x[col_idx]),
        "x_base": float(colunas_x[col_idx]),
        "y": -120.0,
        "dx": 0.0,
        "largura": 96,
        "altura": 96,
        "hp": BOSS_HITS_REQUIRED,
        "hp_max": BOSS_HITS_REQUIRED,
        "dash_timer": random.uniform(2.0, 3.5),
        "em_dash": False,
        "congelado_ate": 0.0
    }

def criar_onda_inicial(colunas_x):
    """
    Onda de Apresentação Reorganizada:
    Apresenta os mobs didaticamente incluindo o Subchefe Creeper Verde (5 HP).
    """
    onda = []
    
    # Linha 1: Mobs Comuns (Default)
    for c in [1, 3]:
        o = novo_inimigo(colunas_x, tipo_forçado='default')
        o['y'] = -60.0
        o['x'] = float(colunas_x[c])
        o['coluna'] = c
        onda.append(o)

    # Linha 2: Creeper Verde (Subchefe Maior de 5 HP - Zig-zag)
    o = novo_inimigo(colunas_x, tipo_forçado='verde')
    o['y'] = -120.0
    o['x'] = float(colunas_x[2])
    o['coluna'] = 2
    onda.append(o)

    # Linha 3: Inimigo de Gelo
    o = novo_inimigo(colunas_x, tipo_forçado='gelo')
    o['y'] = -180.0
    o['x'] = float(colunas_x[0])
    o['coluna'] = 0
    onda.append(o)

    # Linha 4: Inimigo Zangado
    o = novo_inimigo(colunas_x, tipo_forçado='zangado')
    o['y'] = -240.0
    o['x'] = float(colunas_x[4])
    o['coluna'] = 4
    onda.append(o)

    # Linha 5: Inimigo Teleport
    o = novo_inimigo(colunas_x, tipo_forçado='teleport')
    o['y'] = -300.0
    o['x'] = float(colunas_x[1])
    o['coluna'] = 1
    onda.append(o)

    # Linha 6: Inimigo Charged
    o = novo_inimigo(colunas_x, tipo_forçado='charged')
    o['y'] = -360.0
    o['x'] = float(colunas_x[3])
    o['coluna'] = 3
    onda.append(o)

    return onda

def rodar_jogo(tela, relogio, arduino, ler_hardware, nome_jogador="Anônimo"):
    carregar_sprites()

    LARGURA, ALTURA = 800, 600
    jogador_x = LARGURA // 2
    velocidade_jogador_max = 12

    COLUNAS_X = [150, 275, 400, 525, 650]

    # CRIANTE DO FUNDO ESTELAR RETRO (ESTRELAS EM CAMADAS COM PARALAXE)
    estrelas = [
        {
            "x": random.randint(0, LARGURA),
            "y": random.randint(0, ALTURA),
            "vel": random.uniform(0.3, 1.8),
            "tam": random.choice([1, 1, 2, 2, 3]),
            "cor": random.choice([(255, 255, 255), (180, 200, 255), (255, 220, 180), (120, 140, 180)])
        }
        for _ in range(80)
    ]

    # FLUXO DA PARTIDA: ONDA INICIAL DE APRESENTAÇÃO -> JOGO NORMAL
    fase_jogo = "ONDA_INICIAL"
    aliens = criar_onda_inicial(COLUNAS_X)

    tiros = []
    explosoes = []
    popups = []
    bonuses = []
    efeitos_raio = []
    ataques_boss = []
    pontuacao = 0
    total_inimigos_derrotados = 0
    tempo_restante = 60.0
    TEMPO_MAXIMO_REF = 60.0

    velocidade_base_inimigo = 0.50

    buff_velocidade_inimigos_ate = 0.0
    bonus_tiro_duplo_ate = 0.0
    bonus_ataque_area_ate = 0.0
    bonus_escudo_ate = 0.0
    bonus_tiro_rapido_ate = 0.0
    bonus_tempo_extra_ate = 0.0
    bonus_duplicacao_ate = 0.0
    escudo_absorvidos = 0

    boss_primeiro_spawnou = False
    boss_ativo = False
    boss_aura_ativo = False
    boss_horda_ativo = False
    boss_ataque_proximo = 0.0
    boss_sequencia_ataque = 0

    fonte_hud = pygame.font.SysFont('Consolas', 18, bold=True)
    fonte_sub = pygame.font.SysFont('Consolas', 14)
    fonte_popup = pygame.font.SysFont('Consolas', 24, bold=True)
    fonte_gameover = pygame.font.SysFont('Consolas', 36, bold=True)

    rodando = True
    game_over = False
    tempo_game_over = 0.0  # Momento em que o game over ocorreu (para cooldown de 5s)
    tempo_final_jogo = 0.0
    COOLDOWN_GAME_OVER = 5.0  # Segundos antes de redirecionar ao menu
    tempo_ultimo_tiro = 0.0
    INTERVALO_TIRO = 0.18
    tempo_anterior_frame = time.time()
    tempo_inicio_partida = time.time()

    btn_tiro_solto_game_over = False

    while rodando:
        agora = time.time()
        dt = agora - tempo_anterior_frame
        tempo_anterior_frame = agora

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    rodando = False
                elif game_over and (agora - tempo_game_over >= 1.5) and (evento.key == pygame.K_SPACE or evento.key == pygame.K_RETURN):
                    return rodar_jogo(tela, relogio, arduino, ler_hardware, nome_jogador)

        # Lê entradas do Hardware / Teclado
        joy_x, joy_y, btn_menu, btn_tiro = ler_hardware(arduino)

        if btn_menu == 0:
            if game_over:
                rodando = False
                break
            else:
                rodando = False
                pygame.time.wait(300)
                break

        if game_over:
            tela.fill((15, 10, 20))

            # Se o botão de tiro foi solto pelo menos uma vez durante a tela de Game Over
            if btn_tiro == 1:
                btn_tiro_solto_game_over = True

            # Conta o tempo restante do cooldown
            decorrido_go = agora - tempo_game_over
            cooldown_restante = max(0.0, COOLDOWN_GAME_OVER - decorrido_go)

            # Se o cooldown expirou, volta ao menu automaticamente
            if cooldown_restante <= 0:
                rodando = False
                break

            # --- TELA DE GAME OVER ---
            txt_go = fonte_gameover.render("GAME OVER", True, (231, 76, 60))
            tela.blit(txt_go, (LARGURA // 2 - txt_go.get_width() // 2, 170))

            tempo_sobrevivido_go = tempo_final_jogo if tempo_final_jogo > 0 else max(0.0, agora - tempo_inicio_partida)
            tempo_go_fmt = f"{int(tempo_sobrevivido_go // 60):02d}:{int(tempo_sobrevivido_go % 60):02d}"
            txt_pts = fonte_hud.render(f"PONTUAÇÃO FINAL: {pontuacao:04d}  |  ABATES: {total_inimigos_derrotados}  |  TEMPO: {tempo_go_fmt}", True, (255, 255, 255))
            tela.blit(txt_pts, (LARGURA // 2 - txt_pts.get_width() // 2, 240))

            # BARRA DE COOLDOWN (conta regressiva visual)
            bar_go_w = 340
            bar_go_x = LARGURA // 2 - bar_go_w // 2
            bar_go_y = 310
            pct_cd = cooldown_restante / COOLDOWN_GAME_OVER
            pygame.draw.rect(tela, (40, 20, 20), (bar_go_x, bar_go_y, bar_go_w, 16), border_radius=8)
            pygame.draw.rect(tela, (231, 76, 60), (bar_go_x, bar_go_y, int(bar_go_w * pct_cd), 16), border_radius=8)
            pygame.draw.rect(tela, (180, 60, 60), (bar_go_x, bar_go_y, bar_go_w, 16), width=2, border_radius=8)

            txt_cd = fonte_sub.render(f"Voltando ao menu em {cooldown_restante:.1f}s...", True, (200, 140, 140))
            tela.blit(txt_cd, (LARGURA // 2 - txt_cd.get_width() // 2, bar_go_y + 26))

            # Bloqueia reinício prematuro durante os primeiros 1.5s
            lockout_ativo = (decorrido_go < 1.5)
            if lockout_ativo:
                txt_reinicio = fonte_sub.render("Aguarde...", True, (120, 130, 150))
            else:
                txt_reinicio = fonte_sub.render("Pressione Botão de Tiro para jogar novamente", True, (160, 170, 190))
            
            tela.blit(txt_reinicio, (LARGURA // 2 - txt_reinicio.get_width() // 2, 380))

            # Reinicia apenas se tiver passado 1.5s, o botão foi solto e pressionado novamente
            if not lockout_ativo and btn_tiro_solto_game_over and btn_tiro == 0:
                pygame.time.wait(300)
                return rodar_jogo(tela, relogio, arduino, ler_hardware, nome_jogador)

            pygame.display.flip()
            relogio.tick(60)
            continue

        if game_over:
            pygame.display.flip()
            relogio.tick(60)
            continue

        # TEMPO CONTANDO CONTINUAMENTE
        tempo_restante -= dt
        if tempo_restante <= 0:
            tempo_restante = 0
            if not game_over:
                game_over = True
                tempo_final_jogo = max(0.0, agora - tempo_inicio_partida)
                tempo_game_over = agora  # Registra o momento exato do game over
                enviar_comando(arduino, 'M')

                # Salva a pontuação no banco de dados SQLite
                if nome_jogador:
                    jogador_id = obter_ou_criar_jogador(nome_jogador)
                    if jogador_id:
                        salvar_partida_space_invaders(jogador_id, pontuacao, tempo_final_jogo)

        # --- TRANSIÇÃO E SPAWN DO JOGO NORMAL ---
        if fase_jogo == "ONDA_INICIAL":
            if len(aliens) == 0:
                fase_jogo = "JOGO_NORMAL"
                popups.append({
                    "texto": "► JOGO NORMAL INICIADO! ◄",
                    "cor": (46, 204, 113),
                    "x": LARGURA // 2,
                    "y": 200,
                    "criado": agora
                })
        else:
            # HORDA MAIS RÁPIDA NO COMEÇO E PROGRESSÃO MAIS GRADUAL.
            # A aura do boss agora aumenta a horda de forma moderada, sem virar um enjoo de inimigos.
            num_inimigos_desejado = min(MAX_INIMIGOS_TELA, 9 + (pontuacao // 160))

            mult_horda = 3.0 if boss_horda_ativo else 1.0
            horda_extra = 4 if boss_horda_ativo else 0
            num_horda_com_aura = min(MAX_INIMIGOS_TELA, max(num_inimigos_desejado + horda_extra, int(num_inimigos_desejado * mult_horda)))

            while len(aliens) < num_horda_com_aura:
                if (not boss_primeiro_spawnou) and (pontuacao >= BOSS_FIRST_SPAWN_SCORE):
                    boss_primeiro_spawnou = True
                    boss_ativo = True
                    boss_aura_ativo = True
                    boss_horda_ativo = True
                    boss_ataque_proximo = agora + 1.0
                    aliens.append(novo_boss_malware(COLUNAS_X))
                    popups.append({
                        "texto": "☠ BOSS MALWARE DETECTADO! HORDA INVOCADA! ☠",
                        "cor": (231, 76, 60),
                        "x": LARGURA // 2,
                        "y": 180,
                        "criado": agora
                    })

                elif (boss_primeiro_spawnou) and (not boss_ativo) and (pontuacao >= BOSS_FIRST_SPAWN_SCORE) and (random.random() < BOSS_SPAWN_CHANCE):
                    boss_ativo = True
                    boss_aura_ativo = True
                    boss_horda_ativo = True
                    boss_ataque_proximo = agora + 1.0
                    aliens.append(novo_boss_malware(COLUNAS_X))
                    popups.append({
                        "texto": "☠ BOSS MALWARE SURGIU! ☠",
                        "cor": (231, 76, 60),
                        "x": LARGURA // 2,
                        "y": 180,
                        "criado": agora
                    })
                else:
                    aliens.append(novo_inimigo(COLUNAS_X, pontuacao=pontuacao, inimigos_existentes=aliens))

        # MOVIMENTAÇÃO DO JOGADOR
        MIN_X = 45
        MAX_X = LARGURA - 45

        if joy_x < 400: # Esquerda
            fator = (400.0 - joy_x) / 400.0
            vel = max(5, int(velocidade_jogador_max * fator))
            jogador_x = max(MIN_X, jogador_x - vel)
        elif joy_x > 600: # Direita
            fator = (joy_x - 600.0) / 423.0
            vel = max(5, int(velocidade_jogador_max * fator))
            jogador_x = min(MAX_X, jogador_x + vel)

        # DISPAROS DO JOGADOR
        tiro_duplo_ativo = (agora < bonus_tiro_duplo_ate)
        ataque_area_ativo = (agora < bonus_ataque_area_ate)
        duplicacao_ativa = (agora < bonus_duplicacao_ate)
        tiro_rapido_ativo = (agora < bonus_tiro_rapido_ate) and not (tiro_duplo_ativo or duplicacao_ativa)
        escudo_ativo = (agora < bonus_escudo_ate)
        INTERVALO_TIRO_ATUAL = 0.08 if tiro_rapido_ativo else INTERVALO_TIRO

        if btn_tiro == 0 and (agora - tempo_ultimo_tiro >= INTERVALO_TIRO_ATUAL):
            posicoes_tiro = [jogador_x]
            if tiro_duplo_ativo:
                posicoes_tiro = [jogador_x - 14, jogador_x + 14]

            for x_tiro in posicoes_tiro:
                tiros.append({"x": x_tiro, "y": ALTURA - 60, "area": ataque_area_ativo})

            if duplicacao_ativa:
                for offset in (-60, 60):
                    tiros.append({"x": jogador_x + offset, "y": ALTURA - 60, "area": False, "duplicacao": True})

            enviar_comando(arduino, 'T')
            tempo_ultimo_tiro = agora

        # Atualiza Posição dos Tiros
        for t in tiros[:]:
            t['y'] -= 15
            if t['y'] < 0:
                tiros.remove(t)

        # ATAQUE DIRETO DO BOSS: dois disparos alternados em direções diferentes, com centro livre como zona segura
        if boss_ativo and agora >= boss_ataque_proximo:
            boss = next((a for a in aliens if a['tipo'] == 'boss_malware'), None)
            if boss is not None:
                alvo_x = jogador_x
                alvo_y = ALTURA - 45
                centro_seguro = LARGURA // 2
                dx = alvo_x - boss['x']
                dy = alvo_y - (boss['y'] + 35)
                dist = max(1.0, math.hypot(dx, dy))

                # padrão alternado: 2 disparos em lados opostos, com centro livre
                if boss_sequencia_ataque % 2 == 0:
                    grupos = [(-1, -0.28), (1, 0.28)]
                else:
                    grupos = [(-1, -0.12), (1, 0.12)]

                boss_sequencia_ataque += 1

                for lado, inclinacao in grupos:
                    base_dir_x = math.copysign(1.0, alvo_x - centro_seguro if lado < 0 else centro_seguro - alvo_x)
                    angulo_base = math.atan2(dy, dx)
                    for proj_idx in range(3):
                        spread = (proj_idx - 1) * 0.22
                        angulo = angulo_base + inclinacao + spread * lado
                        velocidade = 6
                        ataques_boss.append({
                            'x': boss['x'] + (lado * 18),
                            'y': boss['y'] + 35,
                            'vx': math.cos(angulo) * velocidade,
                            'vy': math.sin(angulo) * velocidade,
                            'raio': 9,
                            'criado': agora,
                        })

                boss_ataque_proximo = agora + 1.2

        for atk in ataques_boss[:]:
            atk['x'] += atk['vx'] * 60 * dt
            atk['y'] += atk['vy'] * 60 * dt

            if (abs(atk['x'] - jogador_x) < 26) and (abs(atk['y'] - (ALTURA - 45)) < 24):
                if agora < bonus_escudo_ate and escudo_absorvidos < 1:
                    escudo_absorvidos += 1
                    bonus_escudo_ate = 0.0
                    popups.append({
                        "texto": "🛡 BLOQUEADO", "cor": (79, 195, 255), "x": jogador_x, "y": ALTURA - 80, "criado": agora
                    })
                    popups.append({
                        "texto": "🛡 ESCUDO QUEBRADO", "cor": (120, 140, 180), "x": jogador_x, "y": ALTURA - 110, "criado": agora
                    })
                    ataques_boss.remove(atk)
                    continue

                tempo_restante -= 25.0
                popups.append({
                    "texto": "-25s", "cor": (231, 76, 60), "x": jogador_x, "y": ALTURA - 80, "criado": agora
                })
                ataques_boss.remove(atk)
            elif atk['y'] > ALTURA + 30 or atk['x'] < -50 or atk['x'] > LARGURA + 50:
                ataques_boss.remove(atk)

        # Atualiza Itens de Bônus Flutuantes (Usando bonus.png)
        for b in bonuses[:]:
            b['y'] += 2.0
            if (abs(b['x'] - jogador_x) < 35) and (b['y'] > ALTURA - 75):
                if b['tipo'] == 'tiro_duplo':
                    bonus_tiro_duplo_ate = agora + BONUS_DURATION
                    popups.append({"texto": "⚡ TIRO DUPLO ATIVADO!", "cor": (241, 196, 15), "x": jogador_x, "y": ALTURA - 90, "criado": agora})
                elif b['tipo'] == 'ataque_area':
                    bonus_ataque_area_ate = agora + BONUS_DURATION
                    popups.append({"texto": "💥 ATAQUE EM ÁREA ATIVADO!", "cor": (155, 89, 182), "x": jogador_x, "y": ALTURA - 90, "criado": agora})
                elif b['tipo'] == 'escudo':
                    bonus_escudo_ate = agora + BONUS_DURATION
                    escudo_absorvidos = 0
                    popups.append({"texto": "🛡 ESCUDO ATIVADO!", "cor": (79, 195, 255), "x": jogador_x, "y": ALTURA - 90, "criado": agora})
                elif b['tipo'] == 'tiro_rapido':
                    bonus_tiro_rapido_ate = agora + BONUS_DURATION
                    popups.append({"texto": "⚙ FIRING BOOST!", "cor": (46, 204, 113), "x": jogador_x, "y": ALTURA - 90, "criado": agora})
                elif b['tipo'] == 'duplicacao':
                    bonus_duplicacao_ate = agora + BONUS_DURATION
                    popups.append({"texto": "✦ DUPLICAÇÃO ATIVA! ✦", "cor": (255, 124, 196), "x": jogador_x, "y": ALTURA - 90, "criado": agora})

                enviar_comando(arduino, 'E')
                bonuses.remove(b)
            elif b['y'] > ALTURA:
                bonuses.remove(b)

        # MOVIMENTAÇÃO DOS INIMIGOS E HABILIDADES ESPECIAIS
        buff_velocidade_ativo = (agora < buff_velocidade_inimigos_ate)

        for a in aliens[:]:
            if agora < a.get('congelado_ate', 0.0):
                continue

            mult_buff = 1.35 if buff_velocidade_ativo else 1.0
            vel_atual = min(velocidade_base_inimigo * mult_buff, VELOCIDADE_INIMIGO_MAX)

            if a['tipo'] == 'verde': # Subchefe Creeper Verde (Movimentação Zig-Zag)
                a['y'] += vel_atual * 0.8
                a['x'] = a['x_base'] + math.sin(a['y'] * 0.04) * 80.0
            elif a['tipo'] == 'zangado':
                a['dash_timer'] -= dt
                if a['dash_timer'] <= 0:
                    a['em_dash'] = True
                    if a['dash_timer'] < -0.8:
                        a['em_dash'] = False
                        a['dash_timer'] = random.uniform(2.5, 4.5)

                if a['em_dash']:
                    a['y'] += vel_atual * 2.2
                else:
                    a['y'] += vel_atual
                a['x'] = a['x_base']
            elif a['tipo'] == 'gelo':
                a['y'] += vel_atual * 0.85
                a['x'] = a['x_base'] + math.sin(a['y'] * 0.08) * 15.0
            elif a['tipo'] == 'boss_malware':
                # BOSS FLUTUA NO TOPO: Movimentação lateral + dash, mas NUNCA desce da zona segura
                BOSS_Y_LIMITE = 220.0  # Limite inferior: boss não passa desta linha
                a['dash_timer'] -= dt
                if a['dash_timer'] <= 0:
                    a['em_dash'] = True
                    if a['dash_timer'] < -0.8:
                        a['em_dash'] = False
                        a['dash_timer'] = random.uniform(2.5, 4.0)

                # Movimento vertical suave (oscila ao redor de y=80-120)
                a['y'] = 80.0 + math.sin(agora * 0.8 + a['x_base'] * 0.01) * 40.0
                a['x'] = a['x_base'] + math.sin(agora * 1.1) * 180.0
                # Garante que nunca ultrapasse o limite inferior
                if a['y'] > BOSS_Y_LIMITE:
                    a['y'] = BOSS_Y_LIMITE
            else:
                a['y'] += vel_atual
                a['x'] = a['x_base']

            # CASO O INIMIGO PASSE PELA BORDA DE BAIXO
            # BOSS MALWARE NUNCA ESCAPA: Fica preso acima (movimento controlado acima)
            if a['y'] > ALTURA - 75 and a['tipo'] != 'boss_malware':
                dano = MOB_RARITY.get(a['tipo'], {}).get('dano_fuga', 5.0)
                # AURA DO BOSS: Inimigos comuns causam o DOBRO DO DANO de fuga!
                if boss_aura_ativo:
                    dano *= 2.4
                    popups.append({"texto": f"☠ AURA!", "cor": (231, 76, 60), "x": a['x'], "y": ALTURA - 90, "criado": agora})
                elif a['tipo'] == 'verde':
                    popups.append({"texto": "!", "cor": (231, 76, 60), "x": a['x'], "y": ALTURA - 90, "criado": agora})
                tempo_restante -= dano

                if a in aliens:
                    aliens.remove(a)
                    if fase_jogo == "JOGO_NORMAL":
                        aliens.append(novo_inimigo(COLUNAS_X, pontuacao=pontuacao))

            # COLISÃO E PROCESSAMENTO DE DANO
            ax, ay = a['x'], a['y']
            w, h = a['largura'], a['altura']
            
            for t in tiros[:]:
                eh_tiro_area = t.get('area', False)
                dist_impacto = math.hypot(ax - t['x'], ay - t['y'])
                colidiu_direto = (ax - w//2 < t['x'] < ax + w//2) and (ay - 10 < t['y'] < ay + h + 10)

                if colidiu_direto or (eh_tiro_area and dist_impacto <= 120.0):
                    
                    # TELEPORTE (50% de chance para Teleport e Boss Malware)
                    if (a['tipo'] in ['teleport', 'boss_malware']) and random.random() < TELEPORT_CHANCE:
                        nova_col = random.randint(0, len(COLUNAS_X) - 1)
                        a['coluna'] = nova_col
                        a['x'] = float(COLUNAS_X[nova_col])
                        a['x_base'] = float(COLUNAS_X[nova_col])
                        a['y'] = max(30.0, a['y'] - random.uniform(30, 80))

                        popups.append({"texto": "↗", "cor": (155, 89, 182), "x": a['x'], "y": a['y'], "criado": agora})
                        if t in tiros and not eh_tiro_area:
                            tiros.remove(t)
                        continue

                    # Reduz HP
                    a['hp'] -= 1
                    if t in tiros:
                        tiros.remove(t)

                    enviar_comando(arduino, 'M')

                    # DERROTA DO INIMIGO (HP <= 0)
                    if a['hp'] <= 0:
                        pts_ganhos = 100 if a['tipo'] == 'boss_malware' else MOB_RARITY.get(a['tipo'], {}).get('pontos', 10)
                        pontuacao += pts_ganhos
                        total_inimigos_derrotados += 1
                        velocidade_base_inimigo = min(velocidade_base_inimigo + 0.006, 0.92)

                        tam_exp = 240 if a['tipo'] == 'boss_malware' else (360 if a['tipo'] == 'verde' else 110)
                        explosoes.append({"x": ax, "y": ay, "criado": agora, "tamanho": tam_exp, "tipo": a['tipo']})

                        # DROP DE POWER-UP: chance aumentada enquanto o boss está vivo
                        chance_drop = BONUS_DROP_CHANCE * 2.5 if boss_ativo else BONUS_DROP_CHANCE
                        if random.random() < min(0.9, chance_drop):
                            tipo_b = random.choice(PODER_UP_TYPES)
                            bonuses.append({"tipo": tipo_b, "x": ax, "y": ay})

                        # HABILIDADE GELO: 40% de chance de congelar apenas inimigos próximos
                        if a['tipo'] == 'gelo' and random.random() < FREEZE_CHANCE:
                            RAIO_CONGELAMENTO = 220.0
                            for outro in aliens:
                                dist = math.hypot(outro['x'] - ax, outro['y'] - ay)
                                if dist <= RAIO_CONGELAMENTO:
                                    outro['congelado_ate'] = agora + 3.0

                            popups.append({"texto": "❄", "cor": (52, 152, 219), "x": ax, "y": ay - 30, "criado": agora})

                        # HABILIDADE CHARGED: Buff de velocidade + efeito do sprite charged-attack.png
                        if a['tipo'] == 'charged':
                            buff_velocidade_inimigos_ate = agora + CHARGED_BUFF_DURATION
                            efeitos_raio.append({"x": ax, "y": ay, "criado": agora})
                            popups.append({"texto": "⚡", "cor": (230, 126, 34), "x": ax, "y": ay - 20, "criado": agora})

                        # SUBCHEFE CREEPER VERDE DERROTADO: +30s LOOT + EXPLODE TODOS OS INIMIGOS (EXCETO BOSS MALWARE!)
                        if a['tipo'] == 'verde':
                            tempo_restante += 30.0
                            enviar_comando(arduino, 'E')
                            popups.append({"texto": "+30s", "cor": (46, 204, 113), "x": ax, "y": ay - 30, "criado": agora})

                            # EXPLODE INIMIGOS COMUNS (EXCETO O BOSS MALWARE!)
                            for outro in aliens[:]:
                                if outro != a and outro['tipo'] != 'boss_malware':
                                    explosoes.append({"x": outro['x'], "y": outro['y'], "criado": agora, "tamanho": 110})
                                    if outro in aliens:
                                        aliens.remove(outro)

                        # BOSS MALWARE DERROTADO: Multiplicar tempo atual por 1.25 + Aura desativada + Bomba de área gigante
                        elif a['tipo'] == 'boss_malware':
                            tempo_restante = max(0.0, tempo_restante * BOSS_TIME_MULTIPLIER_ON_DEFEAT)
                            boss_ativo = False
                            boss_aura_ativo = False
                            boss_horda_ativo = False
                            boss_ataque_proximo = agora + 999.0
                            ataques_boss.clear()
                            enviar_comando(arduino, 'E')

                            popups.append({"texto": "★ VITÓRIA ★", "cor": (241, 196, 15), "x": LARGURA // 2, "y": 180, "criado": agora})

                            for outro in aliens[:]:
                                if outro != a:
                                    explosoes.append({"x": outro['x'], "y": outro['y'], "criado": agora, "tamanho": 110})
                                    if outro in aliens:
                                        aliens.remove(outro)
                        else:
                            tempo_restante += 2.0
                            popups.append({"texto": "+2s", "cor": (46, 204, 113), "x": ax, "y": ay, "criado": agora})

                        if a in aliens:
                            aliens.remove(a)
                            if fase_jogo == "JOGO_NORMAL":
                                aliens.append(novo_inimigo(COLUNAS_X, pontuacao=pontuacao, inimigos_existentes=aliens))

        # DESENHO NA TELA
        tela.fill((10, 12, 22))

        # FUNDO ESTELAR RETRO DINÂMICO (COM PARALAXE E DIVERSAS CORES DE ESTRELAS)
        for est in estrelas:
            est['y'] = (est['y'] + est['vel']) % ALTURA
            pygame.draw.circle(tela, est['cor'], (int(est['x']), int(est['y'])), est['tam'])

        # Linhas guia suaves das 5 Colunas
        for cx in COLUNAS_X:
            pygame.draw.line(tela, (25, 30, 48), (cx, 50), (cx, ALTURA - 20), 1)

        # NAVE DO JOGADOR
        px = jogador_x
        py = ALTURA - 50
        if SPRITES.get('nave'):
            tela.blit(SPRITES['nave'], (px - 24, py - 24))
        else:
            pygame.draw.polygon(tela, (46, 204, 113), [(px, py - 22), (px - 24, py + 10), (px + 24, py + 10)])

        if agora < bonus_duplicacao_ate:
            for offset in (-60, 60):
                clone_x = jogador_x + offset
                clone_img = SPRITES.get('nave')
                if clone_img:
                    clone_surface = clone_img.copy()
                    clone_surface.set_alpha(85)
                    tela.blit(clone_surface, (clone_x - 24, py - 24))
                else:
                    pygame.draw.polygon(tela, (46, 204, 113), [(clone_x, py - 22), (clone_x - 24, py + 10), (clone_x + 24, py + 10)], 2)

        # TIROS DO JOGADOR
        for t in tiros:
            cor_t = (155, 89, 182) if t.get('area', False) else (241, 196, 15)
            if SPRITES.get('tiro'):
                tela.blit(SPRITES['tiro'], (t['x'] - 6, t['y']))
            else:
                pygame.draw.rect(tela, cor_t, (t['x'] - 2, t['y'], 5, 14), border_radius=2)

        # ATAQUES DIRETOS DO BOSS
        for atk in ataques_boss:
            pygame.draw.circle(tela, (231, 76, 60), (int(atk['x']), int(atk['y'])), atk['raio'])
            pygame.draw.circle(tela, (255, 180, 180), (int(atk['x']), int(atk['y'])), max(3, atk['raio'] // 2))

        # ITENS DE BÔNUS FLUTUANTES EM BOLINHAS COLORIDAS (SEM ENGENHARIA)
        for b in bonuses:
            tipo = b.get('tipo', 'tiro_duplo')
            cor = POWERUP_META.get(tipo, POWERUP_META['tiro_duplo'])['cor']
            pygame.draw.circle(tela, cor, (int(b['x']), int(b['y'])), 12)
            pygame.draw.circle(tela, (255, 255, 255), (int(b['x']) - 3, int(b['y']) - 3), 4)

        # RENDERIZAÇÃO DO EFEITO VISUAL CHARGED-ATTACK (RAIO CHARGED)
        for ef in efeitos_raio[:]:
            if agora - ef['criado'] > 0.6:
                efeitos_raio.remove(ef)
                continue
            if SPRITES.get('charged-attack'):
                tela.blit(SPRITES['charged-attack'], (int(ef['x']) - 40, int(ef['y']) - 40))

        # INIMIGOS, SUBCHEFE E BOSS MALWARE
        for a in aliens:
            ax, ay = int(a['x']), int(a['y'])
            if ay + a['altura'] > 0:
                esta_congelado = agora < a.get('congelado_ate', 0.0)

                # Desenha Boss Malware (20 HP) ou Subchefe Creeper (5 HP)
                if a['tipo'] in ['boss_malware', 'verde']:
                    sp_key = 'enemy-boss-malware' if a['tipo'] == 'boss_malware' else 'enemy-verde'

                    # EFEITO AURA DO BOSS: Pulso vermelho brilhante ao redor do sprite
                    if a['tipo'] == 'boss_malware' and boss_aura_ativo:
                        pulso = int(20 + 15 * math.sin(agora * 6.0))
                        aura_surf = pygame.Surface((a['largura'] + pulso*2, a['altura'] + pulso*2), pygame.SRCALPHA)
                        aura_surf.fill((0, 0, 0, 0))
                        pygame.draw.ellipse(aura_surf, (200, 30, 30, 90), (0, 0, a['largura'] + pulso*2, a['altura'] + pulso*2))
                        pygame.draw.ellipse(aura_surf, (255, 80, 0, 50), (pulso//2, pulso//2, a['largura'] + pulso, a['altura'] + pulso))
                        tela.blit(aura_surf, (ax - a['largura']//2 - pulso, ay - pulso))

                    if SPRITES.get(sp_key):
                        tela.blit(SPRITES[sp_key], (ax - a['largura']//2, ay))
                    else:
                        cor_c = (231, 76, 60) if a['tipo'] == 'boss_malware' else (46, 204, 113)
                        pygame.draw.rect(tela, cor_c, (ax - a['largura']//2, ay, a['largura'], a['altura']), border_radius=12)

                    # BARRA DE VIDA DOS CHEFES / SUBCHEFES (5 HP Creeper / 20 HP Boss)
                    if a['hp_max'] > 1:
                        hp_w = 70 if a['tipo'] == 'verde' else 80
                        hp_x = ax - hp_w // 2
                        hp_y = ay - 12
                        pygame.draw.rect(tela, (40, 20, 20), (hp_x, hp_y, hp_w, 7), border_radius=3)
                        fill_hp = int(hp_w * (a['hp'] / float(a['hp_max'])))
                        if fill_hp > 0:
                            cor_hp = (46, 204, 113) if a['tipo'] == 'verde' else (231, 76, 60)
                            pygame.draw.rect(tela, cor_hp, (hp_x, hp_y, fill_hp, 7), border_radius=3)
                        pygame.draw.rect(tela, (255, 255, 255), (hp_x, hp_y, hp_w, 7), width=1, border_radius=3)

                else:
                    sprite_key = f"enemy-{a['tipo']}"
                    sprite_img = SPRITES.get(sprite_key) or SPRITES.get('enemy-default')

                    if sprite_img:
                        tela.blit(sprite_img, (ax - a['largura']//2, ay))
                    else:
                        pygame.draw.rect(tela, (231, 76, 60), (ax - a['largura']//2, ay, a['largura'], a['altura']), border_radius=8)

                if esta_congelado:
                    s_ice = pygame.Surface((a['largura'] + 8, a['altura'] + 8), pygame.SRCALPHA)
                    s_ice.fill((52, 152, 219, 140))
                    tela.blit(s_ice, (ax - a['largura']//2 - 4, ay - 4))
                    pygame.draw.rect(tela, (200, 240, 255), (ax - a['largura']//2 - 4, ay - 4, a['largura'] + 8, a['altura'] + 8), width=2, border_radius=6)

        # RENDERIZAÇÃO DAS EXPLOSÕES USANDO A ANIMAÇÃO DO GIF explosion.gif
        for ex in explosoes[:]:
            decorrido_exp = agora - ex['criado']
            if decorrido_exp > 0.5:
                explosoes.remove(ex)
                continue

            progresso = decorrido_exp / 0.5
            tam_max = ex.get('tamanho', 110)
            tam_atual = int(tam_max * (0.5 + 0.5 * progresso))

            if EXPLOSION_FRAMES:
                fator_extra = 1.7 if ex.get('tipo') == 'verde' else 1.0
                tam_final = max(80, int(tam_atual * fator_extra))
                idx = min(len(EXPLOSION_FRAMES) - 1, int(progresso * len(EXPLOSION_FRAMES)))
                frame = EXPLOSION_FRAMES[idx]
                img_exp = pygame.transform.smoothscale(frame, (tam_final, tam_final))
                tela.blit(img_exp, (int(ex['x']) - tam_final // 2, int(ex['y']) - tam_final // 2))
            else:
                pygame.draw.circle(tela, (241, 196, 15), (int(ex['x']), int(ex['y'])), tam_atual // 2)

        # --- HUD SUPERIOR ---
        pygame.draw.rect(tela, (20, 25, 38), (0, 0, LARGURA, 50))
        pygame.draw.line(tela, (45, 52, 70), (0, 50), (LARGURA, 50), 2)

        tempo_sobrevivido = tempo_final_jogo if game_over else max(0.0, agora - tempo_inicio_partida)
        tempo_fmt = f"{int(tempo_sobrevivido // 60):02d}:{int(tempo_sobrevivido % 60):02d}"
        txt_score = fonte_hud.render(f"PTS: {pontuacao:04d}  |  TEMPO: {tempo_fmt}", True, (255, 255, 255))
        tela.blit(txt_score, (20, 15))

        # BARRA DE TEMPO DE VIDA
        bar_x, bar_y, bar_w, bar_h = 238, 42, 324, 18
        pygame.draw.rect(tela, (30, 35, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=9)

        pct_tempo = max(0.0, min(1.0, tempo_restante / TEMPO_MAXIMO_REF))
        fill_w = int(bar_w * pct_tempo)

        if pct_tempo > 0.5:
            cor_barra = (46, 204, 113)
        elif pct_tempo > 0.25:
            cor_barra = (241, 196, 15)
        else:
            cor_barra = (231, 76, 60)

        if fill_w > 0:
            pygame.draw.rect(tela, cor_barra, (bar_x, bar_y, fill_w, bar_h), border_radius=9)
        pygame.draw.rect(tela, (70, 80, 100), (bar_x, bar_y, bar_w, bar_h), width=2, border_radius=9)

        txt_tempo = fonte_hud.render(f"TEMPO: {tempo_restante:4.1f}s", True, (255, 255, 255))
        tela.blit(txt_tempo, (bar_x + bar_w//2 - txt_tempo.get_width()//2, bar_y - 24))

        status_str = f"ARDUINO ({arduino.port})" if arduino else "TECLADO"
        cor_st = (46, 204, 113) if arduino else (241, 196, 15)
        txt_status = fonte_hud.render(status_str, True, cor_st)
        tela.blit(txt_status, (LARGURA - txt_status.get_width() - 20, 15))

        # HUD DE POWER-UPS ATIVOS
        ativos = []
        for key, meta in POWERUP_META.items():
            timer = {
                'tiro_duplo': bonus_tiro_duplo_ate,
                'ataque_area': bonus_ataque_area_ate,
                'escudo': bonus_escudo_ate,
                'tiro_rapido': bonus_tiro_rapido_ate,
                'duplicacao': bonus_duplicacao_ate,
            }.get(key, 0.0)
            if agora < timer:
                ativos.append((key, meta['label'], meta['cor'], max(0.0, timer - agora)))

        if ativos:
            panel_x = 18
            panel_y = 60
            panel_w = 220
            panel_h = 18 + len(ativos) * 20
            pygame.draw.rect(tela, (18, 23, 34), (panel_x, panel_y, panel_w, panel_h), border_radius=10)
            pygame.draw.rect(tela, (80, 90, 116), (panel_x, panel_y, panel_w, panel_h), width=1, border_radius=10)

            for idx, (key, label, cor, restante) in enumerate(ativos):
                py = panel_y + 12 + idx * 20
                pygame.draw.circle(tela, cor, (panel_x + 12, py + 6), 6)
                txt_p = fonte_sub.render(f"{label}: {restante:.1f}s", True, (240, 245, 255))
                tela.blit(txt_p, (panel_x + 24, py - 2))

        # POPUPS FLUTUANTES
        for p in popups[:]:
            decorrido = agora - p['criado']
            if decorrido > 1.4:
                popups.remove(p)
                continue

            y_popup = p['y'] - int(decorrido * 35)
            x_popup = p['x']

            txt_pop = fonte_popup.render(p['texto'], True, p['cor'])
            tela.blit(txt_pop, (x_popup - txt_pop.get_width()//2, y_popup))

        # RODAPÉ DE INSTRUÇÕES
        txt_fase = f"FASE: {fase_jogo}"
        txt_dica = fonte_sub.render(f"{txt_fase} | Fundo Estelar Retro | Creeper não afeta Malware | Horda Máx 15", True, (140, 150, 170))
        tela.blit(txt_dica, (LARGURA // 2 - txt_dica.get_width() // 2, ALTURA - 20))

        pygame.display.flip()
        relogio.tick(60)

    return
