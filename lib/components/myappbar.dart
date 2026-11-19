import 'package:cpad/providers/settings.dart';
import 'package:flutter/material.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';

class MyAppBar extends ConsumerWidget implements PreferredSizeWidget {
  const MyAppBar({super.key});

  @override
  Size get preferredSize => .fromHeight(_preferredHeight);

  static final double _preferredHeight = 100.0;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final textTheme = Theme.of(context).textTheme
        .apply(bodyColor: Colors.white, displayColor: Colors.white);
    final locality = ref.watch(localityProvider).value;

    final logo = Text.rich(
      TextSpan(
        style: .new(fontWeight: .w300, fontStyle: .italic),
        text: "Fluxo",
        children: [
          TextSpan(
            text: "Med",
            style: .new(fontWeight: .w900, fontStyle: .normal),
          ),
        ],
      ),
      style: textTheme.displaySmall?.apply(color: Colors.white),
    );
    final bar = AppBar(
      title: SizedBox(
        height: _preferredHeight,
        child: Padding(
          padding: .symmetric(horizontal: 6, vertical: 16),
          child: Column(
            spacing: 3,
            mainAxisAlignment: .center,
            crossAxisAlignment: .start,
            children: [
              logo,
              Text(
                locality?.label ?? "Carregando localidade...",
                style: textTheme.bodyMedium,
                maxLines: 1,
                overflow: .ellipsis,
              ),
            ],
          ),
        ),
      ),
      toolbarHeight: _preferredHeight,
    );
    return Theme(
      data: Theme.of(context).copyWith(
        textTheme: Theme.of(context).textTheme
            .apply(bodyColor: Colors.white, displayColor: Colors.white),
      ),
      child: bar,
    );
  }
}
