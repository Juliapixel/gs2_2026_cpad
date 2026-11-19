import 'package:cpad/components/async_view.dart';
import 'package:cpad/components/fluxo_container.dart';
import 'package:cpad/components/kpi_card.dart';
import 'package:cpad/components/notice_banner.dart';
import 'package:cpad/components/section_title.dart';
import 'package:cpad/components/status_badge.dart';
import 'package:cpad/components/status_card.dart';
import 'package:cpad/models/alert.dart';
import 'package:cpad/providers/dashboard.dart';
import 'package:cpad/routes.dart';
import 'package:cpad/texts.dart';
import 'package:flutter/material.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return AsyncView(
      value: ref.watch(networkProvider),
      onRetry: () => ref.refresh(networkProvider.future),
      builder: (context, network) => ListView(
        padding: const .all(16),
        children: [
          const NoticeBanner(Texts.humanDecisionNotice),
          const SectionTitle("Rede de saúde"),
          KpiGrid(
            children: [
              KpiCard(
                "Ocupação da rede",
                network.occupancy,
                lowerIsBetter: true,
                onTap: () => Navigator.pushNamed(context, Routes.occupancy),
              ),
              KpiCard("Espera média", network.averageWait, lowerIsBetter: true),
              StatusCard(
                "Unidades em atenção",
                "${network.unitsInAttention}/${network.totalUnits}",
                StatusText("${network.activePlans} com plano ativo"),
              ),
              KpiCard("Horas de espera evitadas (benefício social)", network.avoidedWait),
            ],
          ),
          const SectionTitle("Alerta em destaque"),
          if (network.highlightedAlert == null)
            FluxoContainer(child: const Text("Nenhum alerta ativo nesta localidade."))
          else
            AlertCard(network.highlightedAlert!),
        ],
      ),
    );
  }
}

class AlertCard extends StatelessWidget {
  final AlertSummary alert;

  const AlertCard(this.alert, {super.key});

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Semantics(
      button: true,
      label: "Alerta ${alert.id}: ${Texts.translate(Texts.alertType, alert.type)} em ${alert.unitName}",
      child: InkWell(
        borderRadius: .circular(14),
        onTap: () => Navigator.pushNamed(context, Routes.alert, arguments: alert.id),
        child: FluxoContainer(
          child: Column(
            crossAxisAlignment: .start,
            spacing: 8,
            children: [
              Row(
                spacing: 8,
                children: [
                  StatusBadge(Texts.translate(Texts.severity, alert.severity), .warning),
                  StatusBadge("Confiança ${Texts.translate(Texts.confidenceLevel, alert.confidenceLevel).toLowerCase()}", .info),
                ],
              ),
              Text(Texts.translate(Texts.alertType, alert.type), style: textTheme.titleMedium?.copyWith(fontWeight: .bold)),
              Text("${alert.unitName} · previsão para as ${alert.forecastHour}h", style: textTheme.bodyMedium),
              Text("${alert.id} · toque para ver justificativa e limitações",
                  style: textTheme.labelMedium?.copyWith(color: Theme.of(context).hintColor)),
            ],
          ),
        ),
      ),
    );
  }
}
