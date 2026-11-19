import 'package:cpad/components/status_card.dart';
import 'package:cpad/models/kpi.dart';
import 'package:flutter/material.dart';

class KpiCard extends StatelessWidget {
  final String title;
  final Kpi kpi;

  /// E.g. wait time and occupancy, where going down is good and up is bad.
  final bool lowerIsBetter;
  final VoidCallback? onTap;

  const KpiCard(this.title, this.kpi, {super.key, this.lowerIsBetter = false, this.onTap});

  StatusText? get _trend {
    final text = kpi.formattedChange;
    if (text == null) return null;
    final change = kpi.change!;
    if (change == 0) return StatusText(text);
    final up = change > 0;
    final good = lowerIsBetter ? !up : up;
    return StatusText("${up ? "↑" : "↓"} $text", tone: good ? .good : .bad);
  }

  @override
  Widget build(BuildContext context) {
    return StatusCard(title, kpi.formattedValue, _trend, onTap: onTap);
  }
}

class KpiGrid extends StatelessWidget {
  final List<Widget> children;

  const KpiGrid({super.key, required this.children});

  @override
  Widget build(BuildContext context) {
    return Column(
      spacing: 12,
      children: [
        for (var i = 0; i < children.length; i += 2)
          IntrinsicHeight(
            child: Row(
              crossAxisAlignment: .stretch,
              spacing: 12,
              children: [
                Expanded(child: children[i]),
                Expanded(child: i + 1 < children.length ? children[i + 1] : const SizedBox()),
              ],
            ),
          ),
      ],
    );
  }
}
