> Manual histórico do conversor. Para as funções atuais, consulte [GUIA_v0.0.2.md](GUIA_v0.0.2.md).

# Manual do O3D Studio 0.0.1

A documentação abaixo reproduz o histórico do conversor de origem. A versão publicada do O3D Studio é 0.0.1.

# O3D Auto Converter 0.8.2 — montagem a partir de veículo de referência

Entrada: .blend, .3ds, .obj. Saída: O3D por peça, texturas, projeto editável e CFG de modelo. Inclui conversor, editor numérico e montagem de uma cópia completa de um veículo de referência. Não é um editor 3D de modelagem; a montagem ainda exige revisão e testes no jogo.


## Correção da aplicação de variáveis — 0.8.2

**Aplicar alterações à peça** agora incorpora os campos da animação e do material selecionados antes de validar a peça. Não é necessário clicar primeiro em Atualizar animação ou Aplicar material para esses campos selecionados. Para criar uma animação nova, continue usando Adicionar ou Preparar receita.

Na montagem, a troca de variável passa a ser aplicada também quando a malha está marcada como `keep` (manter). O remapeamento aceita espaços de indentação nos comandos anim_rot/anim_trans, preservando a formatação. Variáveis remapeadas são validadas também em peças mantidas.

Após aplicar a peça, gere o CFG novamente e salve o projeto. A confirmação altera o projeto em memória; não modifica sozinha um CFG já instalado no jogo.

## Interface simplificada — 0.8.1

A tela principal tem três menus: **Importar**, **Projeto** e **Ferramentas**. O fluxo continua em quatro etapas: **Base**, **Peças**, **Aparência** e **Exportar**. Outro CFG de referência e explicações detalhadas ficam em seções recolhidas.

Na edição de uma associação, **Materiais**, **Animação** e **Código CFG** aparecem em abas separadas. O código deixa de ocupar espaço enquanto você configura materiais. O botão **Aplicar associação** permanece visível.

No editor universal, use os menus **Projeto**, **Scripts** e **Exportar**. A exportação da peça selecionada ou de todos os O3D continua disponível no menu Exportar. As ferramentas e formatos existentes foram preservados.

Validação: compilação dos módulos e suíte automatizada. Aparência visual ainda não conferida em uma sessão gráfica; sem alterações no formato de exportação nesta atualização.

## Luzes e adaptação de referências — 0.8

**Coordenadas das luzes** abre o CFG atualmente usado pelo veículo. A lista mostra `[spotlight]`, `[light_enh_2]` e `[interiorlight]`; selecione uma luz, altere XYZ, clique Aplicar XYZ e salve o CFG. Os outros parâmetros e a ordem permanecem preservados. Usa os campos de posição dos comandos encontrados na referência Torino S. Não cria luzes que estejam ausentes do CFG e não oferece prévia 3D.

**Adaptar scripts** permite selecionar veículo receptor e doador, ler incompatibilidades e associar cada variável/evento ausente a um nome disponível no doador. Verifique vínculos antes de exportar a cópia. A adaptação altera referências nos comandos usuais do CFG (animação, visibilidade, material, texto, evento e dois tipos de luz) e inclui os scripts com listas atualizadas no `.bus`. O relatório `troca_scripts.json` registra o mapa aplicado. O veículo original permanece intacto. Câmbio, suspensão, quantidade de portas, sons, macros, intervalos e lógica não são convertidos por renomeação; compatibilidade de referências não é garantia de compatibilidade funcional.

**Animações ausentes:** na montagem da base, associe cada O3D novo à função da peça de referência e aplique o bloco completo. No editor universal, configure cada peça na aba Animações. Incluir scripts não gera animações automaticamente. Para adaptar um veículo que já aparece no jogo, é preciso identificar seu CFG ativo e suas peças; não há detecção automática universal.

Verificação: 48 testes automatizados, incluindo alteração XYZ sem modificar os outros parâmetros e troca de scripts com remapeamento do CFG e preservação do original. Interface compilada, sem validação visual. Não testado no OMSI/openOMSI.

## Interface e exportação direta — 0.7

