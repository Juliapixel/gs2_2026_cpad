import 'package:cpad/components/async_view.dart';
import 'package:cpad/services/api.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';

void main() {
  Future<void> pullDown(WidgetTester tester, AsyncView<List<int>> view) async {
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: view)));
    await tester.fling(find.byType(ListView), const Offset(0, 300), 1000);
    await tester.pumpAndSettle();
  }

  testWidgets("pull to refresh calls onRetry with data", (tester) async {
    var calls = 0;
    await pullDown(
      tester,
      AsyncView<List<int>>(
        value: const AsyncData(ApiResponse([1, 2, 3])),
        onRetry: () async => calls++,
        builder: (_, data) => ListView(children: [for (final d in data) Text("$d")]),
      ),
    );
    expect(calls, 1);
  });

  testWidgets("pull to refresh calls onRetry on empty state", (tester) async {
    var calls = 0;
    await pullDown(
      tester,
      AsyncView<List<int>>(
        value: const AsyncData(ApiResponse(<int>[])),
        isEmpty: (data) => data.isEmpty,
        onRetry: () async => calls++,
        builder: (_, _) => ListView(),
      ),
    );
    expect(calls, 1);
  });
}
