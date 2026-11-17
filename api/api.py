"""FluxoMed - API MOCK, 100% SIMULADA, com cobertura configurável por localidade.

Como funciona
- A API aceita qualquer UF/município/distrito:  ?uf=SP&municipio=São Paulo&distrito=Itaquera
  (sem parâmetros = São Paulo / Itaquera).
- Só as localidades listadas em COBERTURA têm dados. Hoje: município de São Paulo + seus 32 distritos (subprefeituras).
  Qualquer outra localidade responde 200 com {"status": "indisponivel", ...} (estado de tela "ainda sem dados").
  Para ampliar a cobertura, acrescente uma linha em COBERTURA.
- Dentro da cobertura o cenário é GERADO com seed fixa (mesma localidade = mesma resposta). Nada é dado real, nem os nomes das unidades.
- Tempo real por padrão: a hora segue o relógio (America/Sao_Paulo) e os números evoluem ao longo do dia (renovam a cada 10 min).
  Para congelar em 11/nov/2026 10h30 (desenvolvimento/prints): FLUXOMED_FROZEN=1.
- Estados de tela em qualquer GET: ?delay_ms=2000 | ?simular=erro|vazio|timeout|offline|indisponivel
- As respostas não trazem texto de exibição: tudo que o app mostra vem de códigos estáveis (ex.: "codigo": "sem_cobertura",
  "nivel": "atencao", "janela": "7d") e de números. A tradução pra texto é responsabilidade do app.

Rodar:  pip install -r requirements.txt && uvicorn api:app --reload     Docs: /docs
"""
import asyncio
import math
import os
import random
import re
import unicodedata
import zlib
from collections.abc import Awaitable, Callable
from datetime import datetime
from functools import lru_cache
from typing import Any, Literal
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ======================= TIPOS =======================
# Os dicionários abaixo são dinâmicos (montados em várias etapas), então ficam como dict[str, Any] com um nome que diz o que carregam.
Localidade = dict[str, Any]  # saída de _resolver_localidade: id, nivel, uf, uf_nome, regiao, municipio, distrito
Unidade = dict[str, Any]     # unidade de saúde gerada (id, nome, tipo, vagas_*, espera_min, aberta, ocupacao_pct, nivel...)
Cenario = dict[str, Any]     # saída de _gerar_cenario / _cenario_cacheado
Alerta = dict[str, Any]
Relato = dict[str, Any]
Kpi = dict[str, Any]
Cobertura = dict[str, Any]   # {"uf", "municipio", "distritos"}
Json = dict[str, Any]        # corpo genérico de resposta

Nivel = Literal["uf", "municipio", "distrito"]
TipoUnidade = Literal["UPA", "UBS", "USF"]
Prioridade = Literal["alta", "moderada", "baixa"]
NivelConfianca = Literal["alta", "moderada", "baixa"]
Janela = Literal["7d", "semana", "mes"]
Simulacao = Literal["erro", "vazio", "timeout", "offline", "indisponivel"]
StatusAlerta = Literal["ativo", "resolvido"]
CodigoSemCobertura = Literal["sem_cobertura", "nivel_nao_disponivel", "distrito_desconhecido", "simulado"]