- Tema visual unificado: azul, fundos claros, melhor espaçamento, botões de ação destacados e prévia CFG com fonte monoespaçada em fundo escuro.
- No **Editor de peças**, escolha **Somente a peça selecionada** ou **Todas as peças** em **Exportar geometria**, depois **Exportar O3D + texturas**. Exporta os O3D já convertidos/importados e somente suas texturas referenciadas. Não gera um CFG parcial com vínculos incompletos. A seleção é feita na lista de peças do programa, após converter/importar o modelo.
- Conversão, importação de O3D, exportação de geometria, pacote com doador e troca de scripts gravam diretamente na pasta escolhida. Não criam mais pastas externas `O3D_<id>` ou `Modelo_com_scripts_<id>`. As pastas de recursos `model`, `texture` e scripts são mantidas. A montagem completa conserva `Vehicles/<nome>` e `Fonts`, necessários ao formato do pacote de instalação, sem uma pasta aleatória envolvendo o pacote.
- Reexportar preserva arquivos não envolvidos. Arquivos substituídos recebem backup em `backup_exportacao_<id>.zip` na saída. Falhas durante a cópia tentam restaurar o conteúdo anterior. Arquivos antigos que não fazem parte da nova exportação não são apagados automaticamente.
- **Selecionar doador .bus → Veículo + scripts + .bus** inclui automaticamente o `.bus` escolhido, seus scripts declarados e recursos locais do doador. O `[model]` é atualizado para `model\model.cfg`, e as quatro listas de scripts são atualizadas. Não é mais necessário montar manualmente o `.bus` usando o TXT. Sons externos, posições, física e lógica ainda precisam de revisão. Para copiar os blocos completos de materiais/animações da referência, use a montagem no Studio.

Verificação 0.7: 44 testes automatizados, incluindo conversão real de fixture 3DS com Blender, seleção/todas as peças, texturas, backup/restauração e `.bus` do doador com listas válidas. Interface verificada por compilação, sem inspeção visual neste ambiente. Sem teste no jogo e sem build Windows nesta entrega.

## Blocos completos por peça — 0.6.1

Para aproveitar os materiais e animações da base, use **Veículo base → Peças e animações**. Associe a peça da referência ao novo O3D, selecione os materiais correspondentes, confira pivô/eixos e clique **Aplicar associação**. **Prévia do bloco adaptado** mostra a mesma transformação usada no exportador, mesmo com outras peças ainda pendentes.

A substituição preserva a ordem de `[matl_change]`, `[matl_item]`, `[matl_nightmap]`, `[animparent]`, `[mesh_ident]`, `[mouseevent]`, `[visible]` e `[newanim]`, incluindo parâmetros, comentários e separadores. Ajusta apenas caminho da malha, materiais associados e alterações explícitas de pivô/variável. Pais ausentes, identificadores duplicados e ciclos de parentesco bloqueiam a exportação.

**CFG independente / vazio** gera uma configuração separada a partir do projeto universal: não importa automaticamente esses blocos da base. Não substitua o CFG funcional do ônibus por uma lista de meshes esperando herdar suas animações. A montagem completa requer a pasta da base com suas dependências e revisão das associações; não reconhece a função de cada peça automaticamente.

Validação desta atualização: testes automatizados de preservação do bloco do volante e vínculos entre peças. A interface não foi verificada visualmente e o pacote não foi executado no OMSI/openOMSI.

## O3D pronto, implantação de scripts e skins/fontes — 0.6

### Usar O3D já exportado

Clique **Usar O3D já exportado**, escolha a pasta dos O3D, a pasta de texturas (opcional) e uma saída fora da entrada. O programa lê os binários sem usar Blender, cria uma cópia organizada e gera `project.json`, `report.json` e `model/model.cfg`. O editor abre o projeto para configurar animações, materiais e variáveis. Nomes de textura incompatíveis são adaptados no registro de materiais do O3D; geometria, UV e demais registros binários não são reserializados. Arquivos protegidos/criptografados ou formatos não suportados são rejeitados, sem tentar desbloqueá-los.

Para gerar apenas CFG, use **Gerar CFG** no editor. Para levar também os scripts de uma base, use **CFG + scripts**, selecione o `.bus` doador quando necessário e a saída. O pacote inclui modelo, texturas, `.bus` do doador, dependências declaradas e seus recursos locais. `INCLUIR_NO_BUS.txt` permanece como referência das listas; o `.bus` já é atualizado automaticamente. Física, sons e posições são herdados e exigem revisão. Scripts selecionados isoladamente para consulta não bastam para esse pacote; é necessário o `.bus` com as listas de dependências.

