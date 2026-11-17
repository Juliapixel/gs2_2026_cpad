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

Rodar:  pip install -r requirements.txt && uvicorn api:app --reload     Docs: /docs
"""
import asyncio
import math
import os
import random
import re
import unicodedata
import zlib
from datetime import datetime
from functools import lru_cache
from typing import Literal, Optional
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="FluxoMed - API (dados simulados)", version="4.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], expose_headers=["X-Dados"])

@app.middleware("http")
async def marca_simulado(request, call_next):
    resp = await call_next(request)
    resp.headers["X-Dados"] = "simulados"
    return resp

TZ = ZoneInfo("America/Sao_Paulo")
SNAP = datetime(2026, 11, 11, 10, 30, tzinfo=TZ)
FROZEN = os.getenv("FLUXOMED_FROZEN") == "1"
LIVE = not FROZEN
DEMO_KEY = "SP/sao-paulo/itaquera"  # localidade padrão: sempre tem um alerta ativo pra demonstrar o fluxo
AVISO = "Dados simulados. Nenhuma conduta clínica é automatizada. FluxoMed é um conceito independente inspirado no SUS."
DEFAULT = ("SP", "São Paulo", "Itaquera")

UFS = {  # sigla: (nome, região, capital)
    "AC": ("Acre", "Norte", "Rio Branco"), "AL": ("Alagoas", "Nordeste", "Maceió"), "AP": ("Amapá", "Norte", "Macapá"),
    "AM": ("Amazonas", "Norte", "Manaus"), "BA": ("Bahia", "Nordeste", "Salvador"), "CE": ("Ceará", "Nordeste", "Fortaleza"),
    "DF": ("Distrito Federal", "Centro-Oeste", "Brasília"), "ES": ("Espírito Santo", "Sudeste", "Vitória"),
    "GO": ("Goiás", "Centro-Oeste", "Goiânia"), "MA": ("Maranhão", "Nordeste", "São Luís"), "MT": ("Mato Grosso", "Centro-Oeste", "Cuiabá"),
    "MS": ("Mato Grosso do Sul", "Centro-Oeste", "Campo Grande"), "MG": ("Minas Gerais", "Sudeste", "Belo Horizonte"),
    "PA": ("Pará", "Norte", "Belém"), "PB": ("Paraíba", "Nordeste", "João Pessoa"), "PR": ("Paraná", "Sul", "Curitiba"),
    "PE": ("Pernambuco", "Nordeste", "Recife"), "PI": ("Piauí", "Nordeste", "Teresina"), "RJ": ("Rio de Janeiro", "Sudeste", "Rio de Janeiro"),
    "RN": ("Rio Grande do Norte", "Nordeste", "Natal"), "RS": ("Rio Grande do Sul", "Sul", "Porto Alegre"),
    "RO": ("Rondônia", "Norte", "Porto Velho"), "RR": ("Roraima", "Norte", "Boa Vista"), "SC": ("Santa Catarina", "Sul", "Florianópolis"),
    "SP": ("São Paulo", "Sudeste", "São Paulo"), "SE": ("Sergipe", "Nordeste", "Aracaju"), "TO": ("Tocantins", "Norte", "Palmas"),
}
SP_DISTRITOS = [  # subprefeituras de São Paulo (nomes reais, usados só pra sugestões/grafia correta)
    "Aricanduva/Vila Formosa", "Butantã", "Campo Limpo", "Capela do Socorro", "Casa Verde/Cachoeirinha", "Cidade Ademar", "Cidade Tiradentes",
    "Ermelino Matarazzo", "Freguesia/Brasilândia", "Guaianases", "Ipiranga", "Itaim Paulista", "Itaquera", "Jabaquara", "Jaçanã/Tremembé",
    "Lapa", "M'Boi Mirim", "Mooca", "Parelheiros", "Penha", "Perus", "Pinheiros", "Pirituba/Jaraguá", "Santana/Tucuruvi", "Santo Amaro",
    "São Mateus", "São Miguel Paulista", "Sapopemba", "Vila Prudente", "Sé", "Vila Maria/Vila Guilherme", "Vila Mariana"]
# Nomes de unidades e microáreas são FICTÍCIOS (evita atribuir dado simulado a lugares reais).
BAIRROS = ["Alto do Céu", "Nova Aurora", "Vila Esperança", "Beira Rio", "Campo Verde", "Morro do Sol", "Santa Clara", "Jardim Primavera",
           "Água Fria", "Bela Vista", "Planalto", "Cajueiro Novo", "Rio Doce", "Mangueira", "Poço Novo", "Rosa Branca", "São José", "Vila Nova"]
REGIOES = ["Região Norte", "Região Sul", "Região Leste", "Região Oeste", "Região Central", "Periferia"]

def _rng(*k):
    return random.Random("|".join(map(str, k)))

def _slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

CURADOS = {_slug(n): n for n in [v[2] for v in UFS.values()] + SP_DISTRITOS}

def _canon(s):
    s = " ".join(s.split())
    return CURADOS.get(_slug(s)) or (s.title() if s.islower() else s)

def _seta(v):
    return "↑" if v > 0 else "↓" if v < 0 else "→"

def _rot(v, un, janela):
    return " ".join(f"{_seta(v)}{abs(v)} {un} {janela}".split())

def _kpi(valor, var=None, rot=None, **extra):
    d = {"valor": valor}
    if var is not None:
        d.update(variacao=var, rotulo_variacao=rot)
    d.update(extra)
    return d

def _nivel_conf(c):
    return "alta" if c >= 0.8 else "moderada" if c >= 0.6 else "baixa"

def _agora():
    if not LIVE:
        return SNAP
    n = datetime.now(TZ)
    return n.replace(minute=n.minute // 10 * 10, second=0, microsecond=0)

# ======================= LOCALIDADE =======================
def _resolve(uf, municipio, distrito, checar=True):
    if not (uf or municipio or distrito):
        uf, municipio, distrito = DEFAULT
    if not uf:
        raise HTTPException(422, "Informe a UF (ex.: uf=PE).")
    uf = uf.strip().upper()
    if uf not in UFS:
        raise HTTPException(404, f"UF '{uf}' inválida. Use a sigla (ex.: SP, PE, AM).")
    mun = _canon(municipio) if municipio and municipio.strip() else None
    dis = _canon(distrito) if distrito and distrito.strip() else None
    if dis and not mun:
        raise HTTPException(422, "Para informar o distrito, informe também o município.")
    nivel = "distrito" if dis else "municipio" if mun else "uf"
    key = "/".join(p for p in [uf, _slug(mun) if mun else "", _slug(dis) if dis else ""] if p)
    Ld = {"id": key, "nivel": nivel, "uf": uf, "uf_nome": UFS[uf][0], "regiao": UFS[uf][1], "municipio": mun, "distrito": dis,
            "nome": dis or mun or UFS[uf][0], "nome_exibicao": ", ".join(p for p in [dis, mun, uf] if p)}
    if checar:
        _checar_cobertura(Ld)
    return Ld

async def simulacao(delay_ms: int = Query(0, ge=0, le=10_000, description="Atraso artificial (loading)"),
                    simular: Optional[Literal["erro", "vazio", "timeout", "offline", "indisponivel"]] = Query(None)):
    if simular == "timeout":
        await asyncio.sleep(15)
    if delay_ms:
        await asyncio.sleep(delay_ms / 1000)
    if simular == "erro":
        raise HTTPException(500, "Erro simulado")
    if simular == "offline":
        raise HTTPException(503, detail={"codigo": "sem_conexao", "mensagem": "A conexão falhou. As informações podem estar desatualizadas.",
                                         "copia_disponivel": True, "copia_de": _agora().isoformat()})
    return simular

async def loc(uf: Optional[str] = Query(None, description="Sigla da UF. Sem nenhum parâmetro de local = São Paulo / Itaquera"),
               municipio: Optional[str] = Query(None, description="Município (hoje com dados: São Paulo)"),
               distrito: Optional[str] = Query(None, description="Distrito/subprefeitura (ex.: Itaquera)"),
               sim=Depends(simulacao)):
    L = _resolve(uf, municipio, distrito)
    if sim == "indisponivel":
        raise SemCobertura(L, "simulado")
    return L


# ======================= COBERTURA =======================
# Só estas localidades têm dados. Para ampliar: adicione uma linha ("UF/slug-do-municipio": {...}).
COBERTURA = {"SP/sao-paulo": {"uf": "SP", "municipio": "São Paulo", "distritos": SP_DISTRITOS}}

class SemCobertura(Exception):
    def __init__(self, L, codigo, alternativas=None):
        self.L, self.codigo, self.alternativas = L, codigo, alternativas or []

def _cobertos():
    return [{"uf": c["uf"], "municipio": c["municipio"], "nivel": "município e distritos", "distritos": len(c["distritos"])} for c in COBERTURA.values()]

def _checar_cobertura(L):
    uf = L["uf"]
    if L["nivel"] == "uf":
        mun = [c["municipio"] for c in COBERTURA.values() if c["uf"] == uf]
        raise SemCobertura(L, "nivel_nao_disponivel" if mun else "sem_cobertura",
                           [{"tipo": "municipio", "uf": uf, "municipio": m, "nome": m} for m in mun])
    ck = f"{uf}/{_slug(L['municipio'])}"
    cov = COBERTURA.get(ck)
    if not cov:
        raise SemCobertura(L, "sem_cobertura")
    if L["nivel"] == "distrito" and cov["distritos"]:
        qs, lista = _slug(L["distrito"]), cov["distritos"]
        exato = [d for d in lista if _slug(d) == qs]
        parcial = [d for d in lista if qs and qs in _slug(d)]
        achou = exato or (parcial if len(parcial) == 1 else [])
        if not achou:
            alt = (parcial or lista)[:8]
            raise SemCobertura(L, "distrito_desconhecido", [{"tipo": "distrito", "uf": uf, "municipio": cov["municipio"], "distrito": d,
                                                            "nome": f"{d}, {cov['municipio']}"} for d in alt])
        d = achou[0]
        L.update(distrito=d, nome=d, nome_exibicao=f"{d}, {cov['municipio']}, {uf}", id=f"{ck}/{_slug(d)}")

TEXTOS = {
    "sem_cobertura": ("Ainda sem dados para esta localidade", "O FluxoMed ainda não tem cobertura em {n}. Por enquanto, os dados simulados cobrem: {c}."),
    "nivel_nao_disponivel": ("Informe o município", "Em {n}, os dados existem apenas no nível de município (cobertura atual: {c}). Escolha um município."),
    "distrito_desconhecido": ("Distrito não encontrado", "Não reconhecemos esse distrito. Veja as sugestões de {n}."),
    "simulado": ("Dados indisponíveis no momento", "Estado de teste: indisponibilidade simulada para {n}."),
}

def _envelope(exc):
    t, m = TEXTOS[exc.codigo]; L = exc.L
    cob = ", ".join(f"{c['municipio']}/{c['uf']}" for c in COBERTURA.values())
    return {"status": "indisponivel", "codigo": exc.codigo, "titulo": t,
            "mensagem": m.format(n=L["nome_exibicao"] if exc.codigo != "nivel_nao_disponivel" else L["uf_nome"], c=cob),
            "territorio": L, "locais_cobertos": _cobertos(), "alternativas": exc.alternativas,
            "orientacao": "Em urgência, procure atendimento. Em risco imediato, ligue SAMU 192.", "aviso": AVISO}

@app.exception_handler(SemCobertura)
async def _sem_cobertura(request: Request, exc: SemCobertura):
    corpo = _envelope(exc)
    return JSONResponse(corpo, status_code=200) if request.method == "GET" else JSONResponse({"detail": corpo}, status_code=422)

# ======================= GERADOR DE CENÁRIO =======================
def _unit(nome, tipo, total, occ, espera):
    return {"id": _slug(nome), "nome": nome, "tipo": tipo, "vagas_total": total, "vagas_ocupadas": occ, "espera_min": espera}

def _diurno(tipo, h):  # perfil de demanda ao longo do dia (relativo)
    g = lambda c, w: math.exp(-(((h - c) / w) ** 2))
    return 0.82 + 0.33 * g(10, 2.5) + 0.28 * g(19, 2.5) if tipo == "UPA" else 0.85 + 0.3 * g(9, 2.2) + 0.15 * g(14, 2)

def _demo_ratio(h):  # UPA da localidade padrão: sempre >85%, com curva ao longo do dia (alerta sempre disponível pra demonstrar)
    norm = min(1.0, max(0.0, (_diurno("UPA", h % 24) - 0.82) / (_diurno("UPA", 10) - 0.82)))
    return 0.86 + 0.12 * norm

def _gerar(key, nivel, h, tb):
    r, rt = _rng("terr", key), _rng("tempo", key, tb)
    n = {"distrito": r.randint(10, 18), "municipio": r.randint(20, 36), "uf": r.randint(30, 48)}[nivel]
    esc = {"distrito": 1, "municipio": 1.6, "uf": 2.2}[nivel]
    nupa = max(1, round(n / 9))
    pressao = key == DEMO_KEY or r.random() < 0.65
    pref = r.sample(BAIRROS, len(BAIRROS))
    units = []
    for i in range(n):
        tipo = "UPA" if i < nupa else r.choice(["UBS", "USF"])
        nome = f"{tipo} {pref[i % len(pref)]}" + (f" {i // len(pref) + 1}" if i >= len(pref) else "")
        total = round((r.randint(40, 60) if tipo == "UPA" else r.randint(5, 45)) * esc)
        if tipo == "UPA":
            base = r.uniform(0.88, 0.97) if (pressao and i == 0) else r.uniform(0.6, 0.97 if pressao else 0.84)
        else:
            base = r.uniform(0.5, 0.82)
        ratio = base * _diurno(tipo, h) / _diurno(tipo, 10) + rt.uniform(-0.02, 0.02)
        if key == DEMO_KEY and i == 0:
            ratio = _demo_ratio(h) + rt.uniform(0, 0.015)
        ratio = min(0.99, max(0.05, ratio))
        aberta = tipo == "UPA" or 7 <= h < 19
        espera = (round(18 + ratio * 60 + rt.uniform(-5, 5)) if tipo == "UPA" else round(8 + ratio * 30)) if aberta else None
        u = _unit(nome, tipo, total, round(total * ratio) if aberta else 0, espera)
        u["aberta"], u["_base"] = aberta, base
        units.append(u)
    abertos = [u for u in units if u["aberta"]]
    areas = [(b, r.choice(["alta", "moderada", "moderada", "baixa"])) for b in r.sample(BAIRROS, 6)] if nivel == "distrito" \
        else [(g, r.choice(["alta", "moderada", "moderada", "baixa"])) for g in REGIOES]
    top = max((u for u in units if u["tipo"] == "UPA"), key=lambda u: u["vagas_ocupadas"] / u["vagas_total"])
    atual = round(100 * top["vagas_ocupadas"] / top["vagas_total"])
    demo_top = key == DEMO_KEY and top is units[0]

    def pct(hh):
        v = _demo_ratio(hh % 24) if demo_top else top["_base"] * _diurno("UPA", hh % 24) / _diurno("UPA", 10)
        return round(100 * min(0.99, max(0.05, v)))
    obs, proj = [pct(h - 4 + k) for k in range(4)] + [atual], [pct(h + k) for k in range(1, 5)]
    return {"unidades": units, "areas": areas, "nivel_area": "microárea" if nivel == "distrito" else "região", "h": h,
            "equipes": round(n * r.uniform(1.8, 2.4)), "clima_max": r.randint(27, 36), "cobertura": r.randint(68, 93),
            "visitas": round(r.randint(28, 70) * esc), "rede_espera": round(sum(u["espera_min"] for u in abertos) / len(abertos)),
            "espera_evitada_h": round(r.randint(60, 260) * esc), "plano_ativo": 0,
            "var": {"ocup": r.randint(-8, 8), "espera": r.randint(-14, 14), "vagas": r.randint(-10, 20), "equipes": r.randint(0, 5),
                    "clima": r.randint(-2, 4), "cobertura": r.randint(-2, 3), "visitas": r.randint(-6, 12), "evitada_pct": r.randint(5, 25)},
            "serie_upa": {"nome": top["nome"], "obs": obs, "proj": proj}, "conf": round(r.uniform(0.55, 0.88), 2)}

ALERTAS: dict[str, dict] = {}
ALERTA_DO_TERR: dict[str, str] = {}

def _montar_alerta(L, s, u, aid):
    proj = s["serie_upa"]["proj"][-1] if s["serie_upa"]["nome"] == u["nome"] else min(99, u["ocupacao_pct"] + 3)
    return {
        "id": aid, "territorio": L, "unidade_id": u["id"], "unidade": u["nome"], "gravidade": "atencao",
        "titulo": f"Risco de superlotação na {u['nome']}", "gerado_em": _agora().isoformat(), "atualizado_em": _agora().isoformat(),
        "previsao_para": f"{(s['h'] + 4) % 24}h",
        "projecao": {"valor_pct": proj, "faixa_min_pct": max(0, proj - 6), "faixa_max_pct": min(100, proj + 4),
                     "ocupacao_atual_pct": u["ocupacao_pct"], "horizonte_h": 4},
        "regra": {"limiar_pct": 85, "duracao_min": 30},
        "por_que_apareceu": [
            {"ordem": "01", "titulo": "Ocupação acima do limite", "detalhe": f"{u['ocupacao_pct']}% observados; regra acima de 85% por 30 minutos."},
            {"ordem": "02", "titulo": "Entradas maiores que saídas", "detalhe": "Chegadas superam altas nas últimas horas (simulado)."},
            {"ordem": "03", "titulo": "Padrão histórico do horário", "detalhe": "Esse dia e horário costumam concentrar pico (simulado)."}],
        "confianca": s["conf"], "nivel_confianca": _nivel_conf(s["conf"]),
        "limitacoes": ["Cenário demonstrativo. Não usar para decisões clínicas.", "Projeção de curto prazo baseada em padrão histórico simulado",
                       "Não considera eventos extraordinários (acidentes, surtos)"],
        "exemplo_avaliacao": "Conferir escala e fila. Consultar unidade vizinha sobre capacidade adicional antes de qualquer remanejamento.",
        "unidades_validas": [x["id"] for x in s["unidades"]], "status": "ativo", "avaliacao": None, "auto": False, "avisos": [AVISO]}

def _registrar_alerta(L, s):
    """Alerta surge quando uma UPA passa de 85%, é atualizado enquanto durar e se resolve sozinho quando a ocupação cai."""
    upas = [u for u in s["unidades"] if u["tipo"] == "UPA" and u["ocupacao_pct"] > 85]
    aid = ALERTA_DO_TERR.get(L["id"])
    if aid is None:
        if not upas:
            return
        n = 100 + zlib.crc32(L["id"].encode()) % 900
        while f"ALT-{n}" in ALERTAS:
            n = 100 + (n - 99) % 900
        aid = f"ALT-{n}"
        ALERTAS[aid] = _montar_alerta(L, s, max(upas, key=lambda x: x["ocupacao_pct"]), aid)
        ALERTA_DO_TERR[L["id"]] = aid
        return
    a = ALERTAS[aid]
    if upas:
        if a["status"] == "resolvido" and a.get("auto"):
            a["status"] = "ativo"
        if a["status"] == "ativo":
            novo = _montar_alerta(L, s, max(upas, key=lambda x: x["ocupacao_pct"]), aid)
            novo.update(gerado_em=a["gerado_em"], avaliacao=a["avaliacao"], auto=a["auto"])
            ALERTAS[aid] = novo
    elif a["status"] == "ativo":
        a["status"], a["auto"] = "resolvido", True

@lru_cache(maxsize=512)
def _spec(key, nivel, tb):
    s = _gerar(key, nivel, _agora().hour, tb)
    for u in s["unidades"]:
        u["ocupacao_pct"] = round(100 * u["vagas_ocupadas"] / u["vagas_total"])
        u["vagas_livres"] = u["vagas_total"] - u["vagas_ocupadas"] if u["aberta"] else 0
        u["nivel"] = "fechada" if not u["aberta"] else "atencao" if u["ocupacao_pct"] > 85 else "estavel"
        u["etiqueta"] = {"fechada": "Fechada", "atencao": "Atenção", "estavel": "Estável"}[u["nivel"]]
    s["em_atencao"] = sum(1 for u in s["unidades"] if u["nivel"] == "atencao")
    s["plano_ativo"] = min(s["em_atencao"], _rng("plano", key).randint(0, 2))
    return s

def _S(L):
    s = _spec(L["id"], L["nivel"], _agora().isoformat() if LIVE else "fixo")
    _registrar_alerta(L, s)
    return s

def _tot(s):
    ab = [u for u in s["unidades"] if u["aberta"]]
    tv = sum(u["vagas_total"] for u in ab); oc = sum(u["vagas_ocupadas"] for u in ab)
    return tv, oc, tv - oc, round(100 * oc / tv)

def _cab(L):
    a = _agora()
    rot = f"atualizado em tempo real · {a.hour}h{a.minute:02d}" if LIVE else f"cópia fixa de {a.hour}h{a.minute:02d}"
    return {"territorio": L, "atualizado_em": a.isoformat(), "rotulo_atualizacao": rot, "modo_tempo": "tempo_real" if LIVE else "congelado", "aviso": AVISO}

def _destaque(L):
    a = ALERTAS.get(ALERTA_DO_TERR.get(L["id"], ""))
    if not a or a["status"] != "ativo":
        return None
    return {"id": a["id"], "gravidade": a["gravidade"], "previsao_para": a["previsao_para"], "titulo": a["titulo"],
            "nivel_confianca": a["nivel_confianca"], "rotulo": f"Atenção · previsão para {a['previsao_para']}"}

RELATOS: list[dict] = []
PREFS = {"texto_ampliado": False}
PROX_OC = [1042]

# ======================= LOCALIDADES / BRASIL =======================
@app.get("/")
async def raiz():
    return {"api": "FluxoMed mock", "dados": "100% simulados", "docs": "/docs", "referencia": _agora().isoformat(),
            "localidade_padrao": "SP / São Paulo / Itaquera", "cobertura": _cobertos(),
            "como_usar": "Rotas aceitam ?uf=&municipio=&distrito=. Fora da cobertura: 200 com status 'indisponivel'."}

@app.get("/cobertura")
async def cobertura_endpoint(sim=Depends(simulacao)):
    """Onde existem dados hoje + como ampliar."""
    return {"locais_cobertos": [] if sim == "vazio" else _cobertos(), "demais_localidades": "indisponivel",
            "como_ampliar": "Adicionar uma linha em COBERTURA no main.py (município e, opcionalmente, lista de distritos)."}

@app.get("/localidades/ufs")
async def ufs(sim=Depends(simulacao)):
    if sim == "vazio":
        return []
    return [{"uf": k, "nome": v[0], "regiao": v[1], "capital": v[2],
             "cobertura": "parcial" if any(c["uf"] == k for c in COBERTURA.values()) else "sem_cobertura"} for k, v in UFS.items()]

@app.get("/localidades/sugestoes")
async def sugestoes(q: str = Query("", description="Busca por UF, capital ou distrito"), apenas_disponiveis: bool = False, sim=Depends(simulacao)):
    """Atalhos pro seletor do app. Qualquer texto é aceito nas rotas, mas só o que está em COBERTURA tem dados."""
    if sim == "vazio":
        return []
    cobertos = {k for k in COBERTURA}
    out = [{"tipo": "uf", "uf": k, "nome": v[0], "disponivel": False} for k, v in UFS.items()]
    out += [{"tipo": "municipio", "uf": k, "municipio": v[2], "nome": v[2], "disponivel": f"{k}/{_slug(v[2])}" in cobertos} for k, v in UFS.items()]
    out += [{"tipo": "distrito", "uf": "SP", "municipio": "São Paulo", "distrito": d, "nome": f"{d}, São Paulo", "disponivel": True} for d in SP_DISTRITOS]
    qs = _slug(q)
    return [x for x in out if qs in _slug(x["nome"] + " " + x["uf"]) and (x["disponivel"] or not apenas_disponiveis)][:60]

@app.get("/localidade")
async def localidade(L=Depends(loc), sim=Depends(simulacao)):
    """Confere se a localidade tem dados. Fora da cobertura devolve status 'indisponivel'."""
    s = _S(L)
    return {"status": "disponivel", **L, "unidades": len(s["unidades"]), "em_atencao": s["em_atencao"], "alerta_ativo": _destaque(L) is not None}

@app.get("/brasil/ufs")
async def brasil_ufs(regiao: Optional[str] = None, sim=Depends(simulacao)):
    """Visão nacional: UFs com dados (parcial) e UFs sem cobertura."""
    if sim == "vazio":
        return []
    com, sem = [], []
    for uf, v in UFS.items():
        if regiao and v[1].lower() != regiao.lower():
            continue
        cob = [c for c in COBERTURA.values() if c["uf"] == uf]
        if not cob:
            sem.append({"uf": uf, "nome": v[0], "regiao": v[1], "status": "sem_cobertura", "mensagem": "Ainda sem dados para esta UF."})
            continue
        c = cob[0]; L = _resolve(uf, c["municipio"], None); s = _S(L); tv, oc, livres, pct = _tot(s)
        com.append({"uf": uf, "nome": v[0], "regiao": v[1], "status": "parcial", "escopo": f"{c['municipio']} (município)",
                    "ocupacao_rede_pct": pct, "espera_media_min": s["rede_espera"], "unidades_em_atencao": s["em_atencao"],
                    "total_unidades": len(s["unidades"]), "alerta_ativo": _destaque(L) is not None})
    return sorted(com, key=lambda x: -x["ocupacao_rede_pct"]) + sem

# ======================= CIDADÃO =======================
def _unit_pub(u):
    return {k: u[k] for k in ("id", "nome", "tipo", "aberta", "ocupacao_pct", "vagas_livres", "vagas_total", "espera_min", "etiqueta", "nivel")} | {
        "atendimento": "Atendimento de urgência · 24h" if u["tipo"] == "UPA" else "Atenção básica · consulte a equipe local"}

@app.get("/cidadao/inicio")
async def cid_inicio(L=Depends(loc), sim=Depends(simulacao)):
    s = _S(L); top = max(s["unidades"], key=lambda u: u["ocupacao_pct"]); alta = top["nivel"] == "atencao"
    return {**_cab(L), "destaque": {"tipo": "alta_procura" if alta else "estavel", "unidade_id": top["id"],
            "titulo": f"Alta procura na {top['nome']}" if alta else "Rede com situação estável",
            "texto": (f"Espera média de {top['espera_min']} min. Esse tempo é estimado, não uma posição na fila. O atendimento segue avaliação clínica."
                      if alta else "Nenhuma unidade acima do limite de atenção no momento."), "unidade": _unit_pub(top)}}

@app.get("/cidadao/unidades")
async def cid_unidades(L=Depends(loc), tipo: Optional[Literal["UPA", "UBS", "USF"]] = None, sim=Depends(simulacao)):
    s = _S(L)
    if sim == "vazio":
        return {**_cab(L), "aviso_lista": "Compare informações, não prioridades.", "unidades": []}
    us = sorted([u for u in s["unidades"] if not tipo or u["tipo"] == tipo], key=lambda u: -u["ocupacao_pct"])
    return {**_cab(L), "aviso_lista": "A espera média varia e não garante atendimento imediato. Procure sua unidade de referência para cuidados de rotina.",
            "unidades": [_unit_pub(u) for u in us]}

@app.get("/cidadao/unidades/{uid}")
async def cid_unidade(uid: str, L=Depends(loc), sim=Depends(simulacao)):
    u = next((u for u in _S(L)["unidades"] if u["id"] == uid), None)
    if not u:
        raise HTTPException(404, "Unidade não encontrada neste território")
    return {**_cab(L), **_unit_pub(u), "titulo_status": {"atencao": "Atenção · alta procura", "estavel": "Situação estável", "fechada": "Fechada no momento"}[u["nivel"]],
            "resumo": f"{u['espera_min']} min de espera média" if u["aberta"] else "Unidade fechada no momento",
            "detalhe": f"{u['ocupacao_pct']}% de ocupação · {u['vagas_livres']} vagas disponíveis" if u["aberta"] else "O atendimento de rotina retorna às 07h",
            "nota": "Estimativa sujeita a mudanças. Não representa posição individual na fila.",
            "localizacao": f"{L['nome_exibicao']}. Endereço e contatos não foram incluídos neste cenário demonstrativo.",
            "aviso_disponibilidade": "A disponibilidade depende da avaliação da equipe. Não há reserva ou transferência automática."}

TIPOS_RELATO = {"espera_prolongada": "Espera prolongada", "falta_de_insumos": "Falta de insumos", "estrutura": "Problema de estrutura",
                "atendimento": "Atendimento", "outro": "Outro"}

@app.get("/cidadao/relatos/opcoes")
async def opcoes_relato(L=Depends(loc), sim=Depends(simulacao)):
    s = _S(L)
    return {"unidades": [{"id": u["id"], "nome": u["nome"]} for u in s["unidades"]], "areas": [a[0] for a in s["areas"]],
            "rotulo_area": s["nivel_area"], "tipos": [{"id": k, "nome": v} for k, v in TIPOS_RELATO.items()],
            "quando": ["agora", "hoje", "ontem", "esta_semana"]}

class RelatoIn(BaseModel):
    uf: Optional[str] = None
    municipio: Optional[str] = None
    distrito: Optional[str] = None
    unidade_id: Optional[str] = None
    tipo_ocorrencia: Optional[str] = None
    area: Optional[str] = None
    quando: Optional[str] = None
    descricao: Optional[str] = None
    consentimento_uso_agregado: Optional[bool] = None

@app.post("/cidadao/relatos", status_code=201)
async def criar_relato(b: RelatoIn):
    """Relato anônimo (sem CPF, nome ou contato). Localidade no corpo: uf/municipio/distrito."""
    L = _resolve(b.uf, b.municipio, b.distrito); s = _S(L); erros = []
    u = next((u for u in s["unidades"] if u["id"] == b.unidade_id), None)
    if not u:
        erros.append({"campo": "unidade_id", "mensagem": "Selecione a unidade de saúde."})
    if b.tipo_ocorrencia not in TIPOS_RELATO:
        erros.append({"campo": "tipo_ocorrencia", "mensagem": "Selecione o tipo de ocorrência."})
    if not b.quando:
        erros.append({"campo": "quando", "mensagem": "Informe quando aconteceu."})
    if not b.descricao or len(b.descricao.strip()) < 20:
        erros.append({"campo": "descricao", "mensagem": "Descreva o problema com pelo menos 20 caracteres."})
    if b.area and b.area not in [a[0] for a in s["areas"]]:
        erros.append({"campo": "area", "mensagem": "Área inválida para este território."})
    if erros:
        raise HTTPException(422, detail={"mensagem": f"Faltam {len(erros)} informações obrigatórias.", "campos": erros})
    if not b.consentimento_uso_agregado:
        raise HTTPException(422, detail={"mensagem": "Autorize o uso anônimo do relato para continuar.",
                                         "campos": [{"campo": "consentimento_uso_agregado", "mensagem": "Consentimento obrigatório."}]})
    oc = f"OC-{PROX_OC[0]}"; PROX_OC[0] += 1
    r = {"id": oc, "territorio": L, "unidade_id": u["id"], "unidade": u["nome"], "tipo_ocorrencia": b.tipo_ocorrencia,
         "tipo_rotulo": TIPOS_RELATO[b.tipo_ocorrencia], "area": b.area, "quando": b.quando, "descricao": b.descricao.strip(),
         "registrado_em": _agora().isoformat(), "status": "em_analise", "destino": "regulação territorial", "consentimento": "autorizado para uso agregado",
         "linha_do_tempo": [{"etapa": "registro_recebido", "feito": True}, {"etapa": "analise", "feito": True, "atual": True},
                            {"etapa": "encaminhamento", "feito": False}],
         "proximos_passos": ["A equipe analisa o relato.", "O registro ajuda a identificar gargalos.", "A intervenção depende da equipe responsável."],
         "aviso": "Não há prazo ou intervenção garantida. Em urgência, procure atendimento; em risco imediato, SAMU 192."}
    RELATOS.append(r)
    return r

@app.get("/cidadao/relatos")
async def meus_relatos(sim=Depends(simulacao)):
    """Começa vazio (estado 'você ainda não registrou um relato')."""
    return [] if sim == "vazio" else RELATOS

@app.get("/cidadao/relatos/{oc}")
async def relato(oc: str, sim=Depends(simulacao)):
    r = next((r for r in RELATOS if r["id"] == oc.upper()), None)
    if not r:
        raise HTTPException(404, "Relato não encontrado")
    return r

class PrefsIn(BaseModel):
    texto_ampliado: bool

@app.get("/cidadao/preferencias")
async def get_prefs(sim=Depends(simulacao)):
    return {**PREFS, "privacidade": "Dados agregados. Sem CPF, prontuário, nome ou contato. O relato do cidadão exige consentimento explícito."}

@app.put("/cidadao/preferencias")
async def put_prefs(b: PrefsIn):
    PREFS["texto_ampliado"] = b.texto_ampliado
    return PREFS

# ======================= GESTOR =======================
@app.get("/gestor/rede")
async def g_rede(L=Depends(loc), sim=Depends(simulacao)):
    s = _S(L)
    if sim == "vazio":
        return {**_cab(L), "kpis": None, "alerta_destaque": None}
    v = s["var"]; tv, oc, livres, pct = _tot(s)
    return {**_cab(L), "status_rede": "em monitoramento", "kpis": {
        "ocupacao_rede": _kpi(pct, v["ocup"], _rot(v["ocup"], "p.p.", "em 7 dias"), unidade="%"),
        "espera_media": _kpi(s["rede_espera"], v["espera"], _rot(v["espera"], "min", "em 7 dias"), unidade="min"),
        "em_atencao": {"valor": s["em_atencao"], "total": len(s["unidades"]), "rotulo": f"{s['em_atencao']} de {len(s['unidades'])}",
                       "detalhe": f"{s['plano_ativo']} com plano ativo"},
        "espera_evitada": _kpi(s["espera_evitada_h"], v["evitada_pct"], f"{_seta(v['evitada_pct'])}{abs(v['evitada_pct'])}% no mês", unidade="h",
                               nota="Estimativa simulada de horas de espera reduzidas por orientação do app.")},
        "alerta_destaque": _destaque(L)}

@app.get("/gestor/capacidade")
async def g_cap(L=Depends(loc), sim=Depends(simulacao)):
    s = _S(L)
    if sim == "vazio":
        return {**_cab(L), "kpis": None, "unidades": []}
    v = s["var"]; tv, oc, livres, pct = _tot(s)
    return {**_cab(L), "monitoramento": f"{len(s['unidades'])} unidades monitoradas · {sum(1 for u in s['unidades'] if u['aberta'])} abertas agora", "kpis": {
        "vagas_totais": _kpi(tv, v["vagas"], _rot(v["vagas"], "", "em 7 dias")),
        "vagas_livres": _kpi(livres, None, None, detalhe=f"{round(100 * livres / tv)}% da capacidade"),
        "espera_media": _kpi(s["rede_espera"], v["espera"], _rot(v["espera"], "min", "em 7 dias"), unidade="min"),
        "equipes": _kpi(s["equipes"], v["equipes"], _rot(v["equipes"], "", "nesta semana"))},
        "limiar_atencao_pct": 85,
        "unidades": [{"id": u["id"], "nome": u["nome"], "tipo": u["tipo"], "aberta": u["aberta"], "ocupacao_pct": u["ocupacao_pct"], "acima_do_limite": u["nivel"] == "atencao"}
                     for u in sorted(s["unidades"], key=lambda u: -u["ocupacao_pct"])],
        "alerta_destaque": _destaque(L)}

@app.get("/gestor/territorio")
async def g_terr(L=Depends(loc), sim=Depends(simulacao)):
    s = _S(L)
    if sim == "vazio":
        return {**_cab(L), "kpis": None, "prioridades": []}
    v = s["var"]; altas = sum(1 for a in s["areas"] if a[1] == "alta"); ordem = {"alta": 0, "moderada": 1, "baixa": 2}
    return {**_cab(L), "subtitulo": "Vulnerabilidade, clima e acesso à saúde.", "kpis": {
        "maxima_do_dia": _kpi(s["clima_max"], v["clima"], _rot(v["clima"], "°C", "em 7 dias"), unidade="°C"),
        "cobertura": _kpi(s["cobertura"], v["cobertura"], _rot(v["cobertura"], "p.p.", "no mês"), unidade="%"),
        "areas_prioritarias": {"valor": altas, "total": len(s["areas"]), "rotulo": f"{altas} de {len(s['areas'])}", "detalhe": "Critérios sociais"},
        "visitas_previstas": _kpi(s["visitas"], v["visitas"], _rot(v["visitas"], "", "na semana"))},
        "rotulo_area": s["nivel_area"],
        "prioridades": [{"area": a, "prioridade": p} for a, p in sorted(s["areas"], key=lambda x: ordem[x[1]])], "nota": "Matriz não geográfica."}

@app.get("/gestor/indicadores/ocupacao")
async def g_ocup(L=Depends(loc), sim=Depends(simulacao)):
    s = _S(L)
    if sim == "vazio":
        return {**_cab(L), "indicador": None}
    tv, oc, livres, pct = _tot(s); v = s["var"]["ocup"]; ser = s["serie_upa"]
    upa = next(u for u in s["unidades"] if u["nome"] == ser["nome"]); nobs = len(ser["obs"])
    pontos = [{"hora": f"{(s['h'] - 4 + i) % 24:02d}h", "ocupacao_pct": val, "tipo": "observado" if i < nobs else "projetado"} for i, val in enumerate(ser["obs"] + ser["proj"])]
    return {**_cab(L), "indicador": {"codigo": "IND-OCUP", "titulo": f"{pct}% da rede ocupada",
            "detalhe": f"{oc} de {tv} vagas · {'queda' if v < 0 else 'alta' if v > 0 else 'estável'} de {abs(v)} p.p. em 7 dias", "limiar_atencao": "85% por 30 minutos",
            "unidade_destaque": {"id": upa["id"], "nome": upa["nome"], "ocupacao_pct": upa["ocupacao_pct"],
                                 "texto": f"{upa['nome']}: {upa['ocupacao_pct']}% ({upa['vagas_ocupadas']} de {upa['vagas_total']} vagas)"},
            "grafico": {"titulo": f"{upa['nome']}: histórico e projeção", "eixo": "Ocupação (%)", "observado_ate": f"{s['h']:02d}h",
                        "limiar_pct": 85, "pontos": pontos}}, "alerta_destaque": _destaque(L)}

@app.get("/gestor/alertas")
async def g_alertas(L=Depends(loc), status: Literal["ativo", "resolvido"] = "ativo", sim=Depends(simulacao)):
    _S(L)
    mine = [a for a in ALERTAS.values() if a["territorio"]["id"] == L["id"]]
    lista = [] if sim == "vazio" else [a for a in mine if a["status"] == status]
    ativos = sum(1 for a in mine if a["status"] == "ativo")
    msg = None if lista else (f"Nenhum alerta resolvido neste período. Existe {ativos} alerta ativo em {L['nome']}." if status == "resolvido" and ativos
                              else f"Nenhum alerta {status} neste período.")
    return {**_cab(L), "filtro": status, "ativos": ativos, "mensagem_vazio": msg,
            "alertas": [{k: a[k] for k in ("id", "gravidade", "titulo", "previsao_para", "nivel_confianca", "status")} for a in lista]}

def _alerta(aid, L):
    aid = aid.upper()
    if aid not in ALERTAS:
        try:
            _S(L)  # o alerta pode pertencer à localidade informada, ainda não gerada
        except SemCobertura:
            pass
    if aid not in ALERTAS:
        raise HTTPException(404, "Alerta não encontrado. Informe uf/municipio/distrito do território do alerta.")
    return ALERTAS[aid]

@app.get("/gestor/alertas/{aid}")
async def g_alerta(aid: str, L=Depends(loc), sim=Depends(simulacao)):
    return _alerta(aid, L)

class AvaliacaoIn(BaseModel):
    unidade_id: Optional[str] = None
    acao_proposta: Optional[Literal["remanejar_equipe", "plano_contingencia", "consultar_unidade_vizinha", "reforcar_triagem", "apenas_monitorar"]] = None
    justificativa: Optional[str] = None

@app.post("/gestor/alertas/{aid}/avaliacao")
async def avaliar(aid: str, b: AvaliacaoIn, L=Depends(loc)):
    """Decisão humana sobre o alerta (a equipe decide; nada é automático)."""
    a = _alerta(aid, L); erros = []
    if b.unidade_id not in a["unidades_validas"]:
        erros.append({"campo": "unidade_id", "mensagem": "Selecione a unidade de saúde."})
    if not b.acao_proposta:
        erros.append({"campo": "acao_proposta", "mensagem": "Selecione a ação proposta."})
    if not b.justificativa or len(b.justificativa.strip()) < 10:
        erros.append({"campo": "justificativa", "mensagem": "Escreva uma justificativa (mínimo 10 caracteres)."})
    if erros:
        raise HTTPException(422, detail={"mensagem": f"Faltam {len(erros)} informações obrigatórias.", "campos": erros})
    a["avaliacao"] = {**b.model_dump(), "registrada_em": _agora().isoformat(), "responsavel": "equipe de regulação territorial (sem dados individuais)"}
    return {"mensagem": f"Avaliação registrada para {a['id']}. A equipe de regulação fará a análise.", "alerta": a}

@app.post("/gestor/alertas/{aid}/resolver")
async def resolver(aid: str, L=Depends(loc)):
    a = _alerta(aid, L); a["status"], a["auto"] = "resolvido", False
    return a

@app.get("/gestor/relatos")
async def g_relatos(L=Depends(loc), sim=Depends(simulacao)):
    """Registros agregados da equipe. Vazio até alguém registrar um relato no lado do cidadão."""
    rel = [] if sim == "vazio" else [r for r in RELATOS if r["territorio"]["id"] == L["id"]]
    return {**_cab(L), "relatos": [{**r, "alerta_relacionado": next((a["id"] for a in ALERTAS.values() if a["unidade_id"] == r["unidade_id"]
                                                                    and a["territorio"]["id"] == L["id"] and a["status"] == "ativo"), None)} for r in rel]}

# ======================= OFFLINE / DEMO =======================
@app.get("/snapshot")
async def snapshot(L=Depends(loc), sim=Depends(simulacao)):
    """Cópia completa da localidade pra salvar localmente (modo offline do app)."""
    return {"territorio": L, "copia_de": _agora().isoformat(), "cidadao": {"inicio": await cid_inicio(L), "unidades": await cid_unidades(L)},
            "gestor": {"rede": await g_rede(L), "capacidade": await g_cap(L), "territorio": await g_terr(L), "ocupacao": await g_ocup(L),
                       "alertas": await g_alertas(L)}}

@app.post("/demo/reset")
async def reset():
    """Volta relatos, preferências e alertas ao estado inicial."""
    RELATOS.clear(); PROX_OC[0] = 1042; PREFS["texto_ampliado"] = False
    ALERTAS.clear(); ALERTA_DO_TERR.clear()
    return {"status": "ok"}
