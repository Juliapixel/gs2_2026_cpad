import 'package:flutter/material.dart';

class MyAppBar extends StatelessWidget implements PreferredSizeWidget {
  const MyAppBar({super.key});

  @override
  Size get preferredSize => .fromHeight(_preferredHeight);

  static final double _preferredHeight = 100.0;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme
        .apply(bodyColor: Colors.white, displayColor: Colors.white);

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
    // final expandedHeight = MediaQuery.of(context).size.height * 0.2;
    // final bar = SliverAppBar(
    //   expandedHeight: expandedHeight,
    //   pinned: true,
    //   backgroundColor: Color(0xff072B62),
    //   leading: IconButton(
    //     onPressed: () {},
    //     icon: Icon(Icons.arrow_back, color: Colors.white),
    //   ),
    //   title: logo,
    //   flexibleSpace: LayoutBuilder(
    //     builder: (context, constraints) {
    //       final fraction =
    //           max(0, constraints.biggest.height - kToolbarHeight) /
    //           (expandedHeight - kToolbarHeight);
    //       return FlexibleSpaceBar(
    //         collapseMode: .pin,
    //         background: Padding(
    //           padding: .directional(
    //             bottom: 16,
    //             start: (Theme.of(context).appBarTheme.leadingWidth ?? kToolbarHeight) + 16,
    //             end: 16,
    //             top: kToolbarHeight + 16,
    //           ),
    //           child: Column(
    //             crossAxisAlignment: .start,
    //             mainAxisAlignment: .start,
    //             children: [Text("oi"), Text("oi2")],
    //           ),
    //         ),
    //       );
    //     },
    //   ),
    // );
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
                "Lugar, Sei lá",
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
