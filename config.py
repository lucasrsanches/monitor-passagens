"""Configuração do monitor de passagens. Edite aqui sem mexer no resto do código."""

# ---------------------------------------------------------------- AVIÃO
# Códigos de cidade (Aviasales/Travelpayouts). SAO = GRU + CGH (+ VCP em alguns casos).
FLIGHT_ORIGINS = ["SAO", "VCP"]

# Destinos nacionais aceitos (código de cidade/aeroporto -> nome bonito).
# Qualquer destino fora desta lista é ignorado (ex.: voos internacionais).
BR_DESTINATIONS = {
    "RIO": "Rio de Janeiro", "BSB": "Brasília", "BHZ": "Belo Horizonte", "CNF": "Belo Horizonte",
    "SSA": "Salvador", "REC": "Recife", "FOR": "Fortaleza", "POA": "Porto Alegre",
    "CWB": "Curitiba", "FLN": "Florianópolis", "NAT": "Natal", "MCZ": "Maceió",
    "JPA": "João Pessoa", "AJU": "Aracaju", "BEL": "Belém", "MAO": "Manaus",
    "CGB": "Cuiabá", "CGR": "Campo Grande", "GYN": "Goiânia", "VIX": "Vitória",
    "THE": "Teresina", "SLZ": "São Luís", "PMW": "Palmas", "PVH": "Porto Velho",
    "RBR": "Rio Branco", "MCP": "Macapá", "BVB": "Boa Vista", "IGU": "Foz do Iguaçu",
    "NVT": "Navegantes (Balneário Camboriú)", "JOI": "Joinville", "LDB": "Londrina",
    "MGF": "Maringá", "UDI": "Uberlândia", "IOS": "Ilhéus", "BPS": "Porto Seguro",
    "FEN": "Fernando de Noronha", "JJD": "Jericoacoara", "JDO": "Juazeiro do Norte",
    "CXJ": "Caxias do Sul", "CAC": "Cascavel", "STM": "Santarém", "IMP": "Imperatriz",
    "MOC": "Montes Claros", "IPN": "Ipatinga", "RAO": "Ribeirão Preto", "SJP": "São José do Rio Preto",
    "CPV": "Campina Grande", "PNZ": "Petrolina", "XAP": "Chapecó", "MAB": "Marabá",
    "GIG": "Rio de Janeiro", "SDU": "Rio de Janeiro", "LEC": "Lençóis (Chapada Diamantina)",
    "BYO": "Bonito", "JTC": "Bauru", "PFB": "Passo Fundo", "UBA": "Uberaba", "GVR": "Governador Valadares",
}

# Quantos meses à frente varrer (o cache da API costuma ter até ~12 meses).
FLIGHT_MONTHS_AHEAD = 8

# ---------------------------------------------------------------- ÔNIBUS (ClickBus)
BUS_ENABLED = True
# Slugs de origem da ClickBus. A busca às vezes redireciona pra rodoviária que tem a linha
# (ex.: Tietê -> Peruíbe sai do Jabaquara); o preço é gravado pela rodoviária REAL de embarque.
TIETE, BFUNDA = "sao-paulo-tiete-sp", "sao-paulo-barra-funda-sp"
SANTO_ANDRE, SBC = "santo-andre-sp", "sao-bernardo-do-campo-sp-grande-alvarenga"

