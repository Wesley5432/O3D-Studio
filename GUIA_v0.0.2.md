# O3D Studio v0.0.2 — guia das novas funções

## Começar

No Windows, instale Python 3.11 com Tcl/Tk e abra `start.bat`, ou execute `py -3 app.py`. Para BLEND/OBJ/3DS → O3D, selecione o executável do Blender no conversor. A conversão O3D → OBJ e a prévia geométrica funcionam sem Blender.

O3D Studio continua usando `project.json` versão 2 e montagem versão 3. A numeração do aplicativo é 0.0.2; os projetos anteriores continuam legíveis. Faça novas conversões em outra pasta para não misturar arquivos antigos numerados com os novos nomes.

## Nomes originais

Um objeto chamado `Volante Mercedes.001` gera `Volante Mercedes.001.o3d`. Os IDs `part_0000` ficam no projeto/interface e nos identificadores do CFG, sem prefixar o nome do arquivo. A organização Exterior/Interior/Painel/Mecanica continua opcional.

Caracteres proibidos pelo Windows, nomes reservados e caracteres que não cabem em Windows-1252 são ajustados. Colisões de nomes, inclusive apenas por maiúsculas/minúsculas, recebem sufixo `_2`, `_3` etc. `report.json` conserva o nome do objeto e o arquivo resultante.

## Material e animação na peça

1. Abra **Ferramentas → Editor de peças / CFG independente** e selecione a peça pelo nome.
2. Em **Materiais**, selecione a textura e configure alpha, nightmap e variável. **Aplicar ao material selecionado** já aplica à peça.
3. Em **Animações**, escolha Porta, Volante, Palheta, Manete/câmbio ou outra receita. Preencha a variável do veículo e o fator; clique **Preparar receita da peça**.
4. Confira `rot` ou `trans`, variável, fator e rotação XYZ da origem. **Aplicar animação** aplica a linha selecionada; **Nova animação** acrescenta outra à lista.
5. Salve o projeto e use **Exportar → Gerar CFG**. Aplicar modifica o projeto em memória; gerar CFG grava a configuração.

Parent vazio significa movimento independente. Um Parent faz a peça acompanhar outra peça; a própria peça não aparece entre as opções. O programa bloqueia ciclos.

## Prévia 3D simples

Use **Prévia 3D** no editor ou **Prévia 3D da animação** na montagem da base. Selecione a variável, configure mínimo/máximo e mova a barra. **Executar / pausar** faz um movimento de ida e volta dentro da faixa.

O aramado azul mostra a peça; cinza mostra repouso/controladores; o ponto amarelo marca o pivô. As setas mostram os eixos da origem. Arraste para girar a câmera e use a roda do mouse para aproximar. As vistas Frente, Lateral e Superior ajudam a conferir o centro e a direção do movimento.

Se a peça gira ao redor de um ponto distante, confira o pivô. Se gira no plano errado, ajuste a rotação XYZ da origem. Se o sentido está invertido, confira o sinal do fator. O fator continua sendo multiplicado pelo valor da variável; não assuma que todas as variáveis usam 0–1. Para uma articulação em graus, teste uma faixa como -45 a 45 somente quando isso corresponder à variável da base.

A prévia não executa OSC, curvas de tempo, `offset`, `delay`, `maxspeed`, colisões, física ou efeitos de materiais. Blocos com modificadores não simulados exibem aviso. Outros valores ficam em zero. O desenho é limitado a 6.000 arestas por peça para manter a inspeção leve; o O3D exportado não é simplificado. Confira o resultado final no jogo.

## Marcadores de coordenadas no Blender

Use objetos Empty/Plain Axes ou planos identificados como marcadores. Exemplos:

| Nome ou propriedade no Blender | Uso |
| --- | --- |
| `PIVOT__Volante` | Ponto de origem para a peça Volante |
| `PIVOT__Cabeca Cambio` | Centro do movimento da cabeça do câmbio |
| `LUZ__Painel` | Posição da luz do painel |
| Propriedade `omsi_marker = "pivot"` ou `"light"` | Identifica um marcador sem mudar seu nome |
| Propriedade `omsi_target = "Nome da peça"` | Registra a peça relacionada |
| Propriedade `omsi_variable = "lights_stand"` | Sugestão de variável da luz |

