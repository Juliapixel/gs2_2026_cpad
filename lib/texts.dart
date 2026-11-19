/// The API only returns stable codes; they are translated to text here.
abstract final class Texts {
  static String translate(Map<String, String> table, String code) => table[code] ?? code;

  static const window = {
    "7d": "nos últimos 7 dias",
    "semana": "nesta semana",
    "mes": "neste mês",
  };

  static const reportTypes = {
    "espera_prolongada": "Espera prolongada",
    "falta_de_insumos": "Falta de insumos",
    "estrutura": "Estrutura",
    "atendimento": "Atendimento",
    "outro": "Outro",
  };

  static const reportWhen = {
    "agora": "Agora",
    "hoje": "Hoje",
    "ontem": "Ontem",
    "esta_semana": "Esta semana",
  };

  static const reportStatus = {"em_analise": "Em análise"};

  static const confidenceLevel = {"alta": "Alta", "moderada": "Moderada", "baixa": "Baixa"};

  static const priority = {"alta": "Alta", "moderada": "Moderada", "baixa": "Baixa"};

  static const alertType = {"risco_superlotacao": "Risco de superlotação"};

  static const severity = {"atencao": "Atenção", "critico": "Crítico"};

  static const reasons = {
    "ocupacao_acima_limite": "Ocupação acima do limiar",
    "entradas_maiores_que_saidas": "Entradas de pacientes maiores que as saídas",
    "padrao_historico_horario": "Padrão histórico de demanda para este horário",
  };

  static const limitations = {
    "cenario_demonstrativo": "Cenário demonstrativo, com dados simulados",
    "projecao_curto_prazo_historico_simulado": "Projeção de curto prazo baseada em histórico simulado",
    "nao_considera_eventos_extraordinarios": "Não considera eventos extraordinários (surtos, acidentes, feriados)",
  };

  static const noCoverage = {
    "sem_cobertura": "Esta localidade ainda não tem dados. Hoje há cobertura para o município de São Paulo e seus distritos.",
    "nivel_nao_disponivel": "Não há visão por UF. Informe um município com cobertura.",
    "distrito_desconhecido": "Distrito não encontrado. Confira a grafia nas configurações.",
    "simulado": "Indisponibilidade simulada pela API.",
  };

  static const areaLevel = {"microarea": "microárea", "regiao": "região"};

  static const humanDecisionNotice =
      "Os alertas apoiam, mas não substituem, a decisão humana. Nenhuma conduta é automatizada.";
}
