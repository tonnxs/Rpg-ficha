# Mesa de Fichas — modo local por Wi-Fi

Esta versão adiciona um servidor local ao site de fichas. Os dispositivos conectados à mesma rede Wi-Fi acessam a mesma mesa, sem Firebase e sem hospedagem pública.

## Requisitos
- Node.js 18 ou mais recente no dispositivo que vai hospedar a mesa.
- Todos os celulares/notebooks na mesma rede Wi-Fi.
- O dispositivo anfitrião deve permanecer ligado e com o servidor aberto durante a sessão.

## Ubuntu / Debian / Linux

1. Instale Node.js 18+ (se já tiver Node, pule esta etapa).
2. Baixe o repositório e entre na pasta:
   `git clone https://github.com/tonnxs/Rpg-ficha.git`
   `cd Rpg-ficha`
3. Inicie o servidor:
   `npm start`
4. Descubra o IP local do notebook:
   `hostname -I`
5. No celular, abra o navegador e acesse `http://IP-DO-NOTEBOOK:8080`, substituindo pelo IP mostrado no terminal. Exemplo: `http://192.168.1.10:8080`.

Se o firewall bloquear a conexão, permita a porta TCP 8080 na rede privada. Não exponha essa porta à internet.

## Windows

Instale Node.js 18+ pelo site oficial do Node.js, baixe o repositório como ZIP, extraia a pasta e execute `npm start` no terminal dentro dela. No celular, acesse `http://IP-DO-PC:8080`.

## Android como anfitrião (Termux)

1. Instale Termux por uma fonte oficial do projeto.
2. No Termux execute:
   `pkg update && pkg install nodejs git`
   `git clone https://github.com/tonnxs/Rpg-ficha.git`
   `cd Rpg-ficha`
   `npm start`
3. Descubra o IP do celular nas configurações de Wi-Fi e abra `http://IP-DO-CELULAR:8080` nos outros dispositivos.
4. Mantenha o Termux aberto e impeça o Android de encerrar o aplicativo em segundo plano durante a sessão.

O suporte a hospedar no Android depende do fabricante, das permissões de rede e das restrições de bateria. Usar o notebook Ubuntu como anfitrião costuma ser mais simples.

## Contas e fichas

- Crie a primeira conta pelo botão de cadastro: ela será a conta do **mestre**.
- Cada conta criada depois será de jogador.
- O mestre pode listar e editar todas as fichas.
- Jogadores acessam e editam apenas a própria ficha.
- Use e-mails distintos para cada conta.
- As senhas são armazenadas com hash scrypt; os dados ficam em `data/mesa.json`, no dispositivo anfitrião.
- Faça cópia de segurança desse arquivo para preservar as fichas. Ele é ignorado pelo Git e não deve ser publicado.

## Usar como aplicativo no celular

Depois de abrir a página no navegador, use o menu e escolha **Adicionar à tela inicial** ou **Instalar app** (a opção varia conforme o navegador). Isso cria um atalho para a mesa. O servidor local ainda precisa estar ativo para salvar e compartilhar dados.

## Limitações importantes

- É um sistema local, não sincroniza pela internet com jogadores fora da mesma rede.
- A rede Wi-Fi precisa permitir comunicação entre dispositivos (algumas redes públicas ou redes de convidados bloqueiam isso).
- Não use o modo local em uma rede pública não confiável. O tráfego HTTP na rede local não é criptografado; prefira uma rede privada confiável.
- O primeiro cadastro torna-se mestre. Se apagar `data/mesa.json`, as contas e fichas locais serão apagadas.
