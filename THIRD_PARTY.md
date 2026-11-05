# Dependências e fontes
- vendor/meshio.py: Nathan Burnham, Apache-2.0, cópia sem alterações do commit f325bedd8690a8b7937d29bef2333161826644eb de https://github.com/Road-hog123/Blender-OMSI-Exporter. Licença em vendor/LICENSE_Apache.txt. Usado para serialização O3D.
- vendor/import_3ds.py: Blender contributors, GPL-2.0-or-later, cópia com modificação local para preservar referências de imagens ausentes (place_holder=True) a partir do commit b42d68627734cb18af0e6f41537063984313a284 de https://github.com/blender/blender-addons. Cabeçalhos de autoria preservados. Integração distribuída sob GPL-3.0-or-later.
- Blender é um processo externo GPL; não incluído neste ZIP. https://www.blender.org/download/ . Ao redistribuir uma pasta runtime, preserve as licenças e cumpra a oferta/disponibilidade de código-fonte correspondente do Blender.
- Código próprio deste projeto: GPL-3.0-or-later. Licença completa em LICENSE.

- Transformação UV dos modos POINT/TEXTURE: comportamento conferido no código oficial do Blender, https://github.com/blender/blender/blob/main/source/blender/nodes/shader/nodes/node_shader_mapping.cc . TEXTURE usa a transformação inversa; teste numérico incluído.
