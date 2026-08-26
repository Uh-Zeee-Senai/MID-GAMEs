import os
import pygame
import time
from core.database import (
    obter_ranking_space_invaders,
    obter_vencedores_originais_adventure,
    obter_vencedores_normais_adventure
)

def exibir_rankings(tela, relogio, arduino, ler_hardware):
    """
    Exibe a tela de Rankings com abas interativas no estilo Arcade Retro Neon 80s:
    1. 🏆 Vencedores Originais (Adventure - Boss ZéCreppe)
    2. 🚀 Space Invaders (Top 20 Pontuação)
    3. 🐉 Adventure (Vitórias Normais)
    """
    LARGURA, ALTURA = 800, 600

    COR_FUNDO = (10, 8, 20)
    COR_NEON_ROSA = (255, 0, 128)
    COR_NEON_AZUL = (0, 240, 255)
    COR_NEON_AMARELO = (255, 230, 0)
    COR_NEON_VERDE = (0, 255, 120)
    COR_TEXTO_MUTED = (160, 170, 190)
    COR_TAB_INATIVA = (18, 16, 30)
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
    fonte_tab = carregar_fonte_pixel(11)
    fonte_cabecalho = carregar_fonte_pixel(12)
    fonte_linha = carregar_fonte_pixel(11)
    fonte_sub = carregar_fonte_pixel(10)

    aba_atual = 0
    abas = [
        "VENCEDORES",
        "SPACE",
        "ADVENTURE"
    ]

    estrelas = [
        {"x": (i * 97) % LARGURA, "y": (i * 53) % ALTURA, "tam": (i % 2) + 1, "vel": 0.25 + (i % 3) * 0.15}
        for i in range(30)
    ]

    tempo_ultima_troca = time.time()
    rodando = True

    while rodando:
        agora = time.time()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    rodando = False
                elif evento.key in (pygame.K_LEFT, pygame.K_a):
                    if agora - tempo_ultima_troca > 0.18:
                        aba_atual = (aba_atual - 1) % len(abas)
                        tempo_ultima_troca = agora
                elif evento.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_TAB):
                    if agora - tempo_ultima_troca > 0.18:
                        aba_atual = (aba_atual + 1) % len(abas)
                        tempo_ultima_troca = agora

        joy_x, joy_y, btn_menu, btn_tiro = ler_hardware(arduino)

        if btn_menu == 0 and (agora - tempo_ultima_troca > 0.3):
            rodando = False
            break

        if agora - tempo_ultima_troca > 0.25:
            if joy_x < 300:
                aba_atual = (aba_atual - 1) % len(abas)
                tempo_ultima_troca = agora
            elif joy_x > 700:
                aba_atual = (aba_atual + 1) % len(abas)
                tempo_ultima_troca = agora

        tela.fill(COR_FUNDO)
        for est in estrelas:
            est['y'] = (est['y'] + est['vel']) % ALTURA
            pygame.draw.circle(tela, (80, 82, 110), (int(est['x']), int(est['y'])), est['tam'])

        for y in range(0, ALTURA, 4):
            pygame.draw.line(tela, (14, 12, 28), (0, y), (LARGURA, y), 1)

        txt_titulo = fonte_titulo.render("HALL DA FAMA", True, COR_NEON_AMARELO)
        tela.blit(txt_titulo, (LARGURA // 2 - txt_titulo.get_width() // 2, 36))

        largura_tab = 220
        x_inicio_tabs = 90
        for i, tab_nome in enumerate(abas):
            x_tab = x_inicio_tabs + i * 210
            y_tab = 90
            ativa = (i == aba_atual)

            if ativa:
                cor_bg = COR_HIGHLIGHT
                cor_borda = COR_NEON_AZUL
                cor_txt = COR_NEON_AZUL
            else:
                cor_bg = COR_TAB_INATIVA
                cor_borda = (60, 55, 80)
                cor_txt = COR_TEXTO_MUTED

            pygame.draw.rect(tela, cor_bg, (x_tab, y_tab, largura_tab, 38), border_radius=8)
            pygame.draw.rect(tela, cor_borda, (x_tab, y_tab, largura_tab, 38), width=2 if ativa else 1, border_radius=8)
            txt_t = fonte_tab.render(tab_nome, True, cor_txt)
            tela.blit(txt_t, (x_tab + largura_tab // 2 - txt_t.get_width() // 2, y_tab + 11))

        painel_rect = pygame.Rect(60, 150, 680, 360)
        pygame.draw.rect(tela, COR_PANEL, painel_rect, border_radius=10)
        pygame.draw.rect(tela, COR_NEON_AZUL, painel_rect, width=2, border_radius=10)
        pygame.draw.rect(tela, COR_PANEL_2, (70, 160, 660, 340), border_radius=8)

        pygame.draw.line(tela, COR_NEON_ROSA, (70, 188), (730, 188), 2)

        if aba_atual == 0:
            col1, col2, col3, col4 = "POS", "VENCEDOR", "TEMPO", "DATA"
            dados = obter_vencedores_originais_adventure(limit=10)
        elif aba_atual == 1:
            col1, col2, col3, col4 = "POS", "JOGADOR", "PONTOS", "TEMPO"
            dados = obter_ranking_space_invaders(limit=20)
        else:
            col1, col2, col3, col4 = "POS", "JOGADOR", "TEMPO", "DATA"
            dados = obter_vencedores_normais_adventure(limit=10)

        txt_c1 = fonte_cabecalho.render(col1, True, COR_NEON_VERDE)
        txt_c2 = fonte_cabecalho.render(col2, True, COR_NEON_VERDE)
        txt_c3 = fonte_cabecalho.render(col3, True, COR_NEON_VERDE)
        txt_c4 = fonte_cabecalho.render(col4, True, COR_NEON_VERDE)

        tela.blit(txt_c1, (90, 160))
        tela.blit(txt_c2, (180, 160))
        tela.blit(txt_c3, (465, 160))
        tela.blit(txt_c4, (600, 160))

        if not dados:
            txt_vazio = fonte_linha.render("NENHUM REGISTRO AINDA", True, COR_TEXTO_MUTED)
            tela.blit(txt_vazio, (LARGURA // 2 - txt_vazio.get_width() // 2, 280))
        else:
            y_linha = 205
            for item in dados[:10]:
                pos = item['posicao']
                nome = item['nome']
                if aba_atual == 1:
                    valor = str(item.get('pontuacao', 0))
                else:
                    valor = str(item.get('tempo', 'N/A'))
                data_str = item['data']

                if pos == 1:
                    cor_pos = COR_NEON_AMARELO
                elif pos == 2:
                    cor_pos = (220, 220, 220)
                elif pos == 3:
                    cor_pos = (205, 127, 50)
                else:
                    cor_pos = COR_TEXTO_MUTED

                t_pos = fonte_linha.render(f"{pos}", True, cor_pos)
                t_nome = fonte_linha.render(nome[:18], True, (255, 255, 255))
                t_val = fonte_linha.render(valor, True, COR_NEON_VERDE if aba_atual == 1 else COR_NEON_AZUL)
                if aba_atual == 1:
                    tempo_label = item.get('tempo', 'N/A')
                    t_data = fonte_sub.render(tempo_label, True, COR_NEON_AZUL)
                    data_x = 610
                else:
                    t_data = fonte_sub.render(data_str[:16], True, COR_TEXTO_MUTED)
                    data_x = 600

                tela.blit(t_pos, (95, y_linha))
                tela.blit(t_nome, (180, y_linha))
                tela.blit(t_val, (470, y_linha))
                tela.blit(t_data, (data_x, y_linha + 2))
                pygame.draw.line(tela, (25, 22, 45), (80, y_linha + 22), (715, y_linha + 22), 1)
                y_linha += 28

        txt_dica = fonte_sub.render("X / SETAS: TROCAR ABA   |   ESC / MENU: VOLTAR", True, COR_TEXTO_MUTED)
        tela.blit(txt_dica, (LARGURA // 2 - txt_dica.get_width() // 2, 540))

        pygame.display.flip()
        relogio.tick(60)
