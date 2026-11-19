import 'package:cpad/components/async_view.dart';
import 'package:cpad/components/fluxo_container.dart';
import 'package:cpad/components/section_title.dart';
import 'package:cpad/components/status_badge.dart';
import 'package:cpad/providers/reports.dart';
import 'package:cpad/routes.dart';
import 'package:cpad/texts.dart';
import 'package:flutter/material.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';

class ReportsScreen extends ConsumerWidget {
  const ReportsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    return Column(
      children: [
        Padding(
          padding: const .fromLTRB(16, 16, 16, 0),
          child: FilledButton.icon(
            onPressed: () async {
              final sent = await Navigator.pushNamed(context, Routes.newReport);
              if (sent == true) ref.invalidate(reportsProvider);
            },
            icon: const Icon(Icons.add),
            label: const Text("Registrar relato"),
          ),
        ),
        Expanded(
          child: AsyncView(
            value: ref.watch(reportsProvider),
            onRetry: () => ref.refresh(reportsProvider.future),
            isEmpty: (reports) => reports.isEmpty,
            emptyText: "Você ainda não registrou um relato.",
            builder: (context, reports) => ListView(
              padding: const .all(16),
              children: [
                const SectionTitle("Seus relatos"),
                for (final report in reports)
                  Padding(
                    padding: const .only(bottom: 8),
                    child: FluxoContainer(
                      child: Column(
                        crossAxisAlignment: .start,
                        spacing: 6,
                        children: [
                          Row(
                            spacing: 8,
                            children: [
                              Expanded(
                                child: Text(
                                  Texts.translate(
                                    Texts.reportTypes,
                                    report.type,
                                  ),
                                  style: theme.textTheme.titleSmall?.copyWith(
                                    fontWeight: .bold,
                                  ),
                                ),
                              ),
                              StatusBadge(
                                Texts.translate(
                                  Texts.reportStatus,
                                  report.status,
                                ),
                                .info,
                              ),
                            ],
                          ),
                          Text(
                            "${report.unitName} · ${Texts.translate(Texts.reportWhen, report.when)}",
                            style: theme.textTheme.labelMedium?.copyWith(
                              color: theme.hintColor,
                            ),
                          ),
                          Text(report.description),
                          Text(
                            report.id,
                            style: theme.textTheme.labelSmall?.copyWith(
                              color: theme.hintColor,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
