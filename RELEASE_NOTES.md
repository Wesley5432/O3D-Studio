# O3D Studio v0.0.2

Esta versão acrescenta montagem de base articulada, inspeção de animações e deformação por pesos, mantendo os nomes de origem das peças.

- Nomes dos objetos preservados nos O3D; IDs numéricos permanecem internos.
- Aplicação direta de material/animação, receitas Palheta e Manete/câmbio.
- Prévia 3D em aramado com variável, faixa de valores, pivô, eixos, hierarquia e deformação.
- Marcadores Empty/planos do Blender para pivôs e posições de luzes.
- Exportação de pesos e vínculos `[smoothskin]`/`[setbone]` para coifas/sanfonas, com validação de controladores e índices.
- Montagem de dianteira/reboques de uma base articulada existente, scripts compartilhados e engates XYZ.
- Catálogo pesquisável de variáveis/eventos com usos, descrição contextual, peça, arquivo e linha.
- Exportação O3D → OBJ/MTL da seleção ou de todas as peças, incluindo UV e texturas disponíveis.
- Exemplo original `.blend` e projeto convertido para testar deformação em L.

Leia [GUIA_v0.0.2.md](GUIA_v0.0.2.md) para os passos de uso e limites de cada fluxo.

Verificação: suíte automatizada e conversão real com Blender. A interface e o comportamento no OMSI 2/openOMSI ainda exigem validação manual. A prévia não executa scripts/física; bones e pesos não fazem parte do formato OBJ. O3D protegido não é suportado. A montagem articulada preserva física/rig da base; a malha nova precisa de pesos e alinhamento adequados.

O pacote Windows, quando disponível nesta release, não inclui Blender. Para converter BLEND/OBJ/3DS, selecione sua instalação do Blender no programa.