### Usar outra base e copiar a organização do CFG

Na aba inicial, **Base que fornece a estrutura (.bus)** define qual veículo fornece estrutura e scripts. **Copiar estrutura deste CFG** permite usar um CFG de exemplo. **Modelo novo (pasta do projeto)** aponta para o projeto convertido ou importado de O3D. O resumo mostra a variante escolhida, quantidade de scripts e caminho do CFG.

**Sugerir associações pelo nome** propõe somente correspondências únicas de nomes normalizados e preenche materiais apenas quando textura/ocorrência coincidem. Nomes ambíguos não são associados. Pivôs e eixos ficam sem confirmação: revise cada proposta antes de exportar. Não há reconhecimento automático da função de uma malha desconhecida.

### Trocar somente scripts de um veículo existente

Clique **Trocar somente scripts**. Selecione o `.bus` do ônibus que recebe a alteração, o `.bus` doador e uma pasta de saída fora dos dois veículos. **Verificar referências do CFG** lista variáveis numéricas, variáveis de texto ou eventos usuais que faltam no doador. **Criar cópia com novos scripts** bloqueia essas incompatibilidades detectadas e produz uma nova pasta quando as verificações passam.

Somente as quatro listas de scripts/variáveis/constantes do `.bus` escolhido são substituídas; seus arquivos declarados são copiados para uma pasta com nome exclusivo. Modelos, CFG visual, texturas, física e outras variantes `.bus` existentes permanecem como estavam. A operação nunca modifica o veículo original.

Essa checagem é conservadora e parcial: não interpreta a execução de scripts, não garante macros, lógica de transmissão/portas, variáveis de som ou todos os comandos de luz, nem detecta todos os recursos externos. Referências nativas não declaradas podem exigir revisão manual. Teste a cópia no jogo antes de usar normalmente.

### Selecionar skins e trocar fontes

Carregue a base primeiro. Os canais e fontes vêm do CFG escolhido.

- **Skin específica (.cti)** abre o seletor de arquivos. A pasta da skin passa a ser a pasta de origem dos recursos. O exportador valida os canais `[item]` contra a base e verifica suas imagens; inclui apenas o CTI escolhido entre os CTIs dessa pasta, junto dos demais recursos. Deixar esse campo vazio mantém a opção de copiar a pasta de repaints inteira.
- O seletor de cada canal de skin agora também aceita sua textura original quando a peça da base é mantida. Antes, apenas texturas de peças substituídas eram aceitas, impedindo esse uso.
- Para fontes, use **Escolher .oft** ao lado do nome, ou escolha **Pasta Fonts** e clique **Atualizar lista de fontes da pasta**. O seletor continua permitindo digitar o nome. Os índices de texto permanecem na ordem original.
- A seleção `.oft` define sua pasta como a pasta Fonts a incluir no pacote. Se trocar várias fontes, reúna seus `.oft` e imagens na mesma pasta. Uma substituição sem o `.oft` correspondente nessa pasta bloqueia a exportação. Fontes originais que não forem fornecidas geram aviso de dependência global.

Escolher um CTI não força uma pintura inicial pelo script: disponibiliza o repaint no pacote do veículo. O mecanismo de seleção de pintura e o uso das fontes ainda dependem do jogo e do CFG/script da base.

### Evidência

Testes cobrem importação O3D sem Blender, rejeição de arquivo protegido, pacote CFG + scripts, preservação de O3D/CFG/física na troca de scripts, bloqueio de variáveis ausentes, seleção de CTI e fonte, e sugestões ambíguas. Não houve teste visual da interface no Windows nem execução dentro do OMSI/openOMSI. A entrega permanece em código-fonte.

## Texturas 3DS, nomes e quatro pastas — 0.5

### Conversão

Abra **Converter BLEND / OBJ / 3DS**, escolha o modelo e, se necessário, **Pasta de texturas**. Essa pasta é pesquisada recursivamente quando a imagem não existe no caminho original. Sem pasta escolhida, a busca usa a pasta do modelo. A busca ignora diferenças entre maiúsculas/minúsculas; dois arquivos candidatos com o mesmo nome geram aviso de ambiguidade e não são escolhidos arbitrariamente.

