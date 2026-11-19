import 'package:cpad/colors.dart';
import 'package:cpad/components/myappbar.dart';
import 'package:cpad/screens/home/home.dart';
import 'package:flutter/material.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Demo',
      theme: ThemeData(
        extensions: const [FluxoColors()],
        // This is the theme of your application.
        //
        // TRY THIS: Try running your application with "flutter run". You'll see
        // the application has a purple toolbar. Then, without quitting the app,
        // try changing the seedColor in the colorScheme below to Colors.green
        // and then invoke "hot reload" (save your changes or press the "hot
        // reload" button in a Flutter-supported IDE, or press "r" if you used
        // the command line to start the app).
        //
        // Notice that the counter didn't reset back to zero; the application
        // state is not lost during the reload. To reset the state, use hot
        // restart instead.
        //
        // This works for code too, not just values: Most code changes can be
        // tested with just a hot reload.
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
            ),
        fontFamily: "Inter",
        appBarTheme: AppBarThemeData(backgroundColor: Color.fromARGB(255, 7, 43, 98))
      ),
      home: const MyHomePage(),
    );
  }
}

class MyHomePage extends StatelessWidget {
  const MyHomePage({super.key});

  @override
  Widget build(BuildContext context) {
    // This method is rerun every time setState is called, for instance as done
    // by the _incrementCounter method above.
    //
    // The Flutter framework has been optimized to make rerunning build methods
    // fast, so that you can just rebuild anything that needs updating rather
    // than having to individually change instances of widgets.
    final theme = Theme.of(context);

    final tab_bar = TabBar(
      labelStyle: theme.textTheme.bodyMedium?.copyWith(
        fontWeight: .bold,
        color: theme.primaryColor,
      ),
      unselectedLabelStyle: theme.textTheme.bodyMedium?.copyWith(
        fontWeight: .w500,
        color: theme.hintColor,
      ),
      tabs: [
        Tab(text: "Rede", icon: Icon(Icons.language)),
        Tab(text: "Unidades", icon: Icon(Icons.search)),
        Tab(text: "Alertas", icon: Icon(Icons.error_outline)),
        Tab(text: "Perfil", icon: Icon(Icons.account_circle)),
      ],
    );

    return DefaultTabController(
      initialIndex: 0,
      length: tab_bar.tabs.length,
      child: Scaffold(
        appBar: MyAppBar(),
        bottomNavigationBar: SafeArea(bottom: true, child: tab_bar),
        body: TabBarView(
          children: [
            HomeScreen(),
            SizedBox(height: 1000),
            SizedBox(height: 1000),
            SizedBox(height: 1000),
          ],
        ),
      ),
    );
  }
}