app = FastAPI(title="FluxoMed - API (dados simulados)", version="4.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], expose_headers=["X-Dados"])

@app.middleware("http")
async def marcar_dados_simulados(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    resposta = await call_next(request)
    resposta.headers["X-Dados"] = "simulados"
    return resposta

FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")
INSTANTE_CONGELADO = datetime(2026, 11, 11, 10, 30, tzinfo=FUSO_HORARIO)
FROZEN: bool = os.getenv("FLUXOMED_FROZEN") == "1"
LIVE: bool = not FROZEN
CHAVE_DEMO = "SP/sao-paulo/itaquera"  # localidade padrão: sempre tem um alerta ativo pra demonstrar o fluxo
AVISO = "dados_simulados"  # código do aviso fixo: dados simulados, nenhuma conduta clínica automatizada
LOCALIDADE_PADRAO: tuple[str, str, str] = ("SP", "São Paulo", "Itaquera")
LIMIAR_ATENCAO_PCT = 85
LIMIAR_DURACAO_MIN = 30
HORARIO_BASICO: tuple[int, int] = (7, 19)  # UBS/USF abrem das 7h às 19h; UPA é 24h

UFS: dict[str, tuple[str, str, str]] = {  # sigla: (nome, região, capital)
    "AC": ("Acre", "norte", "Rio Branco"), "AL": ("Alagoas", "nordeste", "Maceió"), "AP": ("Amapá", "norte", "Macapá"),
    "AM": ("Amazonas", "norte", "Manaus"), "BA": ("Bahia", "nordeste", "Salvador"), "CE": ("Ceará", "nordeste", "Fortaleza"),
    "DF": ("Distrito Federal", "centro-oeste", "Brasília"), "ES": ("Espírito Santo", "sudeste", "Vitória"),
    "GO": ("Goiás", "centro-oeste", "Goiânia"), "MA": ("Maranhão", "nordeste", "São Luís"), "MT": ("Mato Grosso", "centro-oeste", "Cuiabá"),
    "MS": ("Mato Grosso do Sul", "centro-oeste", "Campo Grande"), "MG": ("Minas Gerais", "sudeste", "Belo Horizonte"),
    "PA": ("Pará", "norte", "Belém"), "PB": ("Paraíba", "nordeste", "João Pessoa"), "PR": ("Paraná", "sul", "Curitiba"),
    "PE": ("Pernambuco", "nordeste", "Recife"), "PI": ("Piauí", "nordeste", "Teresina"), "RJ": ("Rio de Janeiro", "sudeste", "Rio de Janeiro"),
    "RN": ("Rio Grande do Norte", "nordeste", "Natal"), "RS": ("Rio Grande do Sul", "sul", "Porto Alegre"),
    "RO": ("Rondônia", "norte", "Porto Velho"), "RR": ("Roraima", "norte", "Boa Vista"), "SC": ("Santa Catarina", "sul", "Florianópolis"),
    "SP": ("São Paulo", "sudeste", "São Paulo"), "SE": ("Sergipe", "nordeste", "Aracaju"), "TO": ("Tocantins", "norte", "Palmas"),
}
SP_DISTRITOS: list[str] = [  # subprefeituras de São Paulo (nomes reais, usados só pra sugestões/grafia correta)
    "Aricanduva/Vila Formosa", "Butantã", "Campo Limpo", "Capela do Socorro", "Casa Verde/Cachoeirinha", "Cidade Ademar", "Cidade Tiradentes",
    "Ermelino Matarazzo", "Freguesia/Brasilândia", "Guaianases", "Ipiranga", "Itaim Paulista", "Itaquera", "Jabaquara", "Jaçanã/Tremembé",
    "Lapa", "M'Boi Mirim", "Mooca", "Parelheiros", "Penha", "Perus", "Pinheiros", "Pirituba/Jaraguá", "Santana/Tucuruvi", "Santo Amaro",
    "São Mateus", "São Miguel Paulista", "Sapopemba", "Vila Prudente", "Sé", "Vila Maria/Vila Guilherme", "Vila Mariana"]
# Nomes de unidades e microáreas são FICTÍCIOS (evita atribuir dado simulado a lugares reais).
BAIRROS: list[str] = ["Alto do Céu", "Nova Aurora", "Vila Esperança", "Beira Rio", "Campo Verde", "Morro do Sol", "Santa Clara", "Jardim Primavera",
                      "Água Fria", "Bela Vista", "Planalto", "Cajueiro Novo", "Rio Doce", "Mangueira", "Poço Novo", "Rosa Branca", "São José", "Vila Nova"]
REGIOES: list[str] = ["Região Norte", "Região Sul", "Região Leste", "Região Oeste", "Região Central", "Periferia"]

def _aleatorio(*chaves: object) -> random.Random:
    return random.Random("|".join(map(str, chaves)))

def _slug(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", texto).strip("-")

NOMES_CURADOS: dict[str, str] = {_slug(nome): nome for nome in [capital for _, _, capital in UFS.values()] + SP_DISTRITOS}

def _canonizar_nome(nome: str) -> str:
    nome = " ".join(nome.split())
    return NOMES_CURADOS.get(_slug(nome)) or (nome.title() if nome.islower() else nome)

def _montar_kpi(valor: float, variacao: int | None = None, unidade_variacao: str | None = None, janela: Janela | None = None, **extra: Any) -> Kpi:
    """KPI com variação estruturada: {"valor", "variacao", "unidade_variacao", "janela"}. Janelas: "7d" | "semana" | "mes"."""
    kpi: Kpi = {"valor": valor}
    if variacao is not None:
        kpi.update(variacao=variacao, unidade_variacao=unidade_variacao, janela=janela)
    kpi.update(extra)
    return kpi

def _nivel_confianca(confianca: float) -> NivelConfianca:
    return "alta" if confianca >= 0.8 else "moderada" if confianca >= 0.6 else "baixa"

def _agora() -> datetime:
    if not LIVE:
        return INSTANTE_CONGELADO
    agora = datetime.now(FUSO_HORARIO)
    return agora.replace(minute=agora.minute // 10 * 10, second=0, microsecond=0)

# ======================= LOCALIDADE =======================
def _resolver_localidade(uf: str | None, municipio: str | None, distrito: str | None, checar: bool = True) -> Localidade:
    if not (uf or municipio or distrito):
        uf, municipio, distrito = LOCALIDADE_PADRAO
    if not uf:
        raise HTTPException(422, detail={"codigo": "uf_obrigatoria"})
    uf = uf.strip().upper()
    if uf not in UFS:
        raise HTTPException(404, detail={"codigo": "uf_invalida", "uf": uf})
    municipio_canonico = _canonizar_nome(municipio) if municipio and municipio.strip() else None
    distrito_canonico = _canonizar_nome(distrito) if distrito and distrito.strip() else None
    if distrito_canonico and not municipio_canonico:
        raise HTTPException(422, detail={"codigo": "municipio_obrigatorio"})
    nivel: Nivel = "distrito" if distrito_canonico else "municipio" if municipio_canonico else "uf"
    chave = "/".join(parte for parte in [uf, _slug(municipio_canonico) if municipio_canonico else "",
                                         _slug(distrito_canonico) if distrito_canonico else ""] if parte)
    uf_nome, regiao, _ = UFS[uf]
    localidade: Localidade = {"id": chave, "nivel": nivel, "uf": uf, "uf_nome": uf_nome, "regiao": regiao,
                              "municipio": municipio_canonico, "distrito": distrito_canonico}
    if checar:
        _checar_cobertura(localidade)
    return localidade

async def simulacao_query(delay_ms: int = Query(0, ge=0, le=10_000, description="Atraso artificial (loading)"),
                          simular: Simulacao | None = Query(None)) -> Simulacao | None:
    if simular == "timeout":
        await asyncio.sleep(15)
    if delay_ms:
        await asyncio.sleep(delay_ms / 1000)
    if simular == "erro":
        raise HTTPException(500, detail={"codigo": "erro_simulado"})
    if simular == "offline":
        raise HTTPException(503, detail={"codigo": "sem_conexao", "copia_disponivel": True, "copia_de": _agora().isoformat()})
    return simular

async def localidade_query(uf: str | None = Query(None, description="Sigla da UF. Sem nenhum parâmetro de local = São Paulo / Itaquera"),
                           municipio: str | None = Query(None, description="Município (hoje com dados: São Paulo)"),
                           distrito: str | None = Query(None, description="Distrito/subprefeitura (ex.: Itaquera)"),
                           simulacao: Simulacao | None = Depends(simulacao_query)) -> Localidade:
    localidade = _resolver_localidade(uf, municipio, distrito)
    if simulacao == "indisponivel":
        raise SemCobertura(localidade, "simulado")
    return localidade


# ======================= COBERTURA =======================
# Só estas localidades têm dados. Para ampliar: adicione uma linha ("UF/slug-do-municipio": {...}).
COBERTURA: dict[str, Cobertura] = {"SP/sao-paulo": {"uf": "SP", "municipio": "São Paulo", "distritos": SP_DISTRITOS}}

class SemCobertura(Exception):
    def __init__(self, localidade: Localidade, codigo: CodigoSemCobertura, alternativas: list[dict[str, str]] | None = None) -> None:
        self.localidade, self.codigo, self.alternativas = localidade, codigo, alternativas or []

def _locais_cobertos() -> list[Json]:
    return [{"uf": cobertura["uf"], "municipio": cobertura["municipio"], "nivel": "municipio_e_distritos", "distritos": len(cobertura["distritos"])}
            for cobertura in COBERTURA.values()]

def _checar_cobertura(localidade: Localidade) -> None:
    uf: str = localidade["uf"]
    if localidade["nivel"] == "uf":
        municipios_cobertos = [cobertura["municipio"] for cobertura in COBERTURA.values() if cobertura["uf"] == uf]
        raise SemCobertura(localidade, "nivel_nao_disponivel" if municipios_cobertos else "sem_cobertura",
                           [{"tipo": "municipio", "uf": uf, "municipio": municipio} for municipio in municipios_cobertos])
    chave_cobertura = f"{uf}/{_slug(localidade['municipio'])}"
    cobertura = COBERTURA.get(chave_cobertura)
    if not cobertura:
        raise SemCobertura(localidade, "sem_cobertura")
    if localidade["nivel"] == "distrito" and cobertura["distritos"]:
        distrito_slug = _slug(localidade["distrito"])
        distritos: list[str] = cobertura["distritos"]
        exatos = [distrito for distrito in distritos if _slug(distrito) == distrito_slug]
        parciais = [distrito for distrito in distritos if distrito_slug and distrito_slug in _slug(distrito)]
        encontrados = exatos or (parciais if len(parciais) == 1 else [])
        if not encontrados:
            sugestoes = (parciais or distritos)[:8]
            raise SemCobertura(localidade, "distrito_desconhecido",
                               [{"tipo": "distrito", "uf": uf, "municipio": cobertura["municipio"], "distrito": distrito} for distrito in sugestoes])
        distrito = encontrados[0]
        localidade.update(distrito=distrito, id=f"{chave_cobertura}/{_slug(distrito)}")

def _envelope_sem_cobertura(excecao: SemCobertura) -> Json:
    return {"status": "indisponivel", "codigo": excecao.codigo, "territorio": excecao.localidade, "locais_cobertos": _locais_cobertos(),
            "alternativas": excecao.alternativas, "aviso": AVISO}

@app.exception_handler(SemCobertura)
async def tratar_sem_cobertura(request: Request, excecao: SemCobertura) -> JSONResponse:
    corpo = _envelope_sem_cobertura(excecao)
    return JSONResponse(corpo, status_code=200) if request.method == "GET" else JSONResponse({"detail": corpo}, status_code=422)

# ======================= GERADOR DE CENÁRIO =======================
def _montar_unidade(nome: str, tipo: TipoUnidade, vagas_total: int, vagas_ocupadas: int, espera_min: int | None) -> Unidade:
    return {"id": _slug(nome), "nome": nome, "tipo": tipo, "vagas_total": vagas_total, "vagas_ocupadas": vagas_ocupadas, "espera_min": espera_min}

def _perfil_diurno(tipo: TipoUnidade, hora: float) -> float:  # perfil de demanda ao longo do dia (relativo)
    def gauss(centro: float, largura: float) -> float:
        return math.exp(-(((hora - centro) / largura) ** 2))
    return 0.82 + 0.33 * gauss(10, 2.5) + 0.28 * gauss(19, 2.5) if tipo == "UPA" else 0.85 + 0.3 * gauss(9, 2.2) + 0.15 * gauss(14, 2)

def _ocupacao_demo(hora: float) -> float:  # UPA da localidade padrão: sempre >85%, com curva ao longo do dia (alerta sempre disponível pra demonstrar)
    normalizado = min(1.0, max(0.0, (_perfil_diurno("UPA", hora % 24) - 0.82) / (_perfil_diurno("UPA", 10) - 0.82)))
    return 0.86 + 0.12 * normalizado

def _gerar_cenario(chave: str, nivel: Nivel, hora: int, janela_tempo: str) -> Cenario:
    rng_territorio, rng_tempo = _aleatorio("territorio", chave), _aleatorio("tempo", chave, janela_tempo)
    qtd_unidades = {"distrito": rng_territorio.randint(10, 18), "municipio": rng_territorio.randint(20, 36), "uf": rng_territorio.randint(30, 48)}[nivel]
    escala = {"distrito": 1, "municipio": 1.6, "uf": 2.2}[nivel]
    qtd_upas = max(1, round(qtd_unidades / 9))
    sob_pressao = chave == CHAVE_DEMO or rng_territorio.random() < 0.65
    bairros_embaralhados = rng_territorio.sample(BAIRROS, len(BAIRROS))
    unidades: list[Unidade] = []
    for indice in range(qtd_unidades):
        tipo: TipoUnidade = "UPA" if indice < qtd_upas else rng_territorio.choice(["UBS", "USF"])
        nome = f"{tipo} {bairros_embaralhados[indice % len(bairros_embaralhados)]}" + \
            (f" {indice // len(bairros_embaralhados) + 1}" if indice >= len(bairros_embaralhados) else "")
        vagas_total = round((rng_territorio.randint(40, 60) if tipo == "UPA" else rng_territorio.randint(5, 45)) * escala)
        if tipo == "UPA":
            ocupacao_base = rng_territorio.uniform(0.88, 0.97) if (sob_pressao and indice == 0) else rng_territorio.uniform(0.6, 0.97 if sob_pressao else 0.84)
        else:
            ocupacao_base = rng_territorio.uniform(0.5, 0.82)
        ocupacao = ocupacao_base * _perfil_diurno(tipo, hora) / _perfil_diurno(tipo, 10) + rng_tempo.uniform(-0.02, 0.02)
        if chave == CHAVE_DEMO and indice == 0:
            ocupacao = _ocupacao_demo(hora) + rng_tempo.uniform(0, 0.015)
        ocupacao = min(0.99, max(0.05, ocupacao))
        aberta = tipo == "UPA" or HORARIO_BASICO[0] <= hora < HORARIO_BASICO[1]
        espera_min = (round(18 + ocupacao * 60 + rng_tempo.uniform(-5, 5)) if tipo == "UPA" else round(8 + ocupacao * 30)) if aberta else None
        unidade = _montar_unidade(nome, tipo, vagas_total, round(vagas_total * ocupacao) if aberta else 0, espera_min)
        unidade["aberta"], unidade["_ocupacao_base"] = aberta, ocupacao_base
        unidades.append(unidade)
    abertas = [unidade for unidade in unidades if unidade["aberta"]]
    prioridades_possiveis: list[Prioridade] = ["alta", "moderada", "moderada", "baixa"]
    areas: list[tuple[str, Prioridade]] = \
        [(bairro, rng_territorio.choice(prioridades_possiveis)) for bairro in rng_territorio.sample(BAIRROS, 6)] if nivel == "distrito" \
        else [(regiao, rng_territorio.choice(prioridades_possiveis)) for regiao in REGIOES]
    upa_mais_cheia = max((unidade for unidade in unidades if unidade["tipo"] == "UPA"), key=lambda unidade: unidade["vagas_ocupadas"] / unidade["vagas_total"])
    ocupacao_atual_pct = round(100 * upa_mais_cheia["vagas_ocupadas"] / upa_mais_cheia["vagas_total"])
    usa_curva_demo = chave == CHAVE_DEMO and upa_mais_cheia is unidades[0]

    def ocupacao_pct_na_hora(hora_alvo: int) -> int:
        fracao = _ocupacao_demo(hora_alvo % 24) if usa_curva_demo \
            else upa_mais_cheia["_ocupacao_base"] * _perfil_diurno("UPA", hora_alvo % 24) / _perfil_diurno("UPA", 10)
        return round(100 * min(0.99, max(0.05, fracao)))
    observados = [ocupacao_pct_na_hora(hora - 4 + passo) for passo in range(4)] + [ocupacao_atual_pct]
    projetados = [ocupacao_pct_na_hora(hora + passo) for passo in range(1, 5)]
    return {"unidades": unidades, "areas": areas, "nivel_area": "microarea" if nivel == "distrito" else "regiao", "hora": hora,
            "equipes": round(qtd_unidades * rng_territorio.uniform(1.8, 2.4)), "clima_max": rng_territorio.randint(27, 36),
            "cobertura": rng_territorio.randint(68, 93), "visitas": round(rng_territorio.randint(28, 70) * escala),
            "rede_espera": round(sum(unidade["espera_min"] for unidade in abertas) / len(abertas)),
            "espera_evitada_h": round(rng_territorio.randint(60, 260) * escala), "plano_ativo": 0,
            "variacoes": {"ocupacao": rng_territorio.randint(-8, 8), "espera": rng_territorio.randint(-14, 14), "vagas": rng_territorio.randint(-10, 20),
                          "equipes": rng_territorio.randint(0, 5), "clima": rng_territorio.randint(-2, 4), "cobertura": rng_territorio.randint(-2, 3),
                          "visitas": rng_territorio.randint(-6, 12), "evitada_pct": rng_territorio.randint(5, 25)},
            "serie_upa": {"nome": upa_mais_cheia["nome"], "observados": observados, "projetados": projetados},
            "confianca": round(rng_territorio.uniform(0.55, 0.88), 2)}

ALERTAS: dict[str, Alerta] = {}
ALERTA_POR_TERRITORIO: dict[str, str] = {}  # id da localidade -> id do alerta

def _montar_alerta(localidade: Localidade, cenario: Cenario, unidade: Unidade, alerta_id: str) -> Alerta:
    serie: dict[str, Any] = cenario["serie_upa"]
    projecao_pct: int = serie["projetados"][-1] if serie["nome"] == unidade["nome"] else min(99, unidade["ocupacao_pct"] + 3)
    return {
        "id": alerta_id, "territorio": localidade, "unidade_id": unidade["id"], "unidade": unidade["nome"], "gravidade": "atencao",
        "tipo": "risco_superlotacao", "gerado_em": _agora().isoformat(), "atualizado_em": _agora().isoformat(),
        "previsao_hora": (cenario["hora"] + 4) % 24,
        "projecao": {"valor_pct": projecao_pct, "faixa_min_pct": max(0, projecao_pct - 6), "faixa_max_pct": min(100, projecao_pct + 4),
                     "ocupacao_atual_pct": unidade["ocupacao_pct"], "horizonte_h": 4},
        "regra": {"limiar_pct": LIMIAR_ATENCAO_PCT, "duracao_min": LIMIAR_DURACAO_MIN},
        # motivos pelos quais o alerta apareceu; o app traduz cada código pra texto
        "motivos": [
            {"codigo": "ocupacao_acima_limite", "ocupacao_pct": unidade["ocupacao_pct"], "limiar_pct": LIMIAR_ATENCAO_PCT, "duracao_min": LIMIAR_DURACAO_MIN},
            {"codigo": "entradas_maiores_que_saidas"},
            {"codigo": "padrao_historico_horario"}],
        "confianca": cenario["confianca"], "nivel_confianca": _nivel_confianca(cenario["confianca"]),
        "limitacoes": ["cenario_demonstrativo", "projecao_curto_prazo_historico_simulado", "nao_considera_eventos_extraordinarios"],
        "unidades_validas": [outra["id"] for outra in cenario["unidades"]], "status": "ativo", "avaliacao": None, "auto": False, "avisos": [AVISO]}

def _atualizar_alerta(localidade: Localidade, cenario: Cenario) -> None:
    """Alerta surge quando uma UPA passa de 85%, é atualizado enquanto durar e se resolve sozinho quando a ocupação cai."""
    upas_acima_do_limite = [unidade for unidade in cenario["unidades"] if unidade["tipo"] == "UPA" and unidade["ocupacao_pct"] > LIMIAR_ATENCAO_PCT]
    upa_mais_cheia = max(upas_acima_do_limite, key=lambda upa: upa["ocupacao_pct"]) if upas_acima_do_limite else None
    alerta_id = ALERTA_POR_TERRITORIO.get(localidade["id"])
    if alerta_id is None:
        if not upa_mais_cheia:
            return
        numero = 100 + zlib.crc32(localidade["id"].encode()) % 900
        while f"ALT-{numero}" in ALERTAS:
            numero = 100 + (numero - 99) % 900
        alerta_id = f"ALT-{numero}"
        ALERTAS[alerta_id] = _montar_alerta(localidade, cenario, upa_mais_cheia, alerta_id)
        ALERTA_POR_TERRITORIO[localidade["id"]] = alerta_id
        return
    alerta = ALERTAS[alerta_id]
    if upa_mais_cheia:
        if alerta["status"] == "resolvido" and alerta.get("auto"):
            alerta["status"] = "ativo"
        if alerta["status"] == "ativo":
            alerta_novo = _montar_alerta(localidade, cenario, upa_mais_cheia, alerta_id)
            alerta_novo.update(gerado_em=alerta["gerado_em"], avaliacao=alerta["avaliacao"], auto=alerta["auto"])
            ALERTAS[alerta_id] = alerta_novo
    elif alerta["status"] == "ativo":
        alerta["status"], alerta["auto"] = "resolvido", True

@lru_cache(maxsize=512)
def _cenario_cacheado(chave: str, nivel: Nivel, janela_tempo: str) -> Cenario:
    cenario = _gerar_cenario(chave, nivel, _agora().hour, janela_tempo)
    for unidade in cenario["unidades"]:
        unidade["ocupacao_pct"] = round(100 * unidade["vagas_ocupadas"] / unidade["vagas_total"])
        unidade["vagas_livres"] = unidade["vagas_total"] - unidade["vagas_ocupadas"] if unidade["aberta"] else 0
        unidade["nivel"] = "fechada" if not unidade["aberta"] else "atencao" if unidade["ocupacao_pct"] > LIMIAR_ATENCAO_PCT else "estavel"
    cenario["em_atencao"] = sum(1 for unidade in cenario["unidades"] if unidade["nivel"] == "atencao")
    cenario["plano_ativo"] = min(cenario["em_atencao"], _aleatorio("plano", chave).randint(0, 2))
    return cenario

def _cenario(localidade: Localidade) -> Cenario:
    cenario = _cenario_cacheado(localidade["id"], localidade["nivel"], _agora().isoformat() if LIVE else "fixo")
    _atualizar_alerta(localidade, cenario)
    return cenario

def _totais_rede(cenario: Cenario) -> tuple[int, int, int, int]:
    """Devolve (vagas_total, vagas_ocupadas, vagas_livres, ocupacao_pct) considerando só unidades abertas."""
    abertas = [unidade for unidade in cenario["unidades"] if unidade["aberta"]]
    vagas_total: int = sum(unidade["vagas_total"] for unidade in abertas)
    vagas_ocupadas: int = sum(unidade["vagas_ocupadas"] for unidade in abertas)
    return vagas_total, vagas_ocupadas, vagas_total - vagas_ocupadas, round(100 * vagas_ocupadas / vagas_total)

def _cabecalho(localidade: Localidade) -> Json:
    return {"territorio": localidade, "atualizado_em": _agora().isoformat(), "modo_tempo": "tempo_real" if LIVE else "congelado", "aviso": AVISO}

def _alerta_destaque(localidade: Localidade) -> Json | None:
    alerta = ALERTAS.get(ALERTA_POR_TERRITORIO.get(localidade["id"], ""))
    if not alerta or alerta["status"] != "ativo":
        return None
    return {campo: alerta[campo] for campo in ("id", "tipo", "gravidade", "unidade_id", "unidade", "previsao_hora", "nivel_confianca")}

RELATOS: list[Relato] = []
PREFERENCIAS: dict[str, bool] = {"texto_ampliado": False}
PROXIMO_NUMERO_RELATO: list[int] = [1042]  # lista de 1 item pra ser mutável a partir das rotas

# ======================= LOCALIDADES / BRASIL =======================
@app.get("/")
async def raiz() -> Json:
    return {"api": "fluxomed_mock", "dados": "simulados", "docs": "/docs", "referencia": _agora().isoformat(),
            "localidade_padrao": dict(zip(("uf", "municipio", "distrito"), LOCALIDADE_PADRAO)), "cobertura": _locais_cobertos()}

@app.get("/cobertura")
async def cobertura(simulacao: Simulacao | None = Depends(simulacao_query)) -> Json:
    """Onde existem dados hoje. Para ampliar: adicionar uma linha em COBERTURA (município e, opcionalmente, lista de distritos)."""
    return {"locais_cobertos": [] if simulacao == "vazio" else _locais_cobertos(), "demais_localidades": "indisponivel"}

@app.get("/localidades/ufs")
async def listar_ufs(simulacao: Simulacao | None = Depends(simulacao_query)) -> list[Json]:
    if simulacao == "vazio":
        return []
    return [{"uf": sigla, "nome": nome, "regiao": regiao, "capital": capital,
             "cobertura": "parcial" if any(cobertura["uf"] == sigla for cobertura in COBERTURA.values()) else "sem_cobertura"}
            for sigla, (nome, regiao, capital) in UFS.items()]

@app.get("/localidades/sugestoes")
async def sugerir_localidades(busca: str = Query("", alias="q", description="Busca por UF, capital ou distrito"), apenas_disponiveis: bool = False,
                              simulacao: Simulacao | None = Depends(simulacao_query)) -> list[Json]:
    """Atalhos pro seletor do app. Qualquer texto é aceito nas rotas, mas só o que está em COBERTURA tem dados."""
    if simulacao == "vazio":
        return []
    chaves_cobertas = set(COBERTURA)
    # (texto de busca, item): o texto é só pra filtrar, não vai na resposta
    candidatos: list[tuple[str, Json]] = [(f"{nome} {sigla}", {"tipo": "uf", "uf": sigla, "nome": nome, "disponivel": False}) for sigla, (nome, _, _) in UFS.items()]
    candidatos += [(f"{capital} {sigla}", {"tipo": "municipio", "uf": sigla, "municipio": capital, "disponivel": f"{sigla}/{_slug(capital)}" in chaves_cobertas})
                   for sigla, (_, _, capital) in UFS.items()]
    candidatos += [(f"{distrito} São Paulo SP", {"tipo": "distrito", "uf": "SP", "municipio": "São Paulo", "distrito": distrito, "disponivel": True})
                   for distrito in SP_DISTRITOS]
    busca_slug = _slug(busca)
    return [item for texto_busca, item in candidatos if busca_slug in _slug(texto_busca) and (item["disponivel"] or not apenas_disponiveis)][:60]

@app.get("/localidade")
async def consultar_localidade(localidade: Localidade = Depends(localidade_query), simulacao: Simulacao | None = Depends(simulacao_query)) -> Json:
    """Confere se a localidade tem dados. Fora da cobertura devolve status 'indisponivel'."""
    cenario = _cenario(localidade)
    return {"status": "disponivel", **localidade, "unidades": len(cenario["unidades"]), "em_atencao": cenario["em_atencao"],
            "alerta_ativo": _alerta_destaque(localidade) is not None}

@app.get("/brasil/ufs")
async def visao_brasil(regiao: str | None = None, simulacao: Simulacao | None = Depends(simulacao_query)) -> list[Json]:
    """Visão nacional: UFs com dados (parcial) e UFs sem cobertura."""
    if simulacao == "vazio":
        return []
    com_dados: list[Json] = []
    sem_dados: list[Json] = []
    for sigla, (nome, regiao_uf, _) in UFS.items():
        if regiao and regiao_uf != _slug(regiao):
            continue
        coberturas_da_uf = [cobertura for cobertura in COBERTURA.values() if cobertura["uf"] == sigla]
        if not coberturas_da_uf:
            sem_dados.append({"uf": sigla, "nome": nome, "regiao": regiao_uf, "status": "sem_cobertura"})
            continue
        cobertura = coberturas_da_uf[0]
        localidade = _resolver_localidade(sigla, cobertura["municipio"], None)
        cenario = _cenario(localidade)
        _, _, _, ocupacao_pct = _totais_rede(cenario)
        com_dados.append({"uf": sigla, "nome": nome, "regiao": regiao_uf, "status": "parcial", "escopo": {"municipio": cobertura["municipio"], "nivel": "municipio"},
                          "ocupacao_rede_pct": ocupacao_pct, "espera_media_min": cenario["rede_espera"], "unidades_em_atencao": cenario["em_atencao"],
                          "total_unidades": len(cenario["unidades"]), "alerta_ativo": _alerta_destaque(localidade) is not None})
    return sorted(com_dados, key=lambda item: -item["ocupacao_rede_pct"]) + sem_dados

# ======================= CIDADÃO =======================
def _unidade_publica(unidade: Unidade) -> Json:
    campos = ("id", "nome", "tipo", "aberta", "ocupacao_pct", "vagas_livres", "vagas_total", "espera_min", "nivel")
    return {campo: unidade[campo] for campo in campos} | {
        "atendimento": "24h" if unidade["tipo"] == "UPA" else "basico",
        "horario": None if unidade["tipo"] == "UPA" else {"abre": HORARIO_BASICO[0], "fecha": HORARIO_BASICO[1]}}

@app.get("/cidadao/inicio")
async def cidadao_inicio(localidade: Localidade = Depends(localidade_query), simulacao: Simulacao | None = Depends(simulacao_query)) -> Json:
    cenario = _cenario(localidade)
    unidade_mais_cheia = max(cenario["unidades"], key=lambda unidade: unidade["ocupacao_pct"])
    alta_procura = unidade_mais_cheia["nivel"] == "atencao"
    return {**_cabecalho(localidade), "destaque": {"tipo": "alta_procura" if alta_procura else "estavel", "unidade_id": unidade_mais_cheia["id"],
                                                   "unidade": _unidade_publica(unidade_mais_cheia)}}

@app.get("/cidadao/unidades")
async def cidadao_unidades(localidade: Localidade = Depends(localidade_query), tipo: TipoUnidade | None = None,
                           simulacao: Simulacao | None = Depends(simulacao_query)) -> Json:
    cenario = _cenario(localidade)
    if simulacao == "vazio":
        return {**_cabecalho(localidade), "unidades": []}
    unidades_filtradas = sorted([unidade for unidade in cenario["unidades"] if not tipo or unidade["tipo"] == tipo],
                                key=lambda unidade: -unidade["ocupacao_pct"])
    return {**_cabecalho(localidade), "unidades": [_unidade_publica(unidade) for unidade in unidades_filtradas]}

@app.get("/cidadao/unidades/{unidade_id}")
async def cidadao_unidade(unidade_id: str, localidade: Localidade = Depends(localidade_query), simulacao: Simulacao | None = Depends(simulacao_query)) -> Json:
    unidade = next((unidade for unidade in _cenario(localidade)["unidades"] if unidade["id"] == unidade_id), None)
    if not unidade:
        raise HTTPException(404, detail={"codigo": "unidade_nao_encontrada"})
    return {**_cabecalho(localidade), **_unidade_publica(unidade)}

TIPOS_RELATO: list[str] = ["espera_prolongada", "falta_de_insumos", "estrutura", "atendimento", "outro"]
QUANDO_RELATO: list[str] = ["agora", "hoje", "ontem", "esta_semana"]
DESCRICAO_MIN = 20

@app.get("/cidadao/relatos/opcoes")
async def cidadao_relato_opcoes(localidade: Localidade = Depends(localidade_query), simulacao: Simulacao | None = Depends(simulacao_query)) -> Json:
    cenario = _cenario(localidade)
    return {"unidades": [{"id": unidade["id"], "nome": unidade["nome"]} for unidade in cenario["unidades"]],
            "areas": [nome_area for nome_area, _ in cenario["areas"]], "nivel_area": cenario["nivel_area"],
            "tipos": TIPOS_RELATO, "quando": QUANDO_RELATO, "descricao_min": DESCRICAO_MIN}

class RelatoIn(BaseModel):
    uf: str | None = None
    municipio: str | None = None
    distrito: str | None = None
    unidade_id: str | None = None
    tipo_ocorrencia: str | None = None
    area: str | None = None
    quando: str | None = None
    descricao: str | None = None
    consentimento_uso_agregado: bool | None = None

def _erro_validacao(campos: list[Json]) -> HTTPException:
    """422 padrão: {"codigo": "validacao", "campos": [{"campo", "codigo": obrigatorio|invalido|tamanho_minimo, ...}]}."""
    return HTTPException(422, detail={"codigo": "validacao", "campos": campos})

@app.post("/cidadao/relatos", status_code=201)
async def cidadao_criar_relato(corpo: RelatoIn) -> Relato:
    """Relato anônimo (sem CPF, nome ou contato). Localidade no corpo: uf/municipio/distrito."""
    localidade = _resolver_localidade(corpo.uf, corpo.municipio, corpo.distrito)
    cenario = _cenario(localidade)
    erros: list[Json] = []
    unidade = next((unidade for unidade in cenario["unidades"] if unidade["id"] == corpo.unidade_id), None)
    if not unidade:
        erros.append({"campo": "unidade_id", "codigo": "obrigatorio"})
    if corpo.tipo_ocorrencia not in TIPOS_RELATO:
        erros.append({"campo": "tipo_ocorrencia", "codigo": "obrigatorio"})
    if corpo.quando not in QUANDO_RELATO:
        erros.append({"campo": "quando", "codigo": "obrigatorio"})
    if not corpo.descricao or len(corpo.descricao.strip()) < DESCRICAO_MIN:
        erros.append({"campo": "descricao", "codigo": "tamanho_minimo", "minimo": DESCRICAO_MIN})
    if corpo.area and corpo.area not in [nome_area for nome_area, _ in cenario["areas"]]:
        erros.append({"campo": "area", "codigo": "invalido"})
    if erros:
        raise _erro_validacao(erros)
    assert unidade is not None and corpo.descricao is not None  # garantido pela validação acima; só estreita o tipo
    if not corpo.consentimento_uso_agregado:
        raise _erro_validacao([{"campo": "consentimento_uso_agregado", "codigo": "obrigatorio"}])
    relato_id = f"OC-{PROXIMO_NUMERO_RELATO[0]}"
    PROXIMO_NUMERO_RELATO[0] += 1
    relato: Relato = {"id": relato_id, "territorio": localidade, "unidade_id": unidade["id"], "unidade": unidade["nome"],
                      "tipo_ocorrencia": corpo.tipo_ocorrencia, "area": corpo.area, "quando": corpo.quando, "descricao": corpo.descricao.strip(),
                      "registrado_em": _agora().isoformat(), "status": "em_analise"}
    RELATOS.append(relato)
    return relato

@app.get("/cidadao/relatos")
async def cidadao_relatos(simulacao: Simulacao | None = Depends(simulacao_query)) -> list[Relato]:
    """Começa vazio (estado 'você ainda não registrou um relato')."""
    return [] if simulacao == "vazio" else RELATOS

@app.get("/cidadao/relatos/{relato_id}")
async def cidadao_relato(relato_id: str, simulacao: Simulacao | None = Depends(simulacao_query)) -> Relato:
    relato = next((relato for relato in RELATOS if relato["id"] == relato_id.upper()), None)
    if not relato:
        raise HTTPException(404, detail={"codigo": "relato_nao_encontrado"})
    return relato

class PreferenciasIn(BaseModel):
    texto_ampliado: bool

@app.get("/cidadao/preferencias")
async def cidadao_preferencias(simulacao: Simulacao | None = Depends(simulacao_query)) -> Json:
    return {**PREFERENCIAS, "privacidade": "anonimo"}

@app.put("/cidadao/preferencias")
async def cidadao_salvar_preferencias(corpo: PreferenciasIn) -> dict[str, bool]:
    PREFERENCIAS["texto_ampliado"] = corpo.texto_ampliado
    return PREFERENCIAS

# ======================= GESTOR =======================
@app.get("/gestor/rede")
async def gestor_rede(localidade: Localidade = Depends(localidade_query), simulacao: Simulacao | None = Depends(simulacao_query)) -> Json:
    cenario = _cenario(localidade)
    if simulacao == "vazio":
        return {**_cabecalho(localidade), "kpis": None, "alerta_destaque": None}
    variacoes: dict[str, int] = cenario["variacoes"]
    _, _, _, ocupacao_pct = _totais_rede(cenario)
    return {**_cabecalho(localidade), "status_rede": "monitorando", "kpis": {
        "ocupacao_rede": _montar_kpi(ocupacao_pct, variacoes["ocupacao"], "pp", "7d", unidade="%"),
        "espera_media": _montar_kpi(cenario["rede_espera"], variacoes["espera"], "min", "7d", unidade="min"),
        "em_atencao": {"valor": cenario["em_atencao"], "total": len(cenario["unidades"]), "plano_ativo": cenario["plano_ativo"]},
        "espera_evitada": _montar_kpi(cenario["espera_evitada_h"], variacoes["evitada_pct"], "%", "mes", unidade="h", origem="estimativa_simulada")},
        "alerta_destaque": _alerta_destaque(localidade)}

@app.get("/gestor/capacidade")
async def gestor_capacidade(localidade: Localidade = Depends(localidade_query), simulacao: Simulacao | None = Depends(simulacao_query)) -> Json:
    cenario = _cenario(localidade)
    if simulacao == "vazio":
        return {**_cabecalho(localidade), "kpis": None, "unidades": []}
    variacoes: dict[str, int] = cenario["variacoes"]
    vagas_total, _, vagas_livres, _ = _totais_rede(cenario)
    unidades_ordenadas = sorted(cenario["unidades"], key=lambda unidade: -unidade["ocupacao_pct"])
    return {**_cabecalho(localidade), "unidades_total": len(cenario["unidades"]),
            "unidades_abertas": sum(1 for unidade in cenario["unidades"] if unidade["aberta"]), "kpis": {
        "vagas_totais": _montar_kpi(vagas_total, variacoes["vagas"], None, "7d"),
        "vagas_livres": _montar_kpi(vagas_livres, pct_capacidade=round(100 * vagas_livres / vagas_total)),
        "espera_media": _montar_kpi(cenario["rede_espera"], variacoes["espera"], "min", "7d", unidade="min"),
        "equipes": _montar_kpi(cenario["equipes"], variacoes["equipes"], None, "semana")},
        "limiar_atencao_pct": LIMIAR_ATENCAO_PCT,
        "unidades": [{"id": unidade["id"], "nome": unidade["nome"], "tipo": unidade["tipo"], "aberta": unidade["aberta"],
                      "ocupacao_pct": unidade["ocupacao_pct"], "acima_do_limite": unidade["nivel"] == "atencao"} for unidade in unidades_ordenadas],
        "alerta_destaque": _alerta_destaque(localidade)}

@app.get("/gestor/territorio")
async def gestor_territorio(localidade: Localidade = Depends(localidade_query), simulacao: Simulacao | None = Depends(simulacao_query)) -> Json:
    cenario = _cenario(localidade)
    if simulacao == "vazio":
        return {**_cabecalho(localidade), "kpis": None, "prioridades": []}
    variacoes: dict[str, int] = cenario["variacoes"]
    areas: list[tuple[str, Prioridade]] = cenario["areas"]
    areas_alta_prioridade = sum(1 for _, prioridade in areas if prioridade == "alta")
    ordem_prioridade: dict[Prioridade, int] = {"alta": 0, "moderada": 1, "baixa": 2}
    return {**_cabecalho(localidade), "kpis": {
        "maxima_do_dia": _montar_kpi(cenario["clima_max"], variacoes["clima"], "°C", "7d", unidade="°C"),
        "cobertura": _montar_kpi(cenario["cobertura"], variacoes["cobertura"], "pp", "mes", unidade="%"),
        "areas_prioritarias": {"valor": areas_alta_prioridade, "total": len(areas), "criterio": "social"},
        "visitas_previstas": _montar_kpi(cenario["visitas"], variacoes["visitas"], None, "semana")},
        "nivel_area": cenario["nivel_area"], "geografica": False,
        "prioridades": [{"area": area, "prioridade": prioridade} for area, prioridade in sorted(areas, key=lambda item: ordem_prioridade[item[1]])]}

@app.get("/gestor/indicadores/ocupacao")
async def gestor_ocupacao(localidade: Localidade = Depends(localidade_query), simulacao: Simulacao | None = Depends(simulacao_query)) -> Json:
    cenario = _cenario(localidade)
    if simulacao == "vazio":
        return {**_cabecalho(localidade), "indicador": None}
    vagas_total, vagas_ocupadas, _, ocupacao_pct = _totais_rede(cenario)
    serie: dict[str, Any] = cenario["serie_upa"]
    upa_destaque = next(unidade for unidade in cenario["unidades"] if unidade["nome"] == serie["nome"])
    qtd_observados = len(serie["observados"])
    pontos = [{"hora": (cenario["hora"] - 4 + indice) % 24, "ocupacao_pct": valor, "tipo": "observado" if indice < qtd_observados else "projetado"}
              for indice, valor in enumerate(serie["observados"] + serie["projetados"])]
    return {**_cabecalho(localidade), "indicador": {
        "codigo": "IND-OCUP", "ocupacao_pct": ocupacao_pct, "vagas_ocupadas": vagas_ocupadas, "vagas_total": vagas_total,
        "variacao": cenario["variacoes"]["ocupacao"], "unidade_variacao": "pp", "janela": "7d",
        "limiar_atencao": {"limiar_pct": LIMIAR_ATENCAO_PCT, "duracao_min": LIMIAR_DURACAO_MIN},
        "unidade_destaque": {campo: upa_destaque[campo] for campo in ("id", "nome", "ocupacao_pct", "vagas_ocupadas", "vagas_total")},
        "grafico": {"metrica": "ocupacao_pct", "observado_ate_hora": cenario["hora"], "limiar_pct": LIMIAR_ATENCAO_PCT, "pontos": pontos}},
        "alerta_destaque": _alerta_destaque(localidade)}

@app.get("/gestor/alertas")
async def gestor_alertas(localidade: Localidade = Depends(localidade_query), status: StatusAlerta = "ativo",
                         simulacao: Simulacao | None = Depends(simulacao_query)) -> Json:
    _cenario(localidade)
    alertas_do_territorio = [alerta for alerta in ALERTAS.values() if alerta["territorio"]["id"] == localidade["id"]]
    alertas_filtrados = [] if simulacao == "vazio" else [alerta for alerta in alertas_do_territorio if alerta["status"] == status]
    campos_resumo = ("id", "tipo", "gravidade", "unidade_id", "unidade", "previsao_hora", "nivel_confianca", "status")
    return {**_cabecalho(localidade), "filtro": status, "ativos": sum(1 for alerta in alertas_do_territorio if alerta["status"] == "ativo"),
            "alertas": [{campo: alerta[campo] for campo in campos_resumo} for alerta in alertas_filtrados]}

def _buscar_alerta(alerta_id: str, localidade: Localidade) -> Alerta:
    alerta_id = alerta_id.upper()
    if alerta_id not in ALERTAS:
        try:
            _cenario(localidade)  # o alerta pode pertencer à localidade informada, ainda não gerada
        except SemCobertura:
            pass
    if alerta_id not in ALERTAS:
        raise HTTPException(404, detail={"codigo": "alerta_nao_encontrado"})
    return ALERTAS[alerta_id]

@app.get("/gestor/alertas/{alerta_id}")
async def gestor_alerta(alerta_id: str, localidade: Localidade = Depends(localidade_query), simulacao: Simulacao | None = Depends(simulacao_query)) -> Alerta:
    return _buscar_alerta(alerta_id, localidade)

AcaoProposta = Literal["remanejar_equipe", "plano_contingencia", "consultar_unidade_vizinha", "reforcar_triagem", "apenas_monitorar"]

class AvaliacaoIn(BaseModel):
    unidade_id: str | None = None
    acao_proposta: AcaoProposta | None = None
    justificativa: str | None = None

JUSTIFICATIVA_MIN = 10

@app.post("/gestor/alertas/{alerta_id}/avaliacao")
async def gestor_avaliar_alerta(alerta_id: str, corpo: AvaliacaoIn, localidade: Localidade = Depends(localidade_query)) -> Alerta:
    """Decisão humana sobre o alerta (a equipe decide; nada é automático)."""
    alerta = _buscar_alerta(alerta_id, localidade)
    erros: list[Json] = []
    if corpo.unidade_id not in alerta["unidades_validas"]:
        erros.append({"campo": "unidade_id", "codigo": "obrigatorio"})
    if not corpo.acao_proposta:
        erros.append({"campo": "acao_proposta", "codigo": "obrigatorio"})
    if not corpo.justificativa or len(corpo.justificativa.strip()) < JUSTIFICATIVA_MIN:
        erros.append({"campo": "justificativa", "codigo": "tamanho_minimo", "minimo": JUSTIFICATIVA_MIN})
    if erros:
        raise _erro_validacao(erros)
    alerta["avaliacao"] = {**corpo.model_dump(), "registrada_em": _agora().isoformat(), "responsavel": "equipe_regulacao_territorial"}
    return alerta

@app.post("/gestor/alertas/{alerta_id}/resolver")
async def gestor_resolver_alerta(alerta_id: str, localidade: Localidade = Depends(localidade_query)) -> Alerta:
    alerta = _buscar_alerta(alerta_id, localidade)
    alerta["status"], alerta["auto"] = "resolvido", False
    return alerta

@app.get("/gestor/relatos")
async def gestor_relatos(localidade: Localidade = Depends(localidade_query), simulacao: Simulacao | None = Depends(simulacao_query)) -> Json:
    """Registros agregados da equipe. Vazio até alguém registrar um relato no lado do cidadão."""
    relatos_do_territorio = [] if simulacao == "vazio" else [relato for relato in RELATOS if relato["territorio"]["id"] == localidade["id"]]

    def alerta_relacionado(relato: Relato) -> str | None:
        return next((alerta["id"] for alerta in ALERTAS.values()
                     if alerta["unidade_id"] == relato["unidade_id"] and alerta["territorio"]["id"] == localidade["id"] and alerta["status"] == "ativo"), None)
    return {**_cabecalho(localidade), "relatos": [{**relato, "alerta_relacionado": alerta_relacionado(relato)} for relato in relatos_do_territorio]}

# ======================= OFFLINE / DEMO =======================
@app.get("/snapshot")
async def snapshot(localidade: Localidade = Depends(localidade_query), simulacao: Simulacao | None = Depends(simulacao_query)) -> Json:
    """Cópia completa da localidade pra salvar localmente (modo offline do app)."""
    return {"territorio": localidade, "copia_de": _agora().isoformat(),
            "cidadao": {"inicio": await cidadao_inicio(localidade), "unidades": await cidadao_unidades(localidade)},
            "gestor": {"rede": await gestor_rede(localidade), "capacidade": await gestor_capacidade(localidade),
                       "territorio": await gestor_territorio(localidade), "ocupacao": await gestor_ocupacao(localidade),
                       "alertas": await gestor_alertas(localidade)}}

@app.post("/demo/reset")
async def demo_reset() -> dict[str, str]:
    """Volta relatos, preferências e alertas ao estado inicial."""
    RELATOS.clear(); PROXIMO_NUMERO_RELATO[0] = 1042; PREFERENCIAS["texto_ampliado"] = False
    ALERTAS.clear(); ALERTA_POR_TERRITORIO.clear()
    return {"status": "ok"}
