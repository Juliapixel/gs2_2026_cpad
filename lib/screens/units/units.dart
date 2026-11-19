import 'package:cpad/colors.dart';
import 'package:cpad/components/async_view.dart';
import 'package:cpad/components/bar_chart.dart';
import 'package:cpad/components/fluxo_container.dart';
import 'package:cpad/components/kpi_card.dart';
import 'package:cpad/components/section_title.dart';
import 'package:cpad/components/status_badge.dart';
import 'package:cpad/models/dashboard.dart';
import 'package:cpad/providers/dashboard.dart';
import 'package:flutter/material.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';

class UnitsScreen extends ConsumerWidget {
  const UnitsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    return AsyncView(
      value: ref.watch(capacityProvider),
      onRetry: () => ref.refresh(capacityProvider.future),
      builder: (context, capacity) => ListView(
        padding: const .all(16),
        children: [
          SectionTitle(
            "Capacidade · ${capacity.openUnits} de ${capacity.totalUnits} unidades abertas",
          ),
          KpiGrid(
            children: [
              KpiCard("Vagas totais", capacity.totalBeds),
              KpiCard("Vagas livres", capacity.freeBeds),
              KpiCard(
                "Espera média",
                capacity.averageWait,
                lowerIsBetter: true,
              ),
              KpiCard("Equipes", capacity.teams),
            ],
          ),
          const SectionTitle("Ocupação por unidade (%)"),
          FluxoBarChart(
            maxY: 100,
            threshold: capacity.attentionThresholdPct.toDouble(),
            description:
                "Gráfico de ocupação por unidade, limiar de atenção em ${capacity.attentionThresholdPct}%",
            bars: [
              for (final (i, unit) in capacity.units.indexed)
                Bar(
                  "${i + 1}",
                  unit.occupancyPct.toDouble(),
                  unit.aboveThreshold
                      ? theme.colorScheme.error
                      : theme.primaryColor,
                ),
            ],
          ),
          const SectionTitle("Unidades"),
          for (final (i, unit) in capacity.units.indexed)
            _UnitTile(index: i + 1, unit: unit),
        ],
      ),
    );
  }
}

class _UnitTile extends StatelessWidget {
  final int index;
  final UnitCapacity unit;

  const _UnitTile({required this.index, required this.unit});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final (text, kind) = !unit.open
        ? ("Fechada", StatusKind.info)
        : unit.aboveThreshold
        ? ("Atenção", StatusKind.critical)
        : ("Estável", StatusKind.ok);
    return Padding(
      padding: const .only(bottom: 8),
      child: FluxoContainer(
        child: Column(
          crossAxisAlignment: .start,
          spacing: 8,
          children: [
            Row(
              spacing: 8,
              children: [
                Expanded(
                  child: Text(
                    "$index. ${unit.name}",
                    style: theme.textTheme.titleSmall?.copyWith(
                      fontWeight: .bold,
                    ),
                    overflow: .ellipsis,
                  ),
                ),
                StatusBadge(text, kind),
              ],
            ),
            Semantics(
              label: "Ocupação ${unit.occupancyPct}%",
              child: LinearProgressIndicator(
                value: unit.occupancyPct / 100,
                minHeight: 8,
                borderRadius: .circular(4),
                color: unit.aboveThreshold
                    ? theme.colorScheme.error
                    : theme.extension<FluxoColors>()!.success,
              ),
            ),
            Text(
              "${unit.type} · ocupação ${unit.occupancyPct}%",
              style: theme.textTheme.labelMedium?.copyWith(
                color: theme.hintColor,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