_DEST = {  # slug -> nome
    "peruibe-sp": "Peruíbe", "belo-horizonte-mg": "Belo Horizonte", "juiz-de-fora-mg": "Juiz de Fora",
    "pocos-de-caldas-mg": "Poços de Caldas", "pouso-alegre-mg": "Pouso Alegre",
    "sao-lourenco-mg": "São Lourenço", "ouro-preto-mg": "Ouro Preto", "uberlandia-mg": "Uberlândia",
    "florianopolis-sc": "Florianópolis", "porto-alegre-rs": "Porto Alegre",
    "rio-de-janeiro-rj": "Rio de Janeiro", "parati-rj": "Paraty", "ubatuba-sp": "Ubatuba",
    "caraguatatuba-sp": "Caraguatatuba", "sao-sebastiao-sp": "São Sebastião (Ilhabela)",
    "campos-do-jordao-sp": "Campos do Jordão", "curitiba-pr": "Curitiba", "joinville-sc": "Joinville",
    "balneario-camboriu-sc": "Balneário Camboriú", "londrina-pr": "Londrina",
    "ribeirao-preto-sp": "Ribeirão Preto", "brotas-sp": "Brotas",
}
# Quais origens consultar para cada destino (só onde a ClickBus tem linha — mapeado em 24/11/2026).
_PRIO1 = {  # pedido do Lucas: Peruíbe, Minas, Floripa, Porto Alegre
    "peruibe-sp": [TIETE, BFUNDA, SANTO_ANDRE, SBC],
    "belo-horizonte-mg": [TIETE, SANTO_ANDRE, SBC],
    "juiz-de-fora-mg": [TIETE, BFUNDA, SANTO_ANDRE, SBC],
    "pocos-de-caldas-mg": [TIETE, BFUNDA, SANTO_ANDRE],
    "pouso-alegre-mg": [TIETE, BFUNDA],
    "sao-lourenco-mg": [TIETE, BFUNDA, SANTO_ANDRE, SBC],
    "ouro-preto-mg": [TIETE, BFUNDA, SANTO_ANDRE, SBC],
    "uberlandia-mg": [TIETE, SANTO_ANDRE, SBC],
    "florianopolis-sc": [TIETE, SANTO_ANDRE, SBC],
    "porto-alegre-rs": [TIETE, BFUNDA, SANTO_ANDRE, SBC],
}
_PRIO2 = {  # escolhidos por mim: até ~10h de viagem
    "rio-de-janeiro-rj": [TIETE, BFUNDA, SBC],
    "parati-rj": [TIETE, SANTO_ANDRE],
    "ubatuba-sp": [TIETE],
    "caraguatatuba-sp": [TIETE, SBC],
    "sao-sebastiao-sp": [TIETE, SANTO_ANDRE, SBC],
    "campos-do-jordao-sp": [TIETE, SANTO_ANDRE],
    "curitiba-pr": [TIETE, BFUNDA, SANTO_ANDRE],
    "joinville-sc": [TIETE, BFUNDA, SANTO_ANDRE, SBC],
    "balneario-camboriu-sc": [TIETE, BFUNDA],
    "londrina-pr": [TIETE, SBC],
    "ribeirao-preto-sp": [TIETE, SBC],
    "brotas-sp": [TIETE, BFUNDA, SANTO_ANDRE],
}
BUS_ROUTES = [(o, d, _DEST[d], prio) for prio, table in ((1, _PRIO1), (2, _PRIO2))
              for d, origins in table.items() for o in origins]

BUS_MAX_HOURS = {"*": 14, "Porto Alegre": 22}   # viagem mais longa aceita
BUS_DAYS_AHEAD = 60                 # datas de partida consideradas
BUS_EVERY_N_RUNS = {1: 15, 2: 45}   # cada data é revisitada a cada N execuções (rodízio)
BUS_MAX_PAGES_PER_RUN = 220         # teto de buscas por execução
BUS_PAUSE_SECONDS = 1.0             # pausa entre buscas (gentileza com o site)
BUS_TIME_BUDGET_SECONDS = 20 * 60   # tempo máximo de coleta de ônibus por execução

# ---------------------------------------------------------------- DETECTOR
# A ideia: só avisar quando o preço estiver no menor nível já visto para aquela rota,
# E bem abaixo do preço "normal" (mediana). Preço comum nunca vira alerta.
MIN_SAMPLES = 25             # amostras mínimas da rota antes de qualquer alerta
NEAR_RECORD = 1.05           # até 5% acima do menor preço já visto conta como "recorde"
MAX_RATIO_VS_MEDIAN = 0.60   # e precisa estar pelo menos 40% abaixo da mediana
EXTREME_RATIO = 0.40         # 60%+ abaixo da mediana alerta mesmo sem ser recorde (erro tarifário)
MIN_DAYS_AHEAD = 1           # ignora partidas para hoje
HISTORY_DAYS = 180           # janela do histórico usada na comparação
REALERT_DROP = 0.95          # re-alerta a mesma viagem só se cair mais 5%
REALERT_DAYS = 14
MAX_ALERTS_PER_RUN = 6       # se aparecer muita coisa, manda só as melhores
