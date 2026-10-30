# Mesa de Fichas — D&D 5e + Lanternas

Aplicação web em português para fichas de personagens de D&D 5e com mecânicas personalizadas para os Lanternas.

## Executar
Abra `index.html` em um navegador moderno. No modo padrão, os dados ficam armazenados localmente no navegador (modo demonstração).

## Recursos
- Dados de personagem, atributos, modificadores, PV, CA e deslocamento.
- Rolagens de perícias e salvaguardas com d20.
- Mecânicas personalizadas de anel, bateria, energia (Pe), construtos e poderes de Lanternas.
- Interface responsiva com suporte a tema escuro.
- Código preparado para integração opcional com Firebase ou uma API local.

## Observação sobre armazenamento
O modo de demonstração armazena fichas no `localStorage` do navegador e não sincroniza automaticamente entre dispositivos. Para armazenamento online, configure Firebase Authentication e Firestore no código e estabeleça regras de segurança apropriadas antes de publicar.

## Publicação
O repositório pode ser publicado pelo GitHub Pages em **Settings → Pages**, selecionando a branch `main` e a pasta `/(root)`.
