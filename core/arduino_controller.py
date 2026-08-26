import serial
import serial.tools.list_ports
import time
import pygame

def encontrar_porta_arduino():
    """Tenta encontrar automaticamente a porta COM do Arduino/BlackBoard."""
    portas = list(serial.tools.list_ports.comports())
    for p in portas:
        descricao = p.description.lower()
        hwid = p.hwid.lower()
        if any(term in descricao or term in hwid for term in ['arduino', 'usb serial', 'ch340', 'ftdi', '2341', '1a86']):
            return p.device
    
    if portas:
        return portas[0].device
        
    return None

def conectar_arduino(porta=None, baudrate=115200):
    """Conecta ao Arduino e retorna o objeto serial, ou None em caso de falha."""
    if not porta:
        porta = encontrar_porta_arduino()
        
    if not porta:
        porta = 'COM3' # Fallback padrao
        
    try:
        arduino = serial.Serial(porta, baudrate, timeout=0.01)
        time.sleep(1.0) # Tempo para estabilização do reset do Arduino
        print(f"[Arduino] Conectado com sucesso na porta {porta}!")
        return arduino
    except Exception as e:
        print(f"[Arduino] Não foi possível conectar na porta {porta}: {e}")
        print("[Arduino] Executando em modo de emulação de teclado.")
        return None

def ler_hardware(arduino=None):
    """
    Lê os dados do hardware (Joystick X, Joystick Y, Botão Menu, Botão Tiro).
    NOTA: Os eixos X e Y estão trocados entre si e o eixo X foi invertido (1023 - val) para correta orientação Direita/Esquerda.
    """
    joy_x = 512
    joy_y = 512
    btn_menu = 1 # 1 = Solto, 0 = Pressionado
    btn_tiro = 1 # 1 = Solto, 0 = Pressionado

    # 1. Tenta ler do Arduino Serial se conectado
    if arduino:
        try:
            ultima_linha = None
            while arduino.in_waiting > 0:
                linha = arduino.readline().decode('utf-8', errors='ignore').strip()
                if linha:
                    ultima_linha = linha

            if ultima_linha:
                dados = [int(x) for x in ultima_linha.split(',') if x.strip().isdigit()]
                if len(dados) == 4:
                    # Eixos X e Y trocados e X invertido (1023 - val) conforme solicitação
                    joy_x = 1023 - dados[1] # Inverte direção X (Direita/Esquerda)
                    joy_y = dados[0]        # Eixo Y
                    btn_menu = dados[2]
                    btn_tiro = dados[3]
        except Exception:
            pass

    # 2. Emulação / Fallback de Teclado no Pygame
    if pygame.get_init():
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            joy_x = 0
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            joy_x = 1023
            
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            joy_y = 0
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            joy_y = 1023

        if keys[pygame.K_SPACE] or keys[pygame.K_RETURN] or keys[pygame.K_z]:
            btn_tiro = 0

        if keys[pygame.K_ESCAPE]:
            btn_menu = 0

    return joy_x, joy_y, btn_menu, btn_tiro

def enviar_comando(arduino, cmd_char):
    """Envia um comando de caractere ('T', 'M', 'E') para o Arduino."""
    if arduino:
        try:
            arduino.write(cmd_char.encode('utf-8'))
        except Exception as e:
            print(f"[Arduino Error] Erro ao enviar comando {cmd_char}: {e}")
