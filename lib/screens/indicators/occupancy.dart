import 'package:cpad/colors.dart';
import 'package:cpad/components/async_view.dart';
import 'package:cpad/components/fluxo_container.dart';
import 'package:cpad/components/kpi_card.dart';
import 'package:cpad/components/section_title.dart';
import 'package:cpad/components/status_card.dart';
import 'package:cpad/models/dashboard.dart';
import 'package:cpad/providers/dashboard.dart';
import 'package:cpad/screens/home/home.dart';
import 'package:cpad/texts.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';

class OccupancyScreen extends ConsumerWidget {
  const OccupancyScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text("Ocupação da rede"), foregroundColor: Colors.white),
      body: AsyncView(
        value: ref.watch(occupancyProvider),
        onRetry: () => ref.refresh(occupancyProvider.future),
        builder: (context, indicator) => ListView(
          padding: const .all(16),
          children: [
            KpiGrid(
              children: [
                StatusCard(
                  "Ocupação agora",
                  "${indicator.occupancyPct}%",
                  indicator.change == 0
                      ? StatusText("estável ${Texts.translate(Texts.window, indicator.window)}")
                      : StatusText(
                          "${indicator.change > 0 ? "↑" : "↓"} ${indicator.change.abs()} pp ${Texts.translate(Texts.window, indicator.window)}",
                          tone: indicator.change > 0 ? .bad : .good,
                        ),
                ),
                StatusCard("Vagas ocupadas", "${indicator.occupiedBeds}/${indicator.totalBeds}", null),
              ],
            ),
            SectionTitle("${indicator.highlightedUnit} · ${indicator.highlightedUnitPct}%"),
            FluxoContainer(
              child: Column(
                crossAxisAlignment: .start,
                spacing: 12,
                children: [
                  SizedBox(height: 220, child: _OccupancyChart(indicator)),
                  Wrap(
                    spacing: 16,
                    runSpacing: 4,
                    children: [
                      _Legend("Observado", theme.primaryColor),
                      _Legend("Projetado", theme.extension<FluxoColors>()!.warning),
                      _Legend("Limiar ${indicator.thresholdPct}%", theme.colorScheme.error),
                    ],
                  ),
                ],
              ),
            ),
            const SectionTitle("Regra de atenção"),
            FluxoContainer(
              child: Text(
                "A unidade entra em atenção quando a ocupação fica acima de ${indicator.thresholdPct}% "
                "por mais de ${indicator.durationMin} minutos. A projeção cobre as próximas 4 horas.",
              ),
            ),
            if (indicator.highlightedAlert != null) ...[
              const SectionTitle("Alerta relacionado"),
              AlertCard(indicator.highlightedAlert!),
            ],
          ],
        ),
      ),
    );
  }
}

class _Legend extends StatelessWidget {
  final String text;
  final Color color;

  const _Legend(this.text, this.color);

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: .min,
      spacing: 6,
      children: [
        Container(width: 12, height: 12, decoration: BoxDecoration(color: color, shape: .circle)),
        Text(text, style: Theme.of(context).textTheme.labelMedium),
      ],
    );
  }
}

class _OccupancyChart extends StatelessWidget {
  final OccupancyIndicator indicator;

  const _OccupancyChart(this.indicator);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final axisStyle = theme.textTheme.labelSmall?.copyWith(color: theme.hintColor);
    final points = indicator.points;
    final observed = <FlSpot>[];
    final projected = <FlSpot>[];
    for (final (i, point) in points.indexed) {
      final spot = FlSpot(i.toDouble(), point.occupancyPct.toDouble());
      if (point.projected) {
        // Connects the projection to the last observed point.
        if (projected.isEmpty && observed.isNotEmpty) projected.add(observed.last);
        projected.add(spot);
      } else {
        observed.add(spot);
      }
    }
    return Semantics(
      label: "Gráfico de ocupação por hora. Observado: ${points.where((p) => !p.projected).map((p) => '${p.hour}h ${p.occupancyPct}%').join(', ')}. "
          "Projetado: ${points.where((p) => p.projected).map((p) => '${p.hour}h ${p.occupancyPct}%').join(', ')}.",
      child: LineChart(
        LineChartData(
          lineTouchData: LineTouchData(
            touchTooltipData: LineTouchTooltipData(
              getTooltipColor: (_) => const Color(0xFFEEEEEE),
              fitInsideHorizontally: true,
              fitInsideVertically: true,
              getTooltipItems: (spots) => [
                for (final spot in spots)
                  LineTooltipItem(
                    "${points[spot.x.toInt()].hour}h: ${spot.y.toInt()}%",
                    theme.textTheme.labelMedium!.copyWith(fontWeight: .bold),
                  ),
              ],
            ),
          ),
          minY: 0,
          maxY: 100,
          minX: 0,
          maxX: (points.length - 1).toDouble(),
          borderData: FlBorderData(show: false),
          gridData: const FlGridData(drawVerticalLine: false, horizontalInterval: 25),
          titlesData: FlTitlesData(
            topTitles: const AxisTitles(),
            rightTitles: const AxisTitles(),
            leftTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                reservedSize: 36,
                interval: 25,
                getTitlesWidget: (value, _) => Text("${value.toInt()}%", style: axisStyle),
              ),
            ),
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                reservedSize: 24,
                interval: 1,
                getTitlesWidget: (value, _) => Padding(
                  padding: const .only(top: 4),
                  child: Text("${points[value.toInt()].hour}h", style: axisStyle),
                ),
              ),
            ),
          ),
          extraLinesData: ExtraLinesData(
            horizontalLines: [
              HorizontalLine(y: indicator.thresholdPct.toDouble(), color: theme.colorScheme.error, strokeWidth: 1.5, dashArray: [6, 4]),
            ],
          ),
          lineBarsData: [
            LineChartBarData(
              spots: observed,
              color: theme.primaryColor,
              barWidth: 3,
              isCurved: true,
              dotData: const FlDotData(show: true),
              belowBarData: BarAreaData(show: true, color: theme.colorScheme.primaryContainer),
            ),
            LineChartBarData(
              spots: projected,
              color: theme.extension<FluxoColors>()!.warning,
              barWidth: 3,
              isCurved: true,
              dashArray: [8, 6],
              dotData: const FlDotData(show: true),
            ),
          ],
        ),
      ),
    );
  }
}
