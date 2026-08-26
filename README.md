# Mid Collection Arcade

Este projeto é uma arcade de jogos em Python + Pygame com duas experiências principais:

- Space Invaders: shooter de sobrevivência e pontuação
- Adventure: exploração em mapa de salas, coleta de itens e progressão por níveis

Além disso, o sistema conta com:

- tela inicial com menu retro
- seleção de nome do jogador
- rankings salvos em SQLite
- suporte opcional a Arduino/joystick com fallback para teclado

---

## 1. Como o sistema funciona

O programa principal fica em `main.py` e é o ponto de entrada do projeto.

Ao iniciar, ele:

1. inicializa o pygame
2. inicia o banco de dados SQLite
3. tenta conectar ao Arduino, se houver um dispositivo disponível
4. exibe a tela inicial com menu retro
5. permite navegar entre as opções:
   - SPACE INVADERS
   - ADVENTURE
   - SCORE
6. ao selecionar uma opção, abre a tela correspondente

Se o Arduino não estiver conectado, o jogo usa o teclado como fallback:

- setas / A-D para mover
- W-S para navegar nos menus
- Enter / Espaço para confirmar
- Esc para voltar

---

## 2. Estrutura do projeto

```text
Apresentacao_Calouros/
├── main.py                     # menu principal e fluxo de navegação
├── space_invaders/
│   ├── jogo.py                 # modo Space Invaders
│   └── sprites/               # sprites do shooter
├── adventure/
│   ├── jogo.py                 # mapa, lógica e gameplay do Adventure
│   ├── nivel_modal.py          # seleção de dificuldade
│   └── sprites/               # assets do Adventure
├── core/
│   ├── arduino_controller.py   # comunicação serial com Arduino
│   ├── database.py             # banco e persistência
│   ├── nome_modal.py           # tela de cadastro do nome
│   ├── rankings_ui.py          # tela de rankings
│   └── teste_controle.py       # testes de controle
├── assets/
│   └── fonts/
│       └── PressStart2P-Regular.ttf
└── README.md
```

---

## 3. Como funciona o modo Space Invaders

### Objetivo
O jogador controla uma nave na parte inferior da tela e precisa:

- destruir inimigos
- sobreviver o maior tempo possível
- acumular pontos para entrar no ranking
- combater criaturas raras e bosses especiais

### Controles

- movimentação horizontal da nave
- disparo com botão de tiro
- botão de menu para sair do jogo

### Sistema de jogo

O jogo possui:

- fundo estelar em movimento
- ondas de inimigos
- vários tipos de inimigos com comportamentos diferentes
- bônus aleatórios
- barra de tempo
- pontuação e ranking

### Inimigos do Space Invaders

#### 1. Default
- inimigo comum
- baixa resistência
- ataca pela passagem da horda para baixo da tela
- causa dano ao jogador quando atravessa a linha inferior

#### 2. Verde / Creeper
- também chamado de subchefe
- maior e mais resistente
- tem 5 HP
- movimentos mais agressivos
- ao ser derrotado, gera bônus e pode explodir outros inimigos

#### 3. Gelo
- inimigo com efeito de congelamento
- pode travar outros inimigos próximos ao ser derrotado

#### 4. Zangado
- inimigo de velocidade alta
- entra em “dash” em certos intervalos

#### 5. Teleport
- se move e reaparece em outra coluna
- torna a batalha mais imprevisível

#### 6. Charged
- inimigo especial com velocidade aumentada
- ativa efeito de surto e buff para os inimigos

#### 7. Boss Malware
- chefe final da horda
- muito mais resistente
- movimenta-se de forma complexa
- possui aura de dano e pode invocar pressão extra
- derrota exige persistência e boa movimentação

### Bônus

Durante a partida, podem aparecer itens bônus:

- tiro duplo
- ataque em área
- aumento de dano / área de disparo

Esses itens ajudam a abrir vantagem durante a horda e aumentam o poder de fogo do jogador.

### Condição de derrota

O jogo acaba quando:

- o tempo acaba
- ou o jogador recebe dano suficiente por inimigos que descem da tela

A partida salva a pontuação no banco de dados e a exibe na tela de rankings.

---

## 4. Como funciona o modo ADVENTURE

O Adventure é um modo de exploração e progressão em mapa de salas, com estilo retrô e temática de castelo / reino.

### Objetivo principal
O jogador deve explorar diferentes salas, coletar itens e alcançar a vitória.

Existem duas formas de vencer:

1. Vitória normal: levar o cálice ao castelo dourado interno
2. Vitória secreta: derrotar o boss ZéCreppe na sala secreta

### Visão geral do mapa
O mundo é composto por várias salas conectadas:

