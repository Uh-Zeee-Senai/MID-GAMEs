# Melhorias sugeridas para o projeto

Este documento reúne ideias de melhorias para evoluir o sistema, deixando a experiência mais robusta, visualmente mais forte e mais fácil de manter.

## 1. Padronização visual geral

- criar uma paleta única de cores para menu, ranking, modal de nome e telas de jogo
- centralizar fontes e estilos em um módulo próprio de UI
- padronizar bordas, espaçamentos, radius e transparências entre todas as telas
- remover variações visuais inconsistentes entre os módulos

## 2. Melhor organização do código

- separar a lógica de desenho em componentes UI reutilizáveis
- criar uma camada de helpers para fontes, textos, botões e painéis
- reduzir duplicação de código entre `main.py`, `core/nome_modal.py` e `core/rankings_ui.py`
- mover constantes visuais para um arquivo central de estilo

## 3. Melhor experiência de menu e navegação

- adicionar animação mais suave de seleção
- incluir sons de navegação e confirmação
- criar feedback visual para opções desabilitadas
- permitir navegação por mouse em desktop, além de teclado e joystick
- ajustar a zona de clique/press para evitar acidentalidades no menu

## 4. Melhorias no sistema de entrada

- unificar corretamente entradas de teclado, hardware e joystick em um só controle
- melhorar debounce para evitar múltiplas ações por toque curto
- adicionar mapeamento configurável de botões
- permitir suporte a mais modelos de Arduino sem depender de portas fixas

## 5. Sistema de save e rankings

- salvar ranking por jogo com tempo, nível e modo de vitória
- mostrar melhor nome de jogador e posicionamento
- criar filtros por jogo, data e dificuldade
- incluir paginação ou scroll no ranking, caso aumente bastante

## 6. Melhorias na qualidade de gameplay

- criar tutoriais dentro do jogo para Space Invaders e Adventure
- aumentar variedade de inimigos e chefes
- ajustar balanço de dificuldade por fase
- reduzir elementos aleatórios excessivos em nível 3 do Adventure
- implementar sistemática de checkpoints ou save de progresso

## 7. Melhorias no Adventure

- adicionar minimapa da sala atual
- mostrar objetivo atual na tela com texto claro
- melhorar distinção visual entre salas, portas e itens
- adicionar animação de coleta e interação com objetos
- criar mais pistas visuais para esconder segredos e passagens secreta

## 8. Melhorias no Space Invaders

- adicionar sistema de power-ups mais ricos
- permitir escolha de dificuldade antes da partida
- criar efeitos sonoros de tiro, dano, boss e vitória
- melhorar HUD com vida, combo e status do boss
- incluir fases progressivas com aumento de obstáculos

## 9. Melhorias de acessibilidade

- permitir aumento de contraste para melhor legibilidade
- incluir ajuste de tamanho de texto
- deixar o jogo mais claro para pessoas com baixa visão
- permitir remapear controles em tempo real

## 10. Melhorias de manutenção e qualidade

- criar testes automatizados para funções críticas
- validar entrada de dados do banco e evitar inconsistências
- documentar cada módulo e sua responsabilidade
- separar sprites e dados em pastas mais organizadas
- criar logs bem estruturados para depuração

## 11. Melhorias de apresentação para entrega

- adicionar tela de créditos
- criar tela de introdução com história do jogo
- incluir icon/logo do projeto
- criar vídeo de apresentação ou material de demonstração
- preparar uma versão final mais “polida” para apresentação ao público

## 12. Prioridades recomendadas

Se a ideia for evoluir o projeto de forma prática, estas são as prioridades mais valiosas:

1. padronizar o visual do menu, nome e rankings
2. centralizar fontes e estilos
3. melhorar a lógica de entrada e debounce
4. ajustar a UX do Adventure
5. implementar sons e feedback visual
6. criar uma estrutura melhor de save/rankings

Com essas melhorias, o projeto ficaria mais consistente, profissional e fácil de expandir em futuras versões.
