import 'package:cpad/components/notice_banner.dart';
import 'package:cpad/services/api.dart';
import 'package:cpad/texts.dart';
import 'package:flutter/material.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';

/// Loading, error, empty and offline states; with [onRetry], pull to refresh.
class AsyncView<T> extends StatelessWidget {
  final AsyncValue<ApiResponse<T>> value;

  /// Must return a scrollable widget for pull to refresh to work.
  final Widget Function(BuildContext context, T data) builder;
  final Future<void> Function()? onRetry;
  final bool Function(T data)? isEmpty;
  final String emptyText;

  const AsyncView({
    super.key,
    required this.value,
    required this.builder,
    this.onRetry,
    this.isEmpty,
    this.emptyText = "Nada por aqui ainda.",
  });

  Widget _refreshable(Widget child) {
    final retry = onRetry;
    if (retry == null) return child;
    return RefreshIndicator(
      // The error already shows on screen via [value]; this only avoids an unhandled exception.
      onRefresh: () => retry().then((_) {}, onError: (_) {}),
      child: child,
    );
  }

  @override
  Widget build(BuildContext context) {
    return _refreshable(_content(context));
  }

  Widget _content(BuildContext context) {
    return value.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, _) => switch (error) {
        NoCoverageException(:final code) => _StatusView(
          icon: Icons.map_outlined,
          title: "Ainda sem dados",
          message: Texts.translate(Texts.noCoverage, code),
          onRetry: onRetry,
        ),
        _ => _StatusView(
          icon: Icons.cloud_off,
          title: "Não foi possível carregar",
          message: describeError(error),
          onRetry: onRetry,
        ),
      },
      data: (response) {
        if (isEmpty?.call(response.data) ?? false) {
          return _StatusView(
            icon: Icons.inbox_outlined,
            title: emptyText,
            onRetry: onRetry,
          );
        }
        final cachedAt = response.cachedAt;
        return Column(
          children: [
            if (cachedAt != null)
              Padding(
                padding: const .fromLTRB(16, 16, 16, 0),
                child: NoticeBanner(
                  "Sem conexão. Mostrando cópia salva em ${_formatDate(cachedAt)}.",
                  kind: .warning,
                  icon: Icons.cloud_off,
                ),
              ),
            Expanded(child: builder(context, response.data)),
          ],
        );
      },
    );
  }

  static String _formatDate(DateTime date) {
    String two(int n) => n.toString().padLeft(2, "0");
    return "${two(date.day)}/${two(date.month)} às ${two(date.hour)}h${two(date.minute)}";
  }
}

class _StatusView extends StatelessWidget {
  final IconData icon;
  final String title;
  final String? message;
  final Future<void> Function()? onRetry;

  const _StatusView({
    required this.icon,
    required this.title,
    this.message,
    this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return LayoutBuilder(
      builder: (context, constraints) => ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        children: [
          ConstrainedBox(
            constraints: BoxConstraints(minHeight: constraints.maxHeight),
            child: Center(
              child: Padding(
                padding: const .all(24),
                child: Column(
                  mainAxisSize: .min,
                  spacing: 12,
                  children: [
                    Icon(icon, size: 48, color: theme.hintColor),
                    Text(
                      title,
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: .bold,
                      ),
                      textAlign: .center,
                    ),
                    if (message != null)
                      Text(
                        message!,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: theme.hintColor,
                        ),
                        textAlign: .center,
                      ),
                    if (onRetry != null)
                      OutlinedButton.icon(
                        onPressed: onRetry,
                        icon: const Icon(Icons.refresh),
                        label: const Text("Tentar novamente"),
                      ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