Empties são coletados como marcadores; planos comuns continuam sendo geometria, enquanto planos com prefixo/propriedade de marcador são excluídos das malhas exportadas. A posição inclui transformação dos pais, escala e rotação configuradas na conversão. Empty/plano usa o eixo local +Y para direção de luz; objetos Light usam -Z.

Depois de converter, escolha o marcador e clique **Usar pivô do Blender** no editor ou **Usar coordenadas do marcador Blender** na montagem. Isso preenche XYZ; confira a orientação do eixo na prévia e aplique à peça. O marcador fornece a posição, sem inventar o ângulo correto da animação.

## Palheta e manete

Escolha a receita **Palheta** ou **Manete / câmbio** e uma variável realmente usada pelo script do doador. O fator sugerido é um ponto de partida. Para a lâmina acompanhar um braço, use o braço como Parent e configure a rotação própria da lâmina quando necessária. A prévia mostra a composição desses movimentos.

Um câmbio com dois movimentos pode ter duas animações, cada uma com sua variável/eixo. O programa configura o movimento visual; a lógica de marchas e dos eventos permanece nos scripts.

## Coifa e sanfona com deformação

1. Prepare a malha no Blender e pinte os pesos dos grupos de vértices. Todos os vértices usados precisam ter peso. Mantenha nesses grupos somente os controladores que pretende exportar.
2. Use nomes como `Base Cambio` e `Cabeca Cambio` tanto nos grupos da coifa quanto nas peças controladoras. A base pode ficar estática; o topo acompanha a cabeça. Grupos intermediários permitem uma curva mais distribuída.
3. Marque **Preservar pesos dos grupos de vértices** ao converter. A propriedade `omsi_smoothskin = true` em uma malha também ativa essa exportação para ela. Armatures são avaliadas em repouso; ações, constraints e lógica de rigs Blender não são convertidas automaticamente.
4. Na aba **Deformação**, associe cada grupo à peça controladora. Nomes idênticos e únicos permitem associação inicial. Vínculos ausentes precisam ser preenchidos antes de gerar o CFG.
5. Anime as peças controladoras e confira **Testar deformação na prévia**. O CFG recebe `[smoothskin]` e `[setbone]`, com índices calculados na ordem efetivamente exportada.

Na montagem de um veículo de referência, associe os grupos da nova malha aos controladores da referência na aba **Deformação**. O programa preserva as peças mantidas e atualiza os índices após remoções. Remover um controlador utilizado bloqueia a exportação.

Pesos são normalizados na exportação. Cada grupo O3D admite no máximo 65.535 entradas neste exportador; divida malhas que excedam esse limite. O programa não cria a geometria das dobras nem pinta os pesos de uma coifa/sanfona que ainda não os tenha.

## Exemplo pronto de deformação em L

Abra `examples/Deformacao_Demo` no editor de peças. Selecione **Coifa Câmbio**, abra a prévia, escolha **brake** e teste de 0 até 1. A tira de demonstração dobra em L: sua base permanece fixa e o topo acompanha **Cabeca Cambio**. É um exercício geométrico, não um ônibus completo.

O fonte é `examples/Deformacao_Demo.blend`. `examples/criar_demo_blender.py` permite recriá-lo pelo Blender. O exemplo usa `brake` apenas como controle de teste; substitua pela variável adequada do seu câmbio.

## Luzes dentro do programa

No editor de peças, abra **Projeto → Luzes e marcadores**. Crie uma luz ou selecione uma existente, use um marcador, confira XYZ, cor, alcance e variável e clique **Aplicar luz ao projeto**. Salve e gere o CFG.

`interiorlight` usa a variável escolhida. `spotlight` usa posição, direção, cor, alcance e cones; a seleção do farol depende de `Spot_Select` no script. São posições fixas do veículo, não uma simulação de luzes presas a bones móveis. Para ajustar um CFG pronto sem regenerá-lo pelo editor universal, continua disponível **Ferramentas → Coordenadas das luzes**.

