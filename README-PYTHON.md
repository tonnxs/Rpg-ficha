# Mesa RPG — versão Python

Esta branch inicia a migração para Python/Kivy.

## Construção do APK
A workflow GitHub Actions `Build Mesa RPG Python APK` tenta gerar um APK de depuração a partir de `buildozer.spec`. Abra Actions no GitHub e selecione a execução mais recente; o arquivo aparece em Artifacts se a compilação terminar com sucesso.

## Estado atual
Esta é uma base técnica inicial, não uma migração funcional completa da aplicação web anterior. A interface Kivy e o servidor local estão em desenvolvimento. A API de fichas ainda precisa de autenticação, autorização por mesa, endpoints completos de leitura/edição e testes em aparelhos reais antes de ser usada com dados pessoais.
