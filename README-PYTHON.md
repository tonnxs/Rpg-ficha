# Mesa RPG — versão Python/Kivy

Esta branch contém um MVP nativo em Python/Kivy para Android e desktop.

## Funções implementadas
- Criar/hospedar uma mesa na rede Wi-Fi local.
- Gerar um código de acesso para a mesa.
- Conectar outro aparelho pelo IP do anfitrião e código.
- Criar, listar, abrir, editar e excluir fichas.
- Persistir fichas em SQLite no aparelho que hospeda a mesa.
- API local para listar e consultar fichas, salvar alterações e excluir registros.

## Campos atuais da ficha
Nome, classe/arquétipo, nível, raça/espécie, pontos de vida e anotações livres. A estrutura JSON permite acrescentar atributos e campos específicos de outros sistemas de RPG nas próximas etapas.

## Gerar o APK
A GitHub Actions executa o Buildozer ao receber alterações nesta branch. Acesse **Actions → Build Mesa RPG Python APK** e baixe o artefato `Mesa-RPG-Python-APK) quando a execução terminar com sucesso.

## Limitações e segurança
- Este é um MVP funcional de fichas simples, não uma migração completa de todos os recursos da aplicação web original.
- A sincronização é centralizada no aparelho que hospeda a mesa; esse aparelho precisa manter o aplicativo aberto e estar na mesma rede Wi-Fi.
- O código de acesso protege as rotas da API, mas o tráfego HTTP na rede local não é criptografado. Use apenas em redes confiáveis.
- Ainda é necessário testar o APK em aparelhos Android reais, inclusive permissões de rede, suspensão em segundo plano e compatibilidade entre versões.
- Não há autenticação individual, permissões por jogador, rolagem de dados ou automação de regras nesta versão.

## Desenvolvimento
Instale Python e Kivy no ambiente de desenvolvimento e execute:

```bash
python -m pip install kivy
python main.py
```