A falha do importador 3DS foi corrigida em dois pontos: referências de imagens ausentes não são mais descartadas pelo importador; o exportador segue a imagem ligada através do nó MixRGB usado pelo 3DS. Misturas simples com fator 0/1 são resolvidas pelo ramo ativo. Uma imagem única encontrada numa mistura complexa pode ser recuperada com aviso de aproximação; múltiplas imagens exigem bake e continuam sinalizadas. Isso não é um sistema geral de bake de shaders.

Escala, deslocamento e rotação Z de UV por material são aplicados quando o nó Mapping usa coordenadas UV e modo POINT ou TEXTURE com parâmetros constantes. Outros mapeamentos e camadas UV explícitas são sinalizados para revisão. UV ausente não é reconstruída automaticamente. Transparência, emissão, especular e renderização dentro do jogo ainda precisam de conferência.

A opção **Organizar O3D em Exterior / Interior / Painel / Mecanica** vem ligada na interface. Cria as quatro pastas dentro de `model`, organiza as peças por sugestões baseadas no nome e mantém os caminhos coerentes no projeto e nos CFGs. A classificação não analisa a função da geometria; nomes genéricos ficam em Exterior para revisão. Desligue a opção se preferir exportação plana. A API `engine.run()` mantém `organize=False` por compatibilidade; use `organize=True` para ativar.

Nomes de O3D recebem um prefixo numérico único, remoção de caracteres inválidos e transliteração de acentos. O nome original do objeto permanece no projeto e no relatório. As texturas mantêm os nomes compatíveis existentes e recebem sufixo quando há conflito de conteúdo.

### Revisão e organização manual

Após converter, o resumo mostra peças, texturas, imagens ausentes e avisos. **Abrir resultado e revisar peças** abre diretamente o projeto produzido.

No editor, a busca encontra objeto original, caminho O3D ou textura. A lista mostra separadamente nome e arquivo; materiais sem imagem aparecem como **(sem textura)**. **Diagnóstico** exibe os avisos do `report.json`.

**Organizar / renomear** permite escolher uma das quatro pastas e um nome para cada peça. Clique **Aplicar à peça** e depois **Salvar cópia com as quatro pastas**. A cópia atualiza `project.json`, `report.json` e referências `[mesh]` dos CFGs dentro de `model`; o original permanece intacto. O arquivo `organizacao.json` relaciona caminhos antigos e novos. A janela abre a cópia para edição. Montagens externas que apontavam para os nomes antigos precisam ser reassociadas. Um CFG de saída externo à pasta original não é alterado ou transportado automaticamente.

### Verificação desta versão

Testes de conversão com Blender 4.3.2: arquivo 3DS de teste com material/imagem real, MixRGB, textura em pasta separada, divergência de caixa no nome, imagem ausente, ambiguidade e transformação UV. Conferidos bytes da imagem exportada, referência dentro do O3D e UV calculada. Testes de regressão também cobrem BLEND/OBJ, nomes, pastas e montagem pelo CFG de referência.

O `.3ds` completo que originou os 666 objetos do relatório do usuário não foi fornecido; esse caso específico ainda precisa ser reconvertido com a 0.5. A interface e o executável Windows não foram validados visualmente, e não houve teste dentro do OMSI/openOMSI. O ZIP continua sendo código-fonte com `start.bat` e instruções de build. Os testes de 3DS usam Pillow (`pip install pillow`) apenas para criar a imagem de teste; o aplicativo não exige Pillow.

## Modo universal e CFG vazio — 0.4

Este modo permite configurar modelos convertidos de veículos sem exigir um Torino como referência. Não identifica automaticamente a função das peças e não cria uma simulação física universal.

