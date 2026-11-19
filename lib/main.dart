import 'package:cpad/colors.dart';
import 'package:cpad/components/myappbar.dart';
import 'package:cpad/routes.dart';
import 'package:cpad/screens/home/home.dart';
import 'package:cpad/screens/profile/profile.dart';
import 'package:cpad/screens/reports/reports.dart';
import 'package:cpad/screens/territory/territory.dart';
import 'package:cpad/screens/units/units.dart';
import 'package:flutter/material.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';

void main() {
  runApp(ProviderScope(retry: (_, _) => null, child: const MyApp()));
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "FluxoMed",
      theme: ThemeData(
        extensions: const [FluxoColors()],
        colorScheme:
            .fromSwatch(
              primarySwatch: MaterialColor(
                Color.fromARGB(255, 25, 81, 164).toARGB32(),
                {
                  50: Color.fromARGB(255, 193, 215, 252),
                  100: Color.fromARGB(255, 174, 204, 251),
                  200: Color.fromARGB(255, 131, 176, 249),
                  300: Color.fromARGB(255, 92, 149, 240),
                  400: Color.fromARGB(255, 57, 117, 214),
                  500: Color.fromARGB(255, 25, 81, 164),
                  600: Color.fromARGB(255, 19, 81, 180),
                  700: Color.fromARGB(255, 21, 74, 154),
                  800: Color.fromARGB(255, 13, 56, 121),
                  900: Color.fromARGB(255, 7, 43, 98),
                },
              ),
              errorColor: Color(0xFFB42332),
              backgroundColor: Color(0xFFF3F6FA),
            ).copyWith(
              primaryContainer: Color(0xFFEAF1FC),
              errorContainer: Color(0xFFFDEDEF),
              onPrimaryContainer: Colors.white,
              // fromSwatch would leave outline white (invisible field borders).
              outline: Colors.black45,
              outlineVariant: Colors.black12,
            ),
        fontFamily: "Inter",
        appBarTheme: AppBarThemeData(backgroundColor: Color.fromARGB(255, 7, 43, 98)),
      ),
      initialRoute: Routes.home,
      onGenerateRoute: generateRoute,
    );
  }
}

class MyHomePage extends StatelessWidget {
  const MyHomePage({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    final tabBar = TabBar(
      labelPadding: const .symmetric(horizontal: 2),
      labelStyle: theme.textTheme.labelMedium?.copyWith(
        fontWeight: .bold,
        color: theme.primaryColor,
      ),
      unselectedLabelStyle: theme.textTheme.labelMedium?.copyWith(
        fontWeight: .w500,
        color: theme.hintColor,
      ),
      tabs: [
        Tab(text: "Rede", icon: Icon(Icons.language)),
        Tab(text: "Unidades", icon: Icon(Icons.local_hospital_outlined)),
        Tab(text: "Território", icon: Icon(Icons.map_outlined)),
        Tab(text: "Relatos", icon: Icon(Icons.error_outline)),
        Tab(text: "Perfil", icon: Icon(Icons.account_circle)),
      ],
    );

    return DefaultTabController(
      initialIndex: 0,
      length: tabBar.tabs.length,
      child: Scaffold(
        appBar: MyAppBar(),
        bottomNavigationBar: SafeArea(bottom: true, child: tabBar),
        body: TabBarView(
          children: [
            HomeScreen(),
            UnitsScreen(),
            TerritoryScreen(),
            ReportsScreen(),
            Profile(),
          ],
        ),
      ),
    );
  }
}
