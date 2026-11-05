# O3D Studio 0.0.1

Ferramenta para converter modelos BLEND, OBJ e 3DS em peças O3D, revisar materiais e animações e montar um veículo para testes no OMSI 2 ou no openOMSI.

[Site e tutorial Blender → openOMSI](https://o3d-studio-laboratorio.centeredflea.chatgpt.site/) · [Manual do conversor de origem](MANUAL.md) · [Licenças das dependências](THIRD_PARTY.md)

## Começar no Windows

1. Extraia o código e instale Python 3.11 com Tcl/Tk e o launcher Python para Windows.
2. Abra `start.bat`. Pelo terminal, também é possível executar `py -3 app.py` na pasta do projeto.
3. Em **Importar**, escolha seu modelo, a pasta de saída e o executável do Blender. O projeto documenta testes com Blender 4.3.2. Para usar malhas O3D já exportadas, escolha o importador de O3D.
4. Revise peças e texturas, configure o CFG e confira a montagem antes de exportar uma cópia de teste.

No [tutorial](https://o3d-studio-laboratorio.centeredflea.chatgpt.site/#exemplo), baixe a placa de saída em formato Blender e siga as instruções para associá-la a um ônibus de referência.

## Conteúdo desta distribuição

Inclui o código do aplicativo, os scripts de inicialização e build, testes e dependências Python incorporadas. Os modelos e texturas do veículo de exemplo, o CFG de referência Torino e os registros de validação do pacote original foram omitidos desta distribuição de código. O teste de layout que compara o CFG original depende de uma cópia local em `examples/TorinoS_MB.cfg`.

## Licença

O código próprio é distribuído sob GPL-3.0-or-later. Consulte [LICENSE](LICENSE) e [THIRD_PARTY.md](THIRD_PARTY.md).