- castelo dourado exterior
- castelo dourado interior
- campo inicial
- floresta leste
- castelo branco exterior
- castelo branco interior
- floresta sul
- castelo negro exterior
- castelo negro interior
- labirintos
- catacumbas
- sala secreta do ZéCreppe

A sala atual muda conforme a movimentação do jogador pelas bordas do mapa.

### Personagens do Adventure

#### Jogador
- herói principal do reino
- move-se por salas e coleta itens
- pode carregar apenas um objeto por vez
- pode enfrentar dragões e evitar perigos

#### Yorgle
- dragão amarelo
- vive em áreas mais abertas e simples
- é um inimigo de contato

#### Grundle
- dragão verde
- se move mais rápido que Yorgle
- também ataca por contato

#### Rhindle
- dragão vermelho
- geralmente aparece em fases mais avançadas
- mais agressivo

#### Morcego Preto
- inimigo especial
- rouba itens do jogador em certos intervalos
- cria tensão e exige atenção ao inventário

#### ZéCreppe
- boss secreto
- localizado na sala secreta
- desafio final do modo Adventure
- ao derrotá-lo, o jogador conquista a vitória original

---

## 5. Itens do Adventure

### Espada
- permite derrotar dragões em contato
- essencial para sobreviver em vários trechos

### Chave Dourada
- abre o portão do castelo dourado
- pode servir para desbloquear acesso mais avançado

### Chave Branca
- abre o castelo branco

### Chave Negra
- abre o castelo negro

### Cálice
- item principal para vencer normalmente
- deve ser levado até o castelo dourado interno

### Ponte
- facilita a passagem em certas áreas do mapa

### Ímã
- atrai itens próximos e aumenta a praticidade de coleta

---

## 6. Como vencer o Adventure

### Vitória normal
Para zerar pelo caminho normal:

1. explore o mapa e colete os itens necessários
2. obtenha as chaves para destrancar os castelos
3. recupere o Cálice
4. leve o Cálice até o interior do Castelo Dourado
5. ao chegar ao local correto, a vitória normal é confirmada

### Vitória secreta
Para a vitória secreta:

1. avance pela aventura normalmente
2. descubra a passagem secreta na área do campo inicial
3. acesse a sala secreta do ZéCreppe
4. enfrente o boss
5. derrote o ZéCreppe para completar a vitória original

### Níveis de dificuldade

#### Nível 1
- menor mapa
- menos conteúdo
- introdução ao sistema
- ideal para aprender o jogo

#### Nível 2
- mapa completo
- dificuldade equilibrada
- mais desafios e itens

#### Nível 3
- mapa completo, mas aleatório
- itens e posições ficam embaralhados
- maior desafio e maior replayability

---

## 7. Tutorial rápido para começar

### Para jogar

1. execute:

```bash
python main.py
```

2. na tela principal, use o teclado ou o controle para navegar
3. selecione SPACE INVADERS ou ADVENTURE
4. digite seu nome
5. comece a partida

### Tutorial do Space Invaders

- mova a nave para a esquerda e direita
- mire nos inimigos
- evite que a horda chegue ao fundo da tela
- colete bônus quando aparecerem
- sobreviva até o tempo final para manter a pontuação

### Tutorial do Adventure

- caminhe pelas salas e descubra a rota
- não carregue vários itens ao mesmo tempo
- use as portas e chaves para desbloquear progressão
- sempre observe os dragões e o morcego
- busque o Cálice para vencer normalmente
- vá para a sala secreta se quiser o desafio final

---

## 8. Como zerar os jogos

### Zero do Space Invaders
- sobreviva até o fim da partida
- destrua o máximo de inimigos possível
- derrote chefes raros e mantenha a pontuação alta
- o jogo finaliza ao final do tempo ou ao game over

### Zero do Adventure
Existem duas rotas:

- rota principal: conseguir o Cálice e levar até o castelo dourado
- rota secreta: derrotar ZéCreppe na sala secreta

Em ambos os casos, o jogo grava a vitória no ranking e volta ao menu principal.

---

## 9. Sistema de rankings

O projeto salva os resultados em SQLite para:

- Space Invaders
- Adventure em vitória normal
- Adventure em vitória original/secreta

Quando um jogador termina uma partida, os dados são armazenados e podem ser consultados na tela de `SCORE`.

---

## 10. Observações finais

Este projeto mistura:

- gameplay arcade clássico
- exploração de mapa retrô
- progressão por salas
- sistema de pontuação
- elementos de narrativa e desafio secreto

A ideia central é funcionar como uma mini arcade com identidade retro, usando toda a estrutura de menu, ranking, navegação por teclado/joystick e vários tipos de objetivos.

Se quiser, posso também criar uma segunda versão do README em formato mais visual, com emojis e seções de “manual do jogador” para apresentação pública ou para o GitHub.
