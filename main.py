import pygame
import sys
import os
import time
import math
import array
from core.arduino_controller import conectar_arduino, ler_hardware, enviar_comando
from core import teste_controle
from core.database import init_db
from core.nome_modal import solicitar_nome_jogador
from core import rankings_ui
from space_invaders import jogo as space_invaders_jogo
from adventure import jogo as adventure_jogo
from adventure.nivel_modal import selecionar_nivel_adventure


def _gerar_tone(frequencia=440, duracao_ms=60, volume=0.18):
    # Sem áudio do Python; apenas o buzzer do Arduino deve emitir sons.
    return None


def main():
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass
    init_db()  # Inicializa o banco de dados SQLite (arcade.db)

    LARGURA, ALTURA = 800, 600
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    relogio = pygame.time.Clock()

    # Conecta ao Arduino se disponível
    arduino = conectar_arduino()

    opcao_menu = 0

    # Paleta principal mais consistente com a tela inicial
    COR_FUNDO = (10, 8, 22)
    COR_NEON_ROSA = (255, 0, 128)
    COR_NEON_AZUL = (95, 145, 255)
    COR_NEON_AMARELO = (255, 210, 110)
    COR_NEON_VERDE = (92, 210, 140)
    COR_TEXTO_MUTED = (140, 150, 180)
    COR_CARD_BG = (18, 16, 32)
    COR_CARD_SEL = (35, 26, 48)
    COR_BRANCO = (245, 245, 245)
    COR_PANEL = (17, 15, 28)

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FONTE_PIXEL = os.path.join(BASE_DIR, 'assets', 'fonts', 'PressStart2P-Regular.ttf')
    SPRITES_SPACE_DIR = os.path.join(BASE_DIR, 'space_invaders', 'sprites')

    nave_tela_inicial = pygame.image.load(os.path.join(SPRITES_SPACE_DIR, 'nave-tela-inicial.png')).convert_alpha()
    alien_tela_inicial = pygame.image.load(os.path.join(SPRITES_SPACE_DIR, 'alien.png')).convert_alpha()

    def carregar_fonte_pixel(tamanho):
        if os.path.exists(FONTE_PIXEL):
            return pygame.font.Font(FONTE_PIXEL, tamanho)

        candidatos = [
            'Press Start 2P', 'Press Start K', 'Courier New', 'Consolas', 'Arial'
        ]
        for nome in candidatos:
            try:
                caminho = pygame.font.match_font(nome)
                if caminho:
                    return pygame.font.Font(caminho, tamanho)
            except Exception:
                pass
        return pygame.font.SysFont('Consolas', tamanho, bold=True)

    fonte_titulo_lg = carregar_fonte_pixel(54)
    fonte_titulo_md = carregar_fonte_pixel(38)
    fonte_card_tit = carregar_fonte_pixel(20)
    fonte_card_sub = carregar_fonte_pixel(13)
    fonte_arcade_sm = carregar_fonte_pixel(13)
    fonte_acao = carregar_fonte_pixel(16)

    tempo_ultima_navegacao = 0
    tempo_ultimo_confirmar = 0
    ultimo_nome = ""

    opcoes_menu = [
        {"real_idx": 0, "titulo": "SPACE", "sub": "INVADERS"},
        {"real_idx": 1, "titulo": "ADVENTURE", "sub": "ATARI"},
        {"real_idx": 2, "titulo": "SCORE", "sub": ""},
    ]
    lista_rects_menu = []

    def tocar_menu_sfx(tipo):
        # Sem som via computador; o Arduino cuida do buzzer.
        return

    # Fundo Estelar Discreto do Launcher
    estrelas_launcher = [
        {"x": (i * 97) % LARGURA, "y": (i * 53) % ALTURA, "tam": (i % 2) + 1, "vel": 0.4 + (i % 3) * 0.2}
        for i in range(40)
    ]

    rodando = True
    frame_count = 0

    def executar_opcao(idx):
        nonlocal ultimo_nome, rodando
        real_idx = opcoes_menu[idx]["real_idx"]

        if real_idx == 0:
            nome = solicitar_nome_jogador(tela, relogio, arduino, ler_hardware, ultimo_nome)
            if nome:
                ultimo_nome = nome
                space_invaders_jogo.rodar_jogo(tela, relogio, arduino, ler_hardware, nome)
        elif real_idx == 1:
            nome = solicitar_nome_jogador(tela, relogio, arduino, ler_hardware, ultimo_nome)
            if nome:
                ultimo_nome = nome
                nivel = selecionar_nivel_adventure(tela, relogio, arduino, ler_hardware)
                if nivel:
                    adventure_jogo.rodar_jogo(tela, relogio, arduino, ler_hardware, nome, nivel)
        elif real_idx == 2:
            rankings_ui.exibir_rankings(tela, relogio, arduino, ler_hardware)

        pygame.event.clear()
        tocar_menu_sfx('confirm')

    while rodando:
        frame_count += 1
        agora = time.time()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    rodando = False
                elif evento.key in (pygame.K_UP, pygame.K_w):
                    opcao_menu = (opcao_menu - 1) % len(opcoes_menu)
                    tempo_ultima_navegacao = agora
                    tocar_menu_sfx('move')
                elif evento.key in (pygame.K_DOWN, pygame.K_s):
                    opcao_menu = (opcao_menu + 1) % len(opcoes_menu)
                    tempo_ultima_navegacao = agora
                    tocar_menu_sfx('move')
                elif evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if agora - tempo_ultimo_confirmar > 0.35:
                        tempo_ultimo_confirmar = agora
                        executar_opcao(opcao_menu)

            elif evento.type == pygame.MOUSEMOTION:
                xpos, ypos = evento.pos
                for idx, rect in enumerate(lista_rects_menu):
                    if rect.collidepoint(xpos, ypos):
                        opcao_menu = idx
                        break
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                xpos, ypos = evento.pos
                for idx, rect in enumerate(lista_rects_menu):
                    if rect.collidepoint(xpos, ypos):
                        executar_opcao(idx)
                        break

        # Lê os dados do hardware
        joy_x, joy_y, btn_menu, btn_tiro = ler_hardware(arduino)

        # Navegação no Menu por Joystick Y
        if agora - tempo_ultima_navegacao > 0.22:
            if joy_y < 300:
                opcao_menu = (opcao_menu - 1) % len(opcoes_menu)
                tempo_ultima_navegacao = agora
            elif joy_y > 700:
                opcao_menu = (opcao_menu + 1) % len(opcoes_menu)
                tempo_ultima_navegacao = agora

        # Seleção por Botão de Tiro
        if btn_tiro == 0 and (agora - tempo_ultimo_confirmar > 0.35):
            tempo_ultimo_confirmar = agora
            executar_opcao(opcao_menu)

        # --- RENDERIZAÇÃO RETRO ARCADE ---
        tela.fill(COR_FUNDO)

        # Animação de estrelas no fundo
        for est in estrelas_launcher:
            est['y'] = (est['y'] + est['vel']) % ALTURA
            pygame.draw.circle(tela, (70, 75, 110), (int(est['x']), int(est['y'])), est['tam'])

        # Scanlines CRT
        for y in range(0, ALTURA, 4):
            pygame.draw.line(tela, (14, 12, 28), (0, y), (LARGURA, y), 1)

        # --- MENU INICIAL RETRO PIXEL ---
        # Fundo limpo, sem borda, com o look espacial da referência

        # Título principal em blocos grandes
        titulo_shadow = fonte_titulo_lg.render("MID", True, (255, 0, 0))
        titulo_shadow_2 = fonte_titulo_lg.render("COLLECTION", True, (0, 240, 255))
        tela.blit(titulo_shadow, (LARGURA // 2 - titulo_shadow.get_width() // 2 + 4, 80 + 4))
        tela.blit(titulo_shadow_2, (LARGURA // 2 - titulo_shadow_2.get_width() // 2 + 4, 150 + 4))

        txt_mid = fonte_titulo_lg.render("MID", True, COR_BRANCO)
        txt_collection = fonte_titulo_lg.render("COLLECTION", True, COR_BRANCO)
        tela.blit(txt_mid, (LARGURA // 2 - txt_mid.get_width() // 2, 80))
        tela.blit(txt_collection, (LARGURA // 2 - txt_collection.get_width() // 2, 150))

        pygame.draw.line(tela, (235, 235, 235), (220, 245), (580, 245), 2)

        # Opções do menu em estilo pixel, em destaque vertical
        base_y = 270
        lista_rects_menu = []
        for idx, item in enumerate(opcoes_menu):
            y = base_y + idx * 72
            selecionado = (opcao_menu == idx)
            fator_hover = 1.014 if selecionado else 1.0

            if item["sub"]:
                txt1_base = fonte_titulo_md.render(item["titulo"], True, COR_BRANCO if selecionado else (220, 220, 220))
                txt2_base = fonte_card_sub.render(item["sub"], True, COR_NEON_AMARELO if selecionado else (200, 200, 200))

                if selecionado:
                    txt1 = pygame.transform.smoothscale(txt1_base, (max(1, int(txt1_base.get_width() * fator_hover)), max(1, int(txt1_base.get_height() * fator_hover))))
                    txt2 = pygame.transform.smoothscale(txt2_base, (max(1, int(txt2_base.get_width() * fator_hover)), max(1, int(txt2_base.get_height() * fator_hover))))
                else:
                    txt1 = txt1_base
                    txt2 = txt2_base

                x1 = LARGURA // 2 - txt1.get_width() // 2
                x2 = LARGURA // 2 - txt2.get_width() // 2
                rect_item = pygame.Rect(x1 - 40, y - 8, txt1.get_width() + 80, txt1.get_height() + txt2.get_height() + 32)
                lista_rects_menu.append(rect_item)
                tela.blit(txt1, (x1, y))
                tela.blit(txt2, (x2, y + 36))
            else:
                txt_base = fonte_titulo_md.render(item["titulo"], True, COR_BRANCO if selecionado else (220, 220, 220))
                txt = pygame.transform.smoothscale(txt_base, (max(1, int(txt_base.get_width() * fator_hover)), max(1, int(txt_base.get_height() * fator_hover)))) if selecionado else txt_base
                x = LARGURA // 2 - txt.get_width() // 2
                rect_item = pygame.Rect(x - 18, y + 5, txt.get_width() + 36, txt.get_height() + 20)
                lista_rects_menu.append(rect_item)
                tela.blit(txt, (x, y + 10))

            if selecionado:
                pygame.draw.polygon(tela, COR_NEON_AMARELO, [(170, y + 18), (195, y + 28), (170, y + 38)])
                pygame.draw.polygon(tela, COR_NEON_AMARELO, [(630, y + 18), (605, y + 28), (630, y + 38)])

        # Ícones do espaço na tela inicial
        nave_img = pygame.transform.scale(nave_tela_inicial, (90, 70))
        alien_img = pygame.transform.scale(alien_tela_inicial, (64, 64))

        tela.blit(nave_img, (75, 430))
        tela.blit(alien_img, (660, 350))

        # Texto de ação inferior
        if (frame_count // 25) % 2 == 0:
            txt_start = fonte_acao.render("> PRESSIONE ACTION PARA INICIAR <", True, COR_NEON_AMARELO)
            tela.blit(txt_start, (LARGURA // 2 - txt_start.get_width() // 2, ALTURA - 42))

        pygame.display.flip()
        relogio.tick(60)

    if arduino:
        try:
            arduino.close()
        except Exception:
            pass
    pygame.quit()
    return

if __name__ == '__main__':
    main()
