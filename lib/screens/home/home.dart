import 'package:cpad/components/status_badge.dart';
import 'package:cpad/screens/home/components/status_card.dart';
import 'package:flutter/material.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        StatusCard("Ocupação da rede", "67%", PositiveStatusText("5 mais pessoas tratadas")),
        Row(
          mainAxisAlignment: .center,
          spacing: 12,
          children: [
          StatusBadge("Topperson", .ok),
          StatusBadge("Informativo", .info),
          StatusBadge("Aviso", .warning),
          StatusBadge("Crítico", .critical)
        ],)
      ],
    );
  }
}
