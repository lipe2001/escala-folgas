# Escalas NOC — Starter

Suba com `docker compose up --build -d`.


# Acesso do Admin

O usuario e a senha são definidos pelas variaveis de ambiente `ADMIN` e `ADMIN_PASSWORD`  respectivamente

# Bot Telegram

O bot é definido pela variavel de ambiente `TELEGRAM_TOKEN`.
Como padrão, está o `@ferias_telegram_bot`, criado exclusivamente para fins de testes.
Ele lê e salva no arquivo `\app\bot\data.csv` cada um dos IDs dos contatos para quem vai mandar as mensagens. Para se cadastrar, deve enviar /subscribe.
O bot é configurado pra enviar duas mensagens automaticamente ao publicar as folgas.
Essas mensagens estão formatadas nas funcões `send_folgas_by_day()` e `send_week()` do arquivo bot, respectivamente.
Aqui estão exemplos das duas mensagens:

``` send_folgas_by_day()
Bom Dia! A escala de férias da semana foi publicada. Por favor, verifique seu calendário.

Segunda, dia 03: Gustavo Viana Nascimento, Daniela Neves Fagundes, Manoel Rodrigues Neto
Terça, dia 04: Gabriel Margiotto, Gabryelle Souza Nascimento, Letícia Lima Custódio
Quarta, dia 05: Allefe Rocha Alves, Emanuel Nascimento Vieira
Quinta, dia 06: Anna Luiza Santana Ribeiro, Bruna Castro Lima, Marina Ribeiro Dos Santos
Sexta, dia 07: Francielle Soares Da Silva, Ana Vitória Batista Couto, Darlan Do Carmo Guimarães
```



``` send_week()
Olá! A escala do plantão do fim de semana foi publicada. Por favor, verifique seu calendário. 

Sábado - Equipe A: 
 Iuri Eduardo Braga
 Gabriel Margiotto
 Francielle Soares Da Silva
 Sara Cananda Cotrim
 Gabryelle Souza Nascimento
 Júlio César Santos Neves
 Manoel Rodrigues Neto
 Emanuel Nascimento Vieira
 Lucas Gabriel Campos
 Marina Ribeiro Dos Santos
 Letícia Lima Custódio
 Samuel Da Silva Fagundes
 Daniel Oliveira Reis

 Domingo:
 -> Manha: 
 Gabryelle Souza Nascimento (Huggy) 
 Júlio César Santos Neves (Huggy) 
 Marina Ribeiro Dos Santos (Huggy) 
 Letícia Lima Custódio (Huggy) 

 -> Tarde: 
 Emanuel Nascimento Vieira (Huggy) 
 Lucas Gabriel Campos (Huggy) 
 Samuel Da Silva Fagundes (Huggy)
 
```