## Variáveis, eventos e descrições

Use **Scripts → Variáveis e eventos** no editor ou **Ferramentas → Variáveis e usos no CFG** no Studio. O catálogo permite pesquisar nome, peça, arquivo e descrição; filtrar numéricas/texto/eventos; e mostrar somente usos encontrados no CFG.

Ao selecionar um nome, veja rotação/translação e fator, visibilidade e valor, troca de material, iluminação, texto/letreiro ou evento do mouse. Cada ocorrência inclui arquivo, linha e bloco original. Scripts mostram leituras, escritas e triggers; a descrição explica o uso observado e não adivinha a lógica pelo nome. Uma variável sem uso localizado permanece identificada como tal.

Os botões de uso preenchem os campos do editor. Aplique a peça depois. Cadastrar uma variável manual não cria sua declaração ou seu comportamento no OSC.

## Ônibus articulado

1. Abra **Ferramentas → Ônibus articulado**.
2. Selecione o `.bus` da dianteira de uma base articulada pronta. As seções são encontradas pelos vínculos `[couple_back]`; `[scriptshare]` usa o perfil da dianteira/última seção com scripts próprios.
3. Selecione cada seção e confira seus engates XYZ locais. **Aplicar engates** conserva os outros parâmetros do `.bus`.
4. Em **Editar peças desta seção**, carregue o projeto convertido correspondente e associe as peças. Termine com **Aplicar esta montagem ao articulado**.
5. Salve `articulado.json` e use **Validar e exportar articulado**. A saída inclui `Vehicles/<nome>` e recursos locais; cada seção substituída tem suas malhas e texturas separadas. Seções sem montagem conservam o modelo original.

Esta versão aceita encadeamento traseiro normal (`reversed=false`) com os `.bus` na mesma pasta. Arquivos ausentes, ciclos, controladores removidos e CFG compartilhado entre seções que receberiam modelos distintos são bloqueados. Bases com acoplamento dianteiro/invertido exigem adaptação fora deste fluxo. Física, amortecimento da articulação, eixos, câmeras e passagens de passageiros são herdados e precisam de teste com o novo modelo.

## O3D → OBJ

Use **Ferramentas → O3D → OBJ** para escolher um ou vários arquivos. No editor, **Exportar → OBJ da peça selecionada / OBJ de todas as peças** utiliza o projeto aberto.

São gravados OBJ, MTL, texturas encontradas e `relatorio_obj.json`, diretamente no destino escolhido. A saída usa X direita, Y frente e Z cima, com UV e orientação das faces convertidos. Ao importar no Blender, use Forward Y e Up Z. A matriz de pivô do O3D não desloca a malha novamente.

OBJ transporta a geometria estática; não leva bones, pesos, scripts, animações, luzes ou efeitos específicos do CFG. Texturas ausentes são listadas no relatório. Arquivos O3D protegidos continuam recusados, e formatos/registros binários desconhecidos não são exportados silenciosamente.

## Verificação e limites da entrega

Os testes automatizados verificam leitura/escrita, coordenadas, UV, índices, vínculos, deformação e exportação. Há teste real com Blender para importar `.blend`, gerar O3D com pesos/marcadores e reimportar o OBJ resultante. Use `python -m unittest discover -s tests -p "test_*.py"`; instale Pillow para as fixtures de imagem e deixe Blender no PATH para os testes externos. Testes dependentes de Blender ou do CFG Torino privado são marcados como ignorados quando esses recursos estão ausentes.

A prévia é geométrica e a interface não foi inspecionada em uma sessão gráfica neste ambiente de desenvolvimento. O resultado precisa de validação no Windows e dentro do OMSI 2/openOMSI. As descrições de formatos foram consultadas na [documentação primária do openOMSI](https://github.com/openOMSI-org/openOMSI/blob/main/docs/FORMATS.md); isso não substitui testes nos jogos.
