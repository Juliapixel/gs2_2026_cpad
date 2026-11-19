import 'package:cpad/main.dart';
import 'package:cpad/screens/alerts/alert.dart';
import 'package:cpad/screens/indicators/occupancy.dart';
import 'package:cpad/screens/reports/new_report.dart';
import 'package:flutter/material.dart';

abstract final class Routes {
  static const home = "/";
  static const occupancy = "/indicador/ocupacao";
  static const alert = "/alerta";
  static const newReport = "/relatos/novo";
}

Route<dynamic>? generateRoute(RouteSettings settings) {
  final Widget screen;
  switch (settings.name) {
    case Routes.home:
      screen = const MyHomePage();
    case Routes.occupancy:
      screen = const OccupancyScreen();
    case Routes.alert:
      screen = AlertScreen(id: settings.arguments as String);
    case Routes.newReport:
      screen = const NewReportScreen();
    default:
      return null;
  }
  return MaterialPageRoute(builder: (_) => screen, settings: settings);
}
