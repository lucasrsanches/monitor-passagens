"""Configuração do monitor de passagens. Edite aqui sem mexer no resto do código."""

# ---------------------------------------------------------------- AVIÃO
# Código de cidade (Aviasales/Travelpayouts). SAO inclui Campinas (VCP), por isso filtramos
# pelo aeroporto de saída: só Guarulhos e Congonhas (Campinas é longe de Santo André).
FLIGHT_ORIGINS = ["SAO"]
FLIGHT_AIRPORTS = {"GRU", "CGH"}

# ---------------------------------------------------------------- IDA E VOLTA
# Combos de ida e volta: quantas noites no destino.
TRIP_MIN_NIGHTS = 2
TRIP_MAX_NIGHTS = 10
COMBO_LOOKBACK_HOURS = 192  # combos de ônibus usam preços vistos nos últimos 8 dias
NO_SINGLE_ALERT = {"onibus_volta"}   # a volta sozinha não gera alerta, só entra nos combos

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
    "peruibe-sp": "Peruíbe", "belo-horizonte-mg": "Belo Horizonte",
    "florianopolis-sc": "Florianópolis", "porto-alegre-rs": "Porto Alegre",
    "rio-de-janeiro-rj": "Rio de Janeiro", "parati-rj": "Paraty", "ubatuba-sp": "Ubatuba",
    "caraguatatuba-sp": "Caraguatatuba", "sao-sebastiao-sp": "São Sebastião (Ilhabela)",
    "campos-do-jordao-sp": "Campos do Jordão", "curitiba-pr": "Curitiba",
    "balneario-camboriu-sc": "Balneário Camboriú", "brotas-sp": "Brotas",
    "angra-dos-reis-rj": "Angra dos Reis", "cabo-frio-rj": "Cabo Frio", "arraial-do-cabo-rj": "Arraial do Cabo",
    "buzios-rj": "Búzios", "petropolis-rj": "Petrópolis", "bombinhas-sc": "Bombinhas",
    "penha-sc": "Penha (Beto Carrero)", "aguas-de-lindoia-sp": "Águas de Lindóia",
    "serra-negra-sp": "Serra Negra", "guaruja-sp": "Guarujá", "cananeia-sp": "Cananéia",
}
# Quais origens consultar para cada destino na ClickBus (mapeado em 24 e 26/11/2026).
# Mudança de 26/11: de Minas só Belo Horizonte; entraram mais cidades turísticas.
_PRIO1 = {  # pedido do Lucas: Peruíbe, BH, Floripa, Porto Alegre
    "peruibe-sp": [TIETE, BFUNDA, SBC],
    "belo-horizonte-mg": [TIETE, SANTO_ANDRE, SBC],
    "florianopolis-sc": [TIETE, SANTO_ANDRE, SBC],
    "porto-alegre-rs": [TIETE, BFUNDA, SANTO_ANDRE, SBC],
}
_PRIO2 = {  # cidades turísticas
    "rio-de-janeiro-rj": [TIETE, SBC],
    "parati-rj": [TIETE, SANTO_ANDRE],
    "ubatuba-sp": [TIETE],
    "caraguatatuba-sp": [TIETE, SBC],
    "sao-sebastiao-sp": [TIETE, SANTO_ANDRE, SBC],
    "campos-do-jordao-sp": [TIETE, SANTO_ANDRE],
    "curitiba-pr": [TIETE, SANTO_ANDRE],
    "balneario-camboriu-sc": [TIETE],
    "brotas-sp": [TIETE],
    "angra-dos-reis-rj": [TIETE],
    "cabo-frio-rj": [TIETE],
    "arraial-do-cabo-rj": [TIETE],
    "buzios-rj": [TIETE],
    "petropolis-rj": [TIETE],
    "bombinhas-sc": [TIETE],
    "aguas-de-lindoia-sp": [TIETE],
    "serra-negra-sp": [TIETE],
    "guaruja-sp": [TIETE, SBC],
    "cananeia-sp": [TIETE],
}
# (origem, destino, cidade, prioridade, é_volta). A volta é cidade -> SP (chega em qualquer
# rodoviária de SP/ABC); serve para montar os combos de ida e volta.
BUS_ROUTES = ([(o, d, _DEST[d], prio, False) for prio, table in ((1, _PRIO1), (2, _PRIO2))
               for d, origins in table.items() for o in origins]
              + [(d, TIETE, _DEST[d], prio, True) for prio, table in ((1, _PRIO1), (2, _PRIO2))
                 for d in table])

# ---------------------------------------------------------------- ÔNIBUS (Buser)
# A Buser agrupa por cidade. Rotas onde ela tem viagens (mapeado em 24/11/2026; sem Peruíbe).
BUSER_ENABLED = True
_BSP, _BSA, _BSBC = "sao-paulo-sp", "santo-andre-sp", "sao-bernardo-do-campo-sp"
_BUSER = {  # destino slug -> (prioridade, origens)
    "belo-horizonte-mg": (1, [_BSP, _BSA, _BSBC]),
    "florianopolis-sc": (1, [_BSP]),
    "porto-alegre-rs": (1, [_BSP]),
    "rio-de-janeiro-rj": (2, [_BSP, _BSA, _BSBC]),
    "parati-rj": (2, [_BSP]),
    "curitiba-pr": (2, [_BSP, _BSA, _BSBC]),
    "balneario-camboriu-sc": (2, [_BSP]),
    "angra-dos-reis-rj": (2, [_BSP]),
    "cabo-frio-rj": (2, [_BSP]),
    "arraial-do-cabo-rj": (2, [_BSP]),
    "buzios-rj": (2, [_BSP]),
    "penha-sc": (2, [_BSP]),
}
_BUSER_SLUG = {"parati-rj": "paraty-rj", "buzios-rj": "armacao-dos-buzios-rj"}   # grafia da Buser
BUSER_ROUTES = ([(o, _BUSER_SLUG.get(d, d), _DEST[d], prio, False)
                 for d, (prio, origins) in _BUSER.items() for o in origins]
                + [(_BUSER_SLUG.get(d, d), _BSP, _DEST[d], prio, True) for d, (prio, _) in _BUSER.items()])
BUSER_PAUSE_SECONDS = 5.0
BUSER_TIME_BUDGET_SECONDS = 8 * 60

BUS_MAX_HOURS = {"*": 14, "Porto Alegre": 22, "Bombinhas": 16}   # viagem mais longa aceita
BUS_DAYS_AHEAD = 60                 # datas de partida consideradas
BUS_EVERY_N_RUNS = {1: 30, 2: 60}   # cada data é revisitada a cada N execuções (rodízio)
BUS_MAX_PAGES_PER_RUN = 100         # teto de buscas por execução
BUS_PAUSE_SECONDS = 10.0            # pausa entre buscas — a ClickBus limita (HTTP 429) se for rápido
BUS_TIME_BUDGET_SECONDS = 18 * 60   # tempo máximo de coleta de ônibus por execução

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
