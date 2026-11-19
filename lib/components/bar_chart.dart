import 'package:cpad/components/fluxo_container.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

class Bar {
  final String label;
  final double value;
  final Color color;

  const Bar(this.label, this.value, this.color);
}

class FluxoBarChart extends StatelessWidget {
  final List<Bar> bars;
  final double maxY;
  final double? threshold;
  final String description;

  const FluxoBarChart({
    super.key,
    required this.bars,
    required this.maxY,
    required this.description,
    this.threshold,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final axisStyle = theme.textTheme.labelSmall?.copyWith(
      color: theme.hintColor,
    );
    return FluxoContainer(
      child: Semantics(
        label: description,
        child: SizedBox(
          height: 180,
          child: BarChart(
            BarChartData(
              maxY: maxY,
              alignment: .spaceAround,
              barTouchData: BarTouchData(
                touchTooltipData: BarTouchTooltipData(
                  getTooltipColor: (_) => const Color(0xFFEEEEEE),
                  fitInsideHorizontally: true,
                  fitInsideVertically: true,
                  getTooltipItem: (group, _, rod, _) => BarTooltipItem(
                    "${bars[group.x].label}: ${rod.toY.toInt()}",
                    theme.textTheme.labelMedium!.copyWith(fontWeight: .bold),
                  ),
                ),
              ),
              borderData: FlBorderData(show: false),
              gridData: FlGridData(
                drawVerticalLine: false,
                horizontalInterval: maxY / 4,
              ),
              titlesData: FlTitlesData(
                topTitles: const AxisTitles(),
                rightTitles: const AxisTitles(),
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    reservedSize: 32,
                    interval: maxY / 4,
                    getTitlesWidget: (value, _) =>
                        Text("${value.toInt()}", style: axisStyle),
                  ),
                ),
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    reservedSize: 24,
                    getTitlesWidget: (value, _) => Padding(
                      padding: const .only(top: 4),
                      child: Text(bars[value.toInt()].label, style: axisStyle),
                    ),
                  ),
                ),
              ),
              extraLinesData: ExtraLinesData(
                horizontalLines: [
                  if (threshold != null)
                    HorizontalLine(
                      y: threshold!,
                      color: theme.colorScheme.error,
                      strokeWidth: 1.5,
                      dashArray: [6, 4],
                    ),
                ],
              ),
              barGroups: [
                for (final (i, bar) in bars.indexed)
                  BarChartGroupData(
                    x: i,
                    barRods: [
                      BarChartRodData(
                        toY: bar.value,
                        color: bar.color,
                        width: 14,
                        borderRadius: .circular(4),
                      ),
                    ],
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
