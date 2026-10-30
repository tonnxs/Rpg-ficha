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


## Publicação automática no GitHub Pages
Foi adicionado um workflow em `.github/workflows/pages.yml`. Após habilitar **Settings → Pages → Source: GitHub Actions**, o site será publicado e atualizado a cada envio para a branch `main`.

Endereço esperado: https://tonnxs.github.io/Rpg-ficha/

## Fichas compartilhadas pela internet
O modo de demonstração não sincroniza dados entre pessoas ou dispositivos. Para isso, é necessário configurar um projeto Firebase:
1. Crie um projeto em https://console.firebase.google.com/.
2. Ative Authentication com o método **E-mail/senha**.
3. Crie um banco **Cloud Firestore**.
4. Copie a configuração do aplicativo Web Firebase para o objeto `CFG.firebase` em `index.html`.
5. Configure regras de segurança do Firestore para que cada jogador acesse apenas a própria ficha e o mestre tenha acesso às fichas da mesa.

Não publique regras que permitam leitura e gravação irrestritas. A configuração Firebase do aplicativo web não substitui regras de segurança no banco.
