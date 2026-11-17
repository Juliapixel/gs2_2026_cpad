# FluxoMed API

    pip install -r requirements.txt
    uvicorn api:app --reload --host 0.0.0.0

## Cobertura

Hoje só existe dado para **São Paulo (município) + 32 distritos/subprefeituras**. Padrão sem parâmetros: SP / Itaquera.
Toda rota aceita `?uf=&municipio=&distrito=` (texto livre). Fora da cobertura a resposta é **HTTP 200** com:

    {"status": "indisponivel", "codigo": "sem_cobertura | nivel_nao_disponivel | distrito_desconhecido | simulado",
     "titulo": "...", "mensagem": "...", "locais_cobertos": [...], "alternativas": [...], "orientacao": "...SAMU 192"}

Nos POSTs, fora da cobertura: HTTP 422 com o mesmo corpo dentro de `detail`.
Cliente: se `status == "indisponivel"`, mostrar a tela "ainda sem dados". Dentro da cobertura os dados saem sem esse campo.
Para ampliar: adicionar uma linha em `COBERTURA` no `main.py`.

## Outros

- Dados gerados com seed fixa (mesma localidade = mesma resposta). Nomes de unidades são fictícios.
- **Tempo real por padrão:** a hora segue o relógio (America/Sao_Paulo). Os números evoluem ao longo do dia (picos ~10h e ~19h nas UPAs), renovam a cada 10 min, UBS/USF fecham das 19h às 07h, e os alertas surgem, se atualizam e se resolvem sozinhos conforme a ocupação. Respostas trazem `rotulo_atualizacao` ("atualizado em tempo real · 10h30") e `modo_tempo`.
- Para congelar em 11/nov/2026 10h30 (desenvolvimento, prints): `FLUXOMED_FROZEN=1 uvicorn main:app`.
- Estados de tela em qualquer GET: `?delay_ms=2000`, `?simular=erro|vazio|timeout|offline|indisponivel`.
- `/cobertura`, `/localidades/ufs`, `/localidades/sugestoes?q=&apenas_disponiveis=true`, `/brasil/ufs` (SP "parcial", demais "sem_cobertura").
- `GET /snapshot?...` = cópia completa pra uso offline. `POST /demo/reset` zera relatos, preferências e alertas.

## Rotas

`/docs`: Visualizador OpenAPI

Cidadão: `/cidadao/inicio`, `/cidadao/unidades[/{id}]`, `/cidadao/relatos` (GET/POST), `/cidadao/relatos/opcoes`, `/cidadao/relatos/{OC}`, `/cidadao/preferencias`
Gestor: `/gestor/rede`, `/gestor/capacidade`, `/gestor/territorio`, `/gestor/indicadores/ocupacao`, `/gestor/alertas[/{ALT}]`, `POST /gestor/alertas/{ALT}/avaliacao`, `/gestor/relatos`
