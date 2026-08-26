# Documento de Personalização da Jogabilidade

Este documento descreve as principais variáveis que controlam a dificuldade, a progressão e a mecânica de personalização do jogo em `space_invaders/jogo.py`.

---

## 1) Variáveis de balanceamento geral

### `TELEPORT_CHANCE = 0.50`
- Chance de inimigos do tipo `teleport` ou `boss_malware` se teleportarem ao levar dano.
- Valor alto = mais evasão, mais pressão no jogador.
- Ajuste típico: de 0.20 a 0.70.

### `FREEZE_CHANCE = 0.40`
- Chance do inimigo `gelo` congelar outros inimigos próximos ao ser derrotado.
- Valor alto = maior controle do campo, mais dificuldade para o jogador.

### `BOSS_FIRST_SPAWN_SCORE = 500`
- Pontuação mínima necessária para o primeiro boss aparecer.
- Define quando a fase de boss começa.

### `BOSS_SPAWN_CHANCE = 0.012`
- Probabilidade de um boss surgir aleatoriamente após o primeiro boss.
- Valor baixo = boss aparece mais raramente.

### `BOSS_HITS_REQUIRED = 28`
- Vida total do boss `Malware`.
- Quanto maior, mais tempo para derrotá-lo.

### `BOSS_TIME_MULTIPLIER_ON_DEFEAT = 1.1`
- Multiplica o tempo restante quando o boss é derrotado.
- Valor maior dá bônus mais forte de tempo.

### `BOSS_TIME_DIVISOR_ON_ESCAPE = 1.6`
- Usado em cenários de fuga/escape do boss.
- Afeta a penalidade de tempo quando o boss consegue escapar.

### `CHARGED_MIN_SCORE = 500`
- Pontuação mínima para que inimigos `charged` apareçam.
- Controla a entrada de inimigos mais agressivos.

### `CHARGED_SPAWN_CHANCE = 0.35`
- Chance de spawn de inimigo `charged` quando a pontuação atinge o mínimo.

### `CHARGED_BUFF_DURATION = 3.5`
- Duração do buff aplicado quando um `charged` é derrotado.
- Aumenta a velocidade dos inimigos por alguns segundos.

### `BONUS_DURATION = 10.0`
- Tempo de duração de todos os power-ups ativos.
- Ajusta o impacto dos bônus no gameplay.

### `BONUS_DROP_CHANCE = 0.05`
- Chance de um inimigo dropar um item bônus ao morrer.
- Valor 0.05 = 5%.

### `VELOCIDADE_INIMIGO_MAX = 2.0`
- Velocidade máxima permitida para os inimigos.
- Limita o pulo de dificuldade da horda.

### `MAX_INIMIGOS_TELA = 15`
- Limite máximo de inimigos simultâneos na tela.
- Define o teto da horda.

### `PODER_UP_TYPES`
- Lista dos power-ups disponíveis:
  - `tiro_duplo`
  - `ataque_area`
  - `escudo`
  - `tiro_rapido`
  - `duplicacao`

### `POWERUP_META`
- Configuração visual e texto dos power-ups:
  - `label`: nome exibido
  - `cor`: cor do bônus

---

## 2) Variáveis de raridade e dificuldade dos inimigos

### `MOB_RARITY`
Estrutura principal de balanceamento por tipo de inimigo:

- `default`: comum
- `verde`: subchefe Creeper
- `gelo`: inimigo congelante
- `zangado`: agressivo em dash
- `teleport`: inimigo que se move/teleporta
- `charged`: inimigo com buff de velocidade

Cada entrada contém:
- `nome`: nome visual do tipo
- `peso`: peso de spawn
- `pontos`: pontuação recebida ao derrotar
- `dano_fuga`: dano causado ao atravessar a linha inferior

Exemplo:
- `default`: peso 45, pontos 10, dano_fuga 5.0
- `verde`: peso 6, pontos 50, dano_fuga 15.0
- `charged`: peso 6, pontos 35, dano_fuga 15.0

Importante:
- Quanto maior o `peso`, mais frequente o inimigo aparece.
- `verde` e `charged` são raros, mas fazem mais diferença no gameplay.

---

## 3) Variáveis do ciclo de jogo e spawn

### `tempo_restante`
- Tempo restante do jogador na partida.
- É reduzido por dano de fuga, ataques do boss e outros eventos.
- Quando chega a 0, a partida termina.

### `TEMPO_MAXIMO_REF = 60.0`
- Tempo-base de referência para a barra de tempo da HUD.
- Define o preenchimento visual da barra.

### `velocidade_base_inimigo = 0.50`
- Velocidade inicial base dos inimigos.
- Aumenta com a pontuação e outros buffs.

### `buff_velocidade_inimigos_ate`
- Timestamp até quando a velocidade dos inimigos fica aumentada por um `charged`.

### `boss_primeiro_spawnou`
- Indica se o boss inicial já apareceu.
- Controla a fase de boss e o início dos eventos de aura/horda.

