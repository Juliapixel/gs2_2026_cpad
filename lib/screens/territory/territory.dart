import 'package:cpad/colors.dart';
import 'package:cpad/components/async_view.dart';
import 'package:cpad/components/bar_chart.dart';
import 'package:cpad/components/fluxo_container.dart';
import 'package:cpad/components/kpi_card.dart';
import 'package:cpad/components/section_title.dart';
import 'package:cpad/components/status_badge.dart';
import 'package:cpad/components/status_card.dart';
import 'package:cpad/providers/dashboard.dart';
import 'package:cpad/texts.dart';
import 'package:flutter/material.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';

class TerritoryScreen extends ConsumerWidget {
  const TerritoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final colors = theme.extension<FluxoColors>()!;
    return AsyncView(
      value: ref.watch(territoryProvider),
      onRetry: () => ref.refresh(territoryProvider.future),
      builder: (context, territory) {
        int count(String priority) => territory.priorities.where((a) => a.priority == priority).length;
        return ListView(
          padding: const .all(16),
          children: [
            const SectionTitle("Território"),
            KpiGrid(
              children: [
                KpiCard("Máxima do dia", territory.dayMax, lowerIsBetter: true),
                KpiCard("Cobertura da atenção básica", territory.coverage),
                StatusCard("Áreas prioritárias", "${territory.priorityAreas}/${territory.totalAreas}",
                    const StatusText("critério social")),
                KpiCard("Visitas previstas", territory.plannedVisits),
              ],
            ),
            SectionTitle("Áreas por prioridade (${Texts.translate(Texts.areaLevel, territory.areaLevel)})"),
            FluxoBarChart(
              maxY: (territory.priorities.length.clamp(4, 100)).toDouble(),
              description: "Quantidade de áreas por prioridade",
              bars: [
                Bar("Alta", count("alta").toDouble(), theme.colorScheme.error),
                Bar("Moderada", count("moderada").toDouble(), colors.warning),
                Bar("Baixa", count("baixa").toDouble(), colors.success),
              ],
            ),
            const SectionTitle("Prioridade de visitas"),
            for (final area in territory.priorities)
              Padding(
                padding: const .only(bottom: 8),
                child: FluxoContainer(
                  child: Row(
                    children: [
                      Expanded(child: Text(area.area, style: theme.textTheme.titleSmall?.copyWith(fontWeight: .bold))),
                      StatusBadge(
                        Texts.translate(Texts.priority, area.priority),
                        switch (area.priority) { "alta" => .critical, "moderada" => .warning, _ => .ok },
                      ),
                    ],
                  ),
                ),
              ),
          ],
        );
      },
    );
  }
}
