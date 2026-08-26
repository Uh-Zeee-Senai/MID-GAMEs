import os
import pygame
import time

def solicitar_nome_jogador(tela, relogio, arduino, ler_hardware, nome_anterior=""):
    """
    Exibe a modal retro para o jogador digitar seu nome antes de iniciar a partida.
    - O campo SEMPRE começa 100% VAZIO ("") a cada nova chamada.
    - Limite absoluto de 10 caracteres.
    - O botão [JOGAR] permanece bloqueado enquanto o campo estiver vazio ou > 10 caracteres.
    - Pressionar ESC/Menu retorna None (cancelando a inicialização do jogo).
    """
    LARGURA, ALTURA = 800, 600
    nome = ""

    COR_FUNDO = (10, 8, 20)
    COR_NEON_AZUL = (0, 240, 255)
    COR_NEON_ROSA = (255, 0, 128)
    COR_NEON_VERDE = (0, 255, 120)
    COR_NEON_AMARELO = (255, 230, 0)
    COR_TEXTO_MUTED = (160, 170, 190)
    COR_TEXTO_DESABILITADO = (80, 85, 100)
    COR_PANEL = (12, 12, 22)
    COR_PANEL_2 = (18, 16, 32)
    COR_HIGHLIGHT = (35, 20, 55)

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FONTE_PIXEL = os.path.join(BASE_DIR, 'assets', 'fonts', 'PressStart2P-Regular.ttf')

    def carregar_fonte_pixel(tamanho):
        if os.path.exists(FONTE_PIXEL):
            return pygame.font.Font(FONTE_PIXEL, tamanho)
        return pygame.font.SysFont('Consolas', tamanho, bold=True)

    fonte_titulo = carregar_fonte_pixel(24)
    fonte_input = carregar_fonte_pixel(28)
    fonte_btn = carregar_fonte_pixel(18)
    fonte_sub = carregar_fonte_pixel(12)

    estrelas = [
        {"x": (i * 101) % LARGURA, "y": (i * 67) % ALTURA, "tam": (i % 2) + 1, "vel": 0.3 + (i % 3) * 0.15}
        for i in range(30)
    ]

    tempo_ultimo_input = time.time()
    opcao_selecionada = 0
    pygame.key.start_text_input()
    rodando = True
    resultado_nome = None

    while rodando:
        agora = time.time()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.key.stop_text_input()
                return None

            elif evento.type == pygame.TEXTINPUT:
                opcao_selecionada = 0
                if len(nome) < 10:
                    char = evento.text
                    if char.isalnum() or char in (' ', '_', '-'):
                        nome += char

            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_BACKSPACE:
                    opcao_selecionada = 0
                    nome = nome[:-1]
                elif evento.key == pygame.K_ESCAPE:
                    pygame.key.stop_text_input()
                    return None
                elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if 1 <= len(nome.strip()) <= 10:
                        resultado_nome = nome.strip()
                        rodando = False
                elif evento.key in (pygame.K_DOWN, pygame.K_TAB):
                    opcao_selecionada = 1
                elif evento.key == pygame.K_UP:
                    opcao_selecionada = 0

        joy_x, joy_y, btn_menu, btn_tiro = ler_hardware(arduino)

        if btn_menu == 0 and (agora - tempo_ultimo_input > 0.3):
            pygame.key.stop_text_input()
            return None

        if agora - tempo_ultimo_input > 0.22:
            if joy_y > 700:
                opcao_selecionada = 1
                tempo_ultimo_input = agora
            elif joy_y < 300:
                opcao_selecionada = 0
                tempo_ultimo_input = agora

        if btn_tiro == 0 and (agora - tempo_ultimo_input > 0.3):
            tempo_ultimo_input = agora
            if opcao_selecionada == 1 and (1 <= len(nome.strip()) <= 10):
                resultado_nome = nome.strip()
                rodando = False

        tela.fill(COR_FUNDO)
        for est in estrelas:
            est['y'] = (est['y'] + est['vel']) % ALTURA
            pygame.draw.circle(tela, (80, 82, 110), (int(est['x']), int(est['y'])), est['tam'])

        for y in range(0, ALTURA, 4):
            pygame.draw.line(tela, (14, 12, 28), (0, y), (LARGURA, y), 1)

        modal_rect = pygame.Rect(120, 110, 560, 380)
        pygame.draw.rect(tela, COR_PANEL, modal_rect, border_radius=14)
        pygame.draw.rect(tela, COR_NEON_AZUL, modal_rect, width=2, border_radius=14)
        pygame.draw.rect(tela, COR_PANEL_2, (130, 120, 540, 360), border_radius=10)
        pygame.draw.line(tela, (220, 220, 220), (190, 205), (610, 205), 2)

        txt_tit = fonte_titulo.render("DIGITE", True, COR_NEON_AMARELO)
        txt_tit2 = fonte_titulo.render("SEU NOME", True, COR_NEON_AZUL)
        tela.blit(txt_tit, (LARGURA // 2 - txt_tit.get_width() // 2, 145))
        tela.blit(txt_tit2, (LARGURA // 2 - txt_tit2.get_width() // 2, 178))

        txt_dica1 = fonte_sub.render("MAX 10 CARACTERES", True, COR_TEXTO_MUTED)
        tela.blit(txt_dica1, (LARGURA // 2 - txt_dica1.get_width() // 2, 220))

        input_rect = pygame.Rect(190, 250, 420, 62)
        cor_borda_input = COR_NEON_VERDE if opcao_selecionada == 0 else (120, 130, 160)
        pygame.draw.rect(tela, COR_HIGHLIGHT, input_rect, border_radius=10)
        pygame.draw.rect(tela, cor_borda_input, input_rect, width=2, border_radius=10)

        texto_exibido = nome + ("_" if (int(agora * 2.5) % 2 == 0 and opcao_selecionada == 0) else "")
        txt_nome = fonte_input.render(texto_exibido if texto_exibido else "_", True, (255, 255, 255) if nome else COR_TEXTO_MUTED)
        tela.blit(txt_nome, (input_rect.x + 18, input_rect.y + 14))

        txt_counter = fonte_sub.render(f"{len(nome)}/10", True, COR_NEON_AMARELO if len(nome) == 10 else COR_TEXTO_MUTED)
        tela.blit(txt_counter, (input_rect.right - 60, input_rect.bottom + 10))

        pode_jogar = (1 <= len(nome.strip()) <= 10)
        btn_rect = pygame.Rect(250, 340, 300, 54)

        if pode_jogar:
            if opcao_selecionada == 1:
                cor_btn_bg = (24, 130, 92)
                cor_btn_borda = COR_NEON_VERDE
                cor_btn_txt = (255, 255, 255)
            else:
                cor_btn_bg = (18, 58, 38)
                cor_btn_borda = COR_NEON_VERDE
                cor_btn_txt = COR_NEON_VERDE
        else:
            cor_btn_bg = (25, 25, 35)
            cor_btn_borda = COR_TEXTO_DESABILITADO
            cor_btn_txt = COR_TEXTO_DESABILITADO

        pygame.draw.rect(tela, cor_btn_bg, btn_rect, border_radius=8)
        pygame.draw.rect(tela, cor_btn_borda, btn_rect, width=2, border_radius=8)
        txt_btn = fonte_btn.render("INICIAR JOGO", True, cor_btn_txt)
        tela.blit(txt_btn, (LARGURA // 2 - txt_btn.get_width() // 2, btn_rect.y + 15))

        if not pode_jogar:
            txt_bloqueio = fonte_sub.render("DIGITE DE 1 A 10 CARACTERES", True, COR_NEON_ROSA)
            tela.blit(txt_bloqueio, (LARGURA // 2 - txt_bloqueio.get_width() // 2, 408))
        else:
            txt_ok = fonte_sub.render("ENTER / BOTÃO DE TIRO PARA CONFIRMAR", True, COR_NEON_VERDE)
            tela.blit(txt_ok, (LARGURA // 2 - txt_ok.get_width() // 2, 408))

        txt_esc = fonte_sub.render("[ESC / MENU] VOLTAR", True, COR_TEXTO_MUTED)
        tela.blit(txt_esc, (LARGURA // 2 - txt_esc.get_width() // 2, 435))

        pygame.display.flip()
        relogio.tick(60)

    pygame.key.stop_text_input()
    return resultado_nome
