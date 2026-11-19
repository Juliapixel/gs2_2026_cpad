import 'package:cpad/components/async_view.dart';
import 'package:cpad/components/fluxo_container.dart';
import 'package:cpad/components/kpi_card.dart';
import 'package:cpad/components/notice_banner.dart';
import 'package:cpad/components/section_title.dart';
import 'package:cpad/components/status_badge.dart';
import 'package:cpad/components/status_card.dart';
import 'package:cpad/models/alert.dart';
import 'package:cpad/providers/dashboard.dart';
import 'package:cpad/texts.dart';
import 'package:flutter/material.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';

class AlertScreen extends ConsumerWidget {
  final String id;

  const AlertScreen({super.key, required this.id});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: Text("Alerta $id"), foregroundColor: Colors.white),
      body: SafeArea(
        child: AsyncView(
          value: ref.watch(alertProvider(id)),
          onRetry: () => ref.refresh(alertProvider(id).future),
          builder: (context, alert) => ListView(
            padding: const .all(16),
            children: [
              const NoticeBanner(
                Texts.humanDecisionNotice,
                kind: .warning,
                icon: Icons.gavel,
              ),
              const SizedBox(height: 8),
              Row(
                spacing: 8,
                children: [
                  StatusBadge(
                    Texts.translate(Texts.severity, alert.severity),
                    .warning,
                  ),
                  StatusBadge(
                    alert.status == "ativo" ? "Ativo" : "Resolvido",
                    alert.status == "ativo" ? .critical : .ok,
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                Texts.translate(Texts.alertType, alert.type),
                style: theme.textTheme.headlineSmall?.copyWith(
                  fontWeight: .bold,
                ),
              ),
              Text(
                "${alert.unitName} · ${alert.territory.label}",
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.hintColor,
                ),
              ),
              const SectionTitle("Projeção"),
              KpiGrid(
                children: [
                  StatusCard(
                    "Ocupação agora",
                    "${alert.projection.currentOccupancyPct}%",
                    null,
                  ),
                  StatusCard(
                    "Previsto para as ${alert.forecastHour}h",
                    "${alert.projection.valuePct}%",
                    StatusText(
                      "faixa de ${alert.projection.minPct}% a ${alert.projection.maxPct}%",
                    ),
                  ),
                ],
              ),
              const SectionTitle("Por que este alerta apareceu (evidências)"),
              FluxoContainer(
                child: Column(
                  crossAxisAlignment: .start,
                  spacing: 8,
                  children: [
                    for (final reason in alert.reasons)
                      _Item(
                        Icons.check_circle_outline,
                        _describeReason(reason),
                      ),
                  ],
                ),
              ),
              const SectionTitle("Nível de confiança"),
              FluxoContainer(
                child: Row(
                  spacing: 12,
                  children: [
                    StatusBadge(
                      Texts.translate(
                        Texts.confidenceLevel,
                        alert.confidenceLevel,
                      ),
                      switch (alert.confidenceLevel) {
                        "alta" => .ok,
                        "moderada" => .warning,
                        _ => .critical,
                      },
                    ),
                    Expanded(
                      child: Text(
                        "${(alert.confidence * 100).round()}% de confiança na projeção, com horizonte de ${alert.projection.horizonHours}h.",
                      ),
                    ),
                  ],
                ),
              ),
              const SectionTitle("Limitações"),
              FluxoContainer(
                child: Column(
                  crossAxisAlignment: .start,
                  spacing: 8,
                  children: [
                    for (final code in alert.limitations)
                      _Item(
                        Icons.warning_amber_outlined,
                        Texts.translate(Texts.limitations, code),
                      ),
                    const _Item(
                      Icons.warning_amber_outlined,
                      "A previsão não é confiável fora da cobertura da API ou com confiança baixa.",
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              Text(
                "Gerado em ${alert.generatedAt.replaceFirst("T", " às ").substring(0, 19)}",
                style: theme.textTheme.labelMedium?.copyWith(
                  color: theme.hintColor,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  static String _describeReason(Reason reason) {
    final text = Texts.translate(Texts.reasons, reason.code);
    if (reason.code == "ocupacao_acima_limite") {
      return "$text: ${reason.data["ocupacao_pct"]}% acima de ${reason.data["limiar_pct"]}% "
          "por mais de ${reason.data["duracao_min"]} min";
    }
    return text;
  }
}

class _Item extends StatelessWidget {
  final IconData icon;
  final String text;

  const _Item(this.icon, this.text);

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: .start,
      spacing: 8,
      children: [
        Icon(icon, size: 20, color: Theme.of(context).primaryColor),
        Expanded(child: Text(text)),
      ],
    );
  }
}
