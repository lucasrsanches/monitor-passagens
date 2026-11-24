# Monitor de passagens

Roda sozinho no GitHub Actions a cada 3 horas. Guarda o histórico de preços de cada rota em
`data/prices.db` e **só avisa no Telegram quando o preço está no menor nível já visto da rota
e bem abaixo do normal**. Preço comum nunca vira mensagem.

## Regra do alerta (em `config.py`)

Precisa cumprir **as duas** condições:
- estar no menor preço já visto da rota (ou até 5% acima dele), e
- estar pelo menos 40% abaixo da mediana (o preço "normal").

Exceção: 60% ou mais abaixo do normal sempre alerta, porque costuma ser erro de tarifa.

Além disso:
- Uma rota precisa de pelo menos 25 preços no histórico antes de gerar qualquer alerta.
  Por isso os primeiros 1–2 dias ficam em silêncio, só aprendendo.
- A mesma viagem só é avisada de novo se cair mais 5%.
- Cada rodada manda no máximo 6 alertas (os melhores).

## Configuração (uma vez só)

1. **Token de voos:** crie uma conta grátis em travelpayouts.com. Depois vá em
   *Profile → API token* e copie o token.
2. **Bot do Telegram:** no Telegram, fale com **@BotFather**, mande `/newbot`, escolha um nome
   e copie o token. Depois abra o seu bot e mande `/start`. É assim que ele descobre pra
   quem enviar.
3. **No repositório do GitHub:** vá em *Settings → Secrets and variables → Actions →
   New repository secret* e crie estes dois:
   - `TRAVELPAYOUTS_TOKEN`
   - `TELEGRAM_BOT_TOKEN`
4. Na aba *Actions → monitor-passagens → Run workflow*, rode uma vez para testar.
   Toda segunda chega um "✅ Monitor ativo" para você saber que ele está vivo.

## Fontes

- **Avião:** API oficial de dados da Travelpayouts/Aviasales, com preços em cache de buscas
  reais de São Paulo (SAO) e Campinas (VCP) pra ~60 destinos nacionais, 8 meses à frente.
  O link do alerta abre o Google Flights na data certa. Confira lá antes de comprar.
- **Ônibus:** página pública de busca da ClickBus, lida por um navegador automático
  (`sources/bus.py`). São 63 rotas saindo de Tietê, Barra Funda, Jabaquara, Santo André e
  São Bernardo, pras próximas 60 datas, em rodízio de ~165 buscas por execução.
  Prioridade: Peruíbe, Minas, Florianópolis e Porto Alegre. A lista fica em `config.py`.

## Rodar no PC (teste)

```
pip install -r requirements.txt
python monitor.py
```