1. Converta o `.blend`, `.3ds` ou `.obj` e escolha a pasta que contém `project.json` no Studio.
2. Clique **Editor universal / CFG vazio**. Também é possível selecionar um `.cfg` vazio no campo **CFG de exemplo** e clicar **Carregar estrutura da variante**: isso abre o editor universal sem exigir `.bus` e preenche o CFG com as peças do projeto.
3. No editor, **Selecionar CFG de saída** permite criar `model.cfg` ou escolher um arquivo vazio existente. A lista inicial é produzida nesse momento, se o projeto passar na validação. Se o arquivo já tiver conteúdo, apenas a saída é selecionada; **Gerar CFG** depois substitui o conteúdo e guarda backup.
4. Use **Escolher .bus** para ler as listas de variáveis, eventos e dependências declaradas pelo veículo. Alternativamente, **Ler scripts .osc** lê um ou vários scripts e substitui o perfil atual pelo catálogo de referências encontrado. Os scripts nunca são executados, modificados ou copiados por este editor.
5. Abra **Variáveis e eventos**. Selecione uma variável numérica e clique **Animação**, **Visibilidade** ou **Iluminação** para preencher o campo correspondente. Selecione um evento e clique **Evento** para preencher o mouseevent. Variáveis de texto aparecem para consulta, mas não são usadas como variáveis numéricas de animação.
6. **Adicionar variável manual** cadastra um nome no projeto. Isso permite usá-lo no CFG, mas não cria sua declaração na varlist nem a lógica `.osc`. As referências lidas diretamente de scripts também não comprovam que estejam declaradas nas varlists; confira o `.bus`.
7. Prepare ou edite as animações, materiais e pivôs. Clique **Aplicar alterações à peça** antes de mudar de peça. **Salvar projeto** guarda o perfil, variáveis manuais e caminho de saída; **Gerar CFG** escreve as alterações aplicadas.

O CFG novo tem separadores e identificação por peça, com parâmetros posicionais para mesh, identificação, parent, eventos, visibilidade, animações e materiais. Ele não inventa seções de skins, fontes, luzes ou efeitos sem dados. Para herdar essas configurações, use o modo de CFG de referência da 0.3.1.

Preferencialmente salve em `model/model.cfg`, junto das malhas. Se escolher outra pasta, os caminhos `[mesh]` são calculados em relação a ela. Esses caminhos devem ser revistos ao mover o pacote; texturas e integração ao `.bus` continuam dependendo da estrutura do veículo. O `.bus` não é alterado automaticamente por este modo.

A validação cobre geração em arquivo vazio, backup, caminhos de malhas, variáveis manuais, leitura de scripts, listas de texto do `.bus` e encaminhamento da interface para o modo vazio. A interface não foi validada visualmente no Windows e não houve teste nos motores OMSI/openOMSI. A falha de leitura de texturas 3DS foi tratada na atualização 0.5; veja acima os limites de materiais suportados.

## Organização do CFG — atualização 0.3.1

Na aba **Veículo base**, o novo campo **CFG de exemplo (opcional)** permite escolher o `TorinoS_MB.cfg` fornecido, incluído em `examples/`. Deixe vazio para usar o CFG declarado no `.bus`.

Selecione o `.bus` dentro do veículo completo, indique o CFG de exemplo e clique **Carregar estrutura da variante**. As malhas e recursos continuam sendo procurados na estrutura do veículo base, relativos à pasta do CFG declarado no `.bus`. O arquivo de exemplo pode ficar fora dessa pasta. Na exportação, seu conteúdo adaptado ocupa o caminho de CFG já declarado no `.bus` da nova cópia.

O editor preserva a sequência dos blocos, títulos, separadores, linhas vazias e parâmetros. Trocas de caminhos, materiais e fontes preservam também os espaços no início/fim da linha. A ordem dos índices de texturas de texto e das animações permanece igual à referência. Exclusões de peças e alterações explícitas de pivô modificam seus respectivos blocos; não se deve esperar identidade integral após essas operações. Finais de linha da saída são CRLF para Windows.

Salvar a montagem guarda também o caminho e hash do CFG escolhido. Alterar a referência depois de salvar bloqueia a exportação até recarregar e revisar a montagem. Projetos da 0.3 sem esse campo continuam usando o CFG do `.bus`.

Teste novo: os 306 blocos do CFG anexado foram carregados com malhas sintéticas usadas somente como dependências de teste. Exportar sem modificações reproduziu os bytes do CFG original; trocar uma fonte alterou somente as linhas dessa fonte. Esse teste verifica organização textual, não funcionamento do ônibus no jogo. A interface nova não foi testada visualmente no Windows. A correção de leitura das texturas 3DS foi acrescentada posteriormente na versão 0.5.

## Novo Studio 0.3: usar a estrutura do Torino

