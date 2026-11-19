import 'package:flutter/material.dart';

class FluxoContainer extends Container {
  FluxoContainer({
    super.key,
    super.alignment,
    super.padding = const EdgeInsets.all(16),
    super.isAntiAlias = true,
    super.decoration = const BoxDecoration(
      color: Colors.white,
      borderRadius: .all(.circular(14)),
      border: BoxBorder.symmetric(
        vertical: BorderSide(color: Colors.black12, width: 1),
        horizontal: BorderSide(color: Colors.black12, width: 1),
      ),
    ),
    super.foregroundDecoration,
    super.width,
    super.height,
    super.constraints,
    super.margin,
    super.transform,
    super.transformAlignment,
    super.child,
    super.clipBehavior = Clip.none,
  }) : super(color: null);
}