### `boss_ativo`
- Define se o boss está ativo no campo.

### `boss_aura_ativo`
- Ativa a aura vermelha do boss.
- Aumenta o dano de fuga dos inimigos e aumenta a pressão da horda.

### `boss_horda_ativo`
- Indica se a horda de apoio do boss está ativa.
- Aumenta o número de spawn de inimigos na tela.

### `boss_ataque_proximo`
- Momento do próximo ataque do boss.
- Controla o intervalo entre ondas de projéteis.

### `boss_sequencia_ataque`
- Alterna os padrões dos ataques do boss.
- Permite alternar a sequência de projéteis.

### `num_inimigos_desejado`
- Quantidade alvo de inimigos por spawn.
- Calculado por pontuação: `9 + (pontuacao // 160)`.

### `mult_horda`
- Multiplicador da horda quando a aura do boss está ativa.
- Controla a densidade de inimigos na tela.

### `horda_extra`
- Quantidade extra de inimigos adicionada enquanto a horda do boss está ativa.
- Ajuda a manter a dificuldade em níveis mais baixos sem saturar a tela.

---

## 4) Variáveis de movimentação do jogador

### `velocidade_jogador_max = 12`
- Velocidade máxima da nave do jogador.
- Define a responsividade do controle.

### `MIN_X = 45`
- Limite mínimo da posição horizontal da nave.

### `MAX_X = LARGURA - 45`
- Limite máximo da posição horizontal da nave.

### `INTERVALO_TIRO = 0.18`
- Tempo mínimo entre disparos comuns.

### `INTERVALO_TIRO_ATUAL`
- Tempo de disparo em uso no frame atual.
- Pode ficar menor com `tiro_rapido`.

### `tempo_ultimo_tiro`
- Momento do último disparo do jogador.
- Usado para controlar a cadência.

---

## 5) Variáveis de power-ups ativos

Essas variáveis guardam o tempo em que cada buff está ativo:

- `bonus_tiro_duplo_ate`
- `bonus_ataque_area_ate`
- `bonus_escudo_ate`
- `bonus_tiro_rapido_ate`
- `bonus_duplicacao_ate`

### Como funcionam
- Se o tempo atual for menor que o valor salvo, o power-up está ativo.
- Exemplo:
  - `agora < bonus_tiro_rapido_ate`
  - O tiro rapido está ativo até esse timestamp.

---

## 6) Variáveis de pontuação e progresso

### `pontuacao`
- Soma de pontos acumulados.
- Aumenta conforme os inimigos são derrotados.

### `total_inimigos_derrotados`
- Quantidade total de inimigos abatidos.
- Usado na tela de Game Over.

### `tempo_restante`
- Tempo de sobrevivência atual.
- Também pode ser aumentado ao derrotar certos inimigos.

### `tempo_final_jogo`
- Tempo total registrado ao fim da partida.

---

## 7) Variáveis de efeitos visuais e feedback

### `explosoes`
- Lista de explosões ativas.
- Controla a animação visual e tamanho da explosão.

### `popups`
- Textos flutuantes exibidos na tela: `+2s`, `+30s`, `AURA`, `VITÓRIA`, etc.

### `bonus`
- Itens coletáveis de power-up espalhados pelo mapa.

### `efeitos_raio`
- Efeito visual dos inimigos `charged`.

### `ataques_boss`
- Projéteis disparados pelo boss.

---

## 8) Como personalizar a dificuldade rapidamente

Se quiser ajustar a experiência do jogo, os pontos mais úteis são:

1. `MAX_INIMIGOS_TELA` — limita a densidade da horda
2. `VELOCIDADE_INIMIGO_MAX` — controle da velocidade máxima
3. `BOSS_HITS_REQUIRED` — vida do boss
4. `BOSS_SPAWN_CHANCE` — frequência com que o boss reaparece
5. `MOB_RARITY` — raridade e peso dos inimigos
6. `Bonus` e `tempo_restante` — impacto dos power-ups e recompensas
7. `CHARGED_BUFF_DURATION` — duração do efeito de pressão da horda

---

## 9) Resumo prático

Para deixar o jogo mais fácil:
- reduzir `MAX_INIMIGOS_TELA`
- diminuir `VELOCIDADE_INIMIGO_MAX`
- reduzir `BOSS_HITS_REQUIRED`
- aumentar `BOSS_SPAWN_CHANCE` e reduzir `horda_extra`

Para deixar o jogo mais difícil:
- aumentar `MAX_INIMIGOS_TELA`
- aumentar `VELOCIDADE_INIMIGO_MAX`
- aumentar `BOSS_HITS_REQUIRED`
- aumentar `CHARGED_BUFF_DURATION`
- aumentar `MOB_RARITY` de tipos raros

---

## 10) Observação

Muitas dessas variáveis podem ser ajustadas em tempo de desenvolvimento sem quebrar a lógica do jogo, desde que a mudança seja feita junto com a estrutura de spawn e o cálculo de dano/tempo.