1. Abra `start.bat`. Use **Converter BLEND / OBJ / 3DS** para gerar a pasta com `project.json`, `model` e `texture`. O nome correto do arquivo Blender é `.blend`.
2. Na aba **Veículo base**, escolha um `.bus` dentro da pasta completa extraída do Torino de referência e a pasta convertida. Clique **Carregar estrutura da variante**. Carregar outra variante reinicia as associações; salve sua montagem antes.
3. Na aba **Peças e animações**, procure cada peça da referência. Selecione `replace` (substituir), `keep` (manter) ou `remove` (remover). `pending` significa pendente e bloqueia exportação. **Manter todas as peças ainda pendentes** serve para uma montagem parcial; continua incluindo peças do Torino original.
4. Ao substituir, selecione a malha convertida e associe cada material original ao slot correto. Edite as variáveis nos seletores se necessário, confira pivô/eixos e clique **Aplicar associação da peça antes de trocar de peça**. O bloco original mostrado abaixo é somente consulta. A interface não desloca a malha nem mostra prévia 3D.
5. Em **Skins e fontes**, escolha opcionalmente a pasta de repaints `.cti` + imagens e a pasta `Fonts` com `.oft` + imagens. Ajuste os nomes de fontes e selecione a nova textura de cada canal de skin afetado pela substituição. As variáveis do `.cti` precisam corresponder aos canais da referência. A textura base pode ser substituída por outra imagem do mesmo formato. Não há geração de novas fontes nem edição gráfica das pinturas.
6. Salve a montagem em JSON para continuar depois. Seus caminhos apontam para as pastas locais originais; mover essas pastas exige atualizar os caminhos.
7. Clique **Verificar montagem**, corrija as pendências e **Exportar pacote de teste**. A exportação cria uma pasta nova com `Vehicles/<nome>`, `Fonts` se fornecida, instruções e o projeto. Use nome com letras sem acentos, números, `_` ou `-`.
8. Instale numa cópia de teste do jogo. Confira o logfile e ajuste física, dimensões, eixos, câmeras, posições de luzes, passageiros e sons externos. Escolher OMSI 2/openOMSI registra o destino; não garante compatibilidade nem transforma scripts específicos entre motores.

### O que é preservado e o que muda

A montagem lê os blocos reais do CFG apontado pelo `.bus`. Mantém sequência de animações, identificadores, parents, visibilidade, eventos, comandos de material e índices de texturas de texto. Nos blocos substituídos, troca o caminho da malha e os seletores de materiais conforme a associação. Variáveis e pivôs só mudam quando indicados. Texturas das novas malhas recebem nomes separados para não sobrescrever imagens das peças mantidas. Essa alteração no binário O3D preserva os demais bytes, incluindo geometria e UV.

Scripts, constantes, física e recursos são copiados da referência para uma pasta nova. Somente a variante `.bus` escolhida é mantida na raiz. O nome de apresentação do modelo é atualizado. O programa não inventa massa, torque, suspensão, distâncias entre eixos ou lógica de portas com base apenas na malha.

A validação bloqueia pendências, materiais não associados, imagens ausentes, parents removidos, alterações detectadas no `.bus`/CFG e substituição de blocos com bones (`setbone`/`smoothskin`). Blocos com luzes/efeitos ou algumas configurações globais não podem ser removidos automaticamente. Essas verificações não cobrem todas as dependências externas possíveis. Skins e fontes continuam dependendo de arquivos válidos e compatíveis com a referência.

### Evidência e limites da 0.3

- As seis variantes do Torino anterior foram lidas: duas com 328 blocos e quatro com 306. Preservação integral do conteúdo de cada CFG confirmada ao manter todas as peças (normalizando apenas finais de linha).
- Montagem de uma cópia completa da referência testada em pasta nova; substituição, textura, skin, fonte, variável e pivô testados com fixture própria. Isso não significa que as 134 peças do 113 já foram associadas ao Torino.
- Testes automatizados e resultados ficam em `tests/` e `validation/`.
- A interface foi implementada, mas não teve validação visual nesta sessão: o ambiente não permitiu iniciar o servidor gráfico. Não foi produzido nem testado um executável Windows. O código é entregue para execução com Python/Tk ou compilação pelo BAT.
- Não houve execução dentro do OMSI 2 ou openOMSI. Não há garantia de UV sem falhas, renderização automática, ajuste físico automático nem reconhecimento infalível da função das peças.
- O ZIP posterior com sufixo `(1)` não ficou disponível. A referência usada foi o pacote anterior `Marcopolo Torino S RMTC-GO byZane.zip`. Scripts/modelos completos do Torino não estão duplicados neste pacote do programa.

