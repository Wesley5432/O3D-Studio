# O3D Studio 0.0.2

Ferramenta para converter BLEND, OBJ e 3DS em peças O3D, configurar materiais/animações e montar veículos a partir de uma base para OMSI 2/openOMSI.

[Guia da v0.0.2](GUIA_v0.0.2.md) · [Notas da versão](RELEASE_NOTES.md) · [Site e tutorial](https://o3d-studio-laboratorio.centeredflea.chatgpt.site/) · [Manual histórico](MANUAL.md)

## Novidades

- Nomes originais das peças nos O3D, com IDs apenas para identificação interna.
- Prévia de animação em aramado: variável, pivô, eixos, hierarquia e deformação por pesos.
- Receitas de palheta/manete e aplicação direta de material/animação.
- Marcadores do Blender para pivôs e luzes; vínculos smoothskin para coifa/sanfona.
- Montagem de dianteira/reboques de uma base articulada, com engates e scripts compartilhados.
- Catálogo pesquisável de variáveis/eventos, com descrição baseada no CFG e localização de cada uso.
- Exportação O3D → OBJ/MTL, selecionada ou completa, com UV e texturas disponíveis.

## Começar no Windows

1. Extraia o código e instale Python 3.11 com Tcl/Tk e o launcher Python para Windows.
2. Abra `start.bat`, ou execute `py -3 app.py` na pasta do projeto.
3. Para converter BLEND/OBJ/3DS, selecione sua instalação do Blender. Os testes locais usam Blender 4.3.2. O3D → OBJ e a prévia geométrica não dependem de Blender.
4. Abra **Ferramentas → Editor de peças / CFG independente** e escolha `examples/Deformacao_Demo` para testar o exemplo de deformação em L.

O fonte do exemplo é `examples/Deformacao_Demo.blend`. No editor, selecione **Coifa Câmbio**, abra a prévia e varie **brake** de 0 a 1. A base fica fixa e o topo acompanha a cabeça do câmbio. Este é um exercício geométrico, não um ônibus completo.

## Validação

```sh
python -m pip install Pillow
python -m unittest discover -s tests -p "test_*.py"
```

Os testes externos requerem Blender no PATH ou em `BLENDER_PATH`. Sem ele, esses testes são explicitamente ignorados. O teste que compara o CFG original Torino requer uma cópia local em `examples/TorinoS_MB.cfg`; esse material de referência não é distribuído publicamente.

Para gerar o aplicativo Windows, execute `build_windows.bat`. O Blender é externo e não é incluído no executável.

## Limites

A prévia é geométrica e não executa scripts, física ou todos os modificadores do CFG. Coifas/sanfonas precisam de pesos e controladores preparados. A montagem articulada usa uma base pronta e exige conferir física, alinhamento e passageiros. OBJ exporta pose estática; O3D protegido não é suportado. Consulte o guia para os limites de cada fluxo e faça o teste final no jogo.

O pacote público inclui código, testes e o exemplo original de deformação. Modelos, texturas e CFGs do ônibus Torino usado como referência local não estão incluídos.

## Licença

Código próprio sob GPL-3.0-or-later. Consulte [LICENSE](LICENSE) e [THIRD_PARTY.md](THIRD_PARTY.md).