## Rodar no Windows

1. Instale Python 3.11 com Tcl/Tk (https://www.python.org/downloads/windows/).
2. Extraia o ZIP inteiro. Entre na pasta O3D_Auto_Converter e execute start.bat.
3. Selecione o blender.exe. O backend foi testado com Blender 4.3.2 Linux. Outros sistemas/versões devem ser verificados; o Blender escolhido deve conseguir ler a versão do arquivo .blend.
4. Escolha o modelo e pasta de saída. Escala 1 corresponde a uma unidade por metro. Entrada: Z para cima. Confira orientação e dimensão do modelo de origem.
5. Clique Converter para O3D e examine report.json. As saídas sempre usam uma pasta nova.
6. Clique Abrir editor de peças / gerar CFG e escolha a pasta convertida que contém project.json.

O Blender trabalha em segundo plano. O programa não salva o arquivo .blend original e desativa a execução automática de scripts ao abri-lo.

## Usar o editor numérico anterior (janela do conversor)

- A lista à esquerda seleciona a peça. A identificação `part_0000`, por exemplo, é usada como parent em outras peças.
- Escolher .bus lê as listas de scripts, variáveis e constantes. Não executa scripts e não copia automaticamente um veículo inteiro. Referências ausentes bloqueiam a geração de um CFG associado àquela base. Limpar perfil permite voltar à configuração sem perfil.
- Parent associa uma peça à animação de outra. O exportador ordena parents antes dos filhos e rejeita ciclos. Não aplica automaticamente a hierarquia Blender como hierarquia OMSI, pois a geometria já foi exportada em coordenadas mundiais.
- Pivô XYZ vazio utiliza a matriz de origem gravada no O3D. Preencher XYZ escreve `origin_trans` no CFG em coordenadas OMSI (lateral, longitudinal, vertical). Esse campo não move a malha.
- Evento aceita uma família declarada no perfil, incluindo handlers `_drag` e `_off`.
- Visibilidade usa variável e valor; deixe a variável vazia para não adicionar condição.
- Na aba Animações, prepare uma receita e ajuste a lista. Os campos abaixo da lista são tipo rot/trans, variável, fator e rotações XYZ da origem em graus. A ordem das linhas é a ordem aplicada. Para reordenar nesta versão, remova e readicione na ordem desejada.
- Na aba Materiais, selecione o slot e configure alpha 0/1/2 ou um mapa noturno condicionado a uma variável. O mapa deve estar dentro da pasta texture da conversão. O programa usa o nome exportado e a ocorrência daquele material, sem misturar slots.
- Clique Aplicar alterações à peça antes de trocar de peça. Salvar projeto grava as alterações aplicadas. Gerar CFG escreve model/Model_gerado.cfg e mantém backup se esse arquivo já existia. Integre esse CFG ao .bus correspondente e teste no jogo.
- Desfazer recupera até 20 estados da sessão. Depois de desfazer, salve para gravar o estado recuperado.

As receitas são editáveis e não detectam automaticamente as funções das peças:

| Receita na interface | Uso inicial |
|---|---|
| static | Peça sem animação |
| door | Variável escolhida (ex.: door_0), origem Y 90°, fator ajustável |
| steering | Axle_Steering_0_L, origem Y 90°, fator inicial 1200 |
| wheel_front | Giro, suspensão e direção; escolha eixo 0–9 e lado L/R |
| wheel_rear | Giro e suspensão; escolha eixo e lado |
| custom | Uma rotação pela variável/fator escolhidos, editável depois |

As três animações da receita wheel_front não reproduzem todas as particularidades de um ônibus: inclinação adicional, hierarquia e detalhes do chassi podem exigir mais linhas. Os fatores das receitas foram orientados pelo exemplo analisado; não são uma calibração universal.

## Pivôs e materiais

A geometria continua em coordenadas mundiais; a matriz de origem do objeto, incluindo a transformação herdada, é gravada no registro O3D de animação. A conversão de eixos segue X,Z,Y e a matriz é armazenada transposta, conforme a referência documentada em THIRD_PARTY.md. Conferimos numericamente as origens; comportamento de rotação com diferentes escalas/hierarquias ainda precisa de teste no motor OMSI.

Imagens externas ou empacotadas em formatos suportados são copiadas preservando os bytes quando possível. Os nomes originais seguros são mantidos; nomes inválidos ou conflitantes são adaptados e registrados. Imagens geradas ou de formato não suportado são exportadas para PNG. Imagens ausentes mantêm uma referência no material e um aviso, em vez de desaparecer silenciosamente do O3D. As imagens ausentes continuam precisando ser fornecidas.

Dois materiais com a mesma textura continuam sendo dois slots. report.json e project.json registram nome exportado, slot e ocorrência. Isso permite gerar `[matl]` e `[matl_change]` coerentes com os novos O3D. Não copie cegamente um CFG antigo: sua geometria e ordenação de slots podem ser diferentes.

Suporte básico de material: cor e imagem diretamente ligadas ao Base Color de um Principled. Shaders procedurais, Mapping nodes, UV diferente por material, PBR completo, render targets e repaints ainda exigem tratamento adicional. A UV ativa é preservada, com adaptação de V. Não há unwrap ou reparo automático de UV nesta versão.

## Reparo geométrico opcional

A opção de reparo vem desligada. Quando ligada, remove da saída triângulos cujo produto vetorial das arestas é exatamente zero e substitui normais nulas pela normal da face. Não modifica o .blend nem faz remesh/decimação. Pode alterar o sombreamento nos pontos reparados; confira o resultado visualmente.

## Amostra real incluída

A pasta sample_113 contém a nova conversão do 113.blend fornecido: 134 O3D, project.json e CFG estático. O modelo continua sem texturas, porque elas não vieram no primeiro ZIP. As peças não receberam animações inventadas: abra esse projeto para fazer as associações. O perfil de scripts também não está preenchido, pois o .bus original apontava para dependências ausentes.

Validação numérica: 134 malhas, 327.734 triângulos após o reparo optativo; geometria e UV idênticas à exportação de teste anterior. Todas as 134 origens foram verificadas quanto à coordenada mundial esperada. Os arquivos de referência do Torino S RMTC orientaram a sintaxe e as receitas; seus scripts e recursos completos não são distribuídos aqui.

## Testes reproduzíveis

Com Blender no PATH:

    python tests/check_conversion.py
    python -m unittest discover -s tests -p "test_*.py"

A suíte usa conversões reais do Blender para fixtures .blend/.3ds/.obj, verifica matrizes no binário, UV, hierarquia de origem, reparo optativo, cópia de texturas, conflito de nomes, material repetido e referência a imagem ausente. Os testes de projeto verificam CFG, variáveis, pivôs explícitos, parentesco, rejeição de ciclos e perfil incompleto. Relatórios da execução estão na pasta validation.

Limites de verificação: não há teste visual da interface neste ambiente sem display, nem build/teste do EXE Windows, nem carregamento no OMSI/openOMSI. A compilação Python e os testes descritos passaram; isso não equivale a afirmar que o ônibus está pronto para dirigir.

## Distribuição independente

Execute build_windows.bat no Windows para gerar dist/O3DAutoConverter/O3DAutoConverter.exe. Esse build exige Python e acesso para instalar PyInstaller. Para o usuário final não instalar Blender separadamente, coloque a distribuição portátil completa do Blender em runtime/ (com runtime/blender.exe) antes do build. Distribua a pasta inteira resultante, com as licenças e disponibilidade do código-fonte exigidas pelas dependências.

Este ZIP contém código-fonte, não EXE pré-compilado nem Blender portátil. O aplicativo tem interface própria e usa Blender como componente externo/interno à pasta portátil.

## Ainda fora desta versão

Visualização/edição 3D interativa, prévia animada, deslocamento da geometria no editor, luzes projetadas, cabine/passengers, telas dinâmicas, fontes, deformação por ossos, geração de física e .bus completos, execução/simulação dos scripts e calibração automática. Esses recursos não estão implícitos no botão Gerar CFG.

Fontes e licenças de componentes em THIRD_PARTY.md. Código próprio GPL-3.0-or-later.

