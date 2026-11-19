import 'package:cpad/components/async_view.dart';
import 'package:cpad/components/notice_banner.dart';
import 'package:cpad/models/report.dart';
import 'package:cpad/providers/reports.dart';
import 'package:cpad/providers/settings.dart';
import 'package:cpad/screens/reports/validation.dart';
import 'package:cpad/services/api.dart';
import 'package:cpad/texts.dart';
import 'package:flutter/material.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';

class NewReportScreen extends ConsumerWidget {
  const NewReportScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(title: const Text("Novo relato"), foregroundColor: Colors.white),
      body: AsyncView(
        value: ref.watch(reportOptionsProvider),
        onRetry: () => ref.refresh(reportOptionsProvider.future),
        builder: (context, options) => _ReportForm(options),
      ),
    );
  }
}

class _ReportForm extends ConsumerStatefulWidget {
  final ReportOptions options;

  const _ReportForm(this.options);

  @override
  ConsumerState<_ReportForm> createState() => _ReportFormState();
}

class _ReportFormState extends ConsumerState<_ReportForm> {
  final _form = GlobalKey<FormState>();
  final _description = TextEditingController();
  String? _unitId;
  String? _type;
  String? _when;
  bool _consent = false;
  bool _showConsentError = false;
  bool _sending = false;

  @override
  void dispose() {
    _description.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final valid = _form.currentState!.validate();
    setState(() => _showConsentError = !_consent);
    if (!valid || !_consent) return;
    setState(() => _sending = true);
    final messenger = ScaffoldMessenger.of(context);
    final navigator = Navigator.of(context);
    try {
      final api = await ref.read(apiProvider.future);
      final locality = await ref.read(localityProvider.future);
      await api.post("/cidadao/relatos", {
        ...locality.query,
        "unidade_id": _unitId,
        "tipo_ocorrencia": _type,
        "quando": _when,
        "descricao": _description.text.trim(),
        "consentimento_uso_agregado": _consent,
      });
      messenger.showSnackBar(const SnackBar(content: Text("Relato registrado. Obrigado por contribuir!")));
      navigator.pop(true);
    } on ApiException catch (e) {
      final fields = e.fields.map((f) => f["campo"]).join(", ");
      messenger.showSnackBar(SnackBar(content: Text(fields.isEmpty ? describeError(e) : "Confira os campos: $fields")));
    } on Exception catch (e) {
      messenger.showSnackBar(SnackBar(content: Text(describeError(e))));
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final options = widget.options;
    return Form(
      key: _form,
      autovalidateMode: .onUserInteraction,
      child: ListView(
        padding: const .all(16),
        children: [
          const NoticeBanner(
            "Relato anônimo: não coletamos nome, CPF nem contato. Os dados são usados apenas de forma agregada.",
            icon: Icons.lock_outline,
          ),
          const SizedBox(height: 16),
          DropdownButtonFormField<String>(
            initialValue: _unitId,
            decoration: const InputDecoration(labelText: "Unidade de saúde", border: OutlineInputBorder()),
            items: [for (final unit in options.units) DropdownMenuItem(value: unit.id, child: Text(unit.name))],
            onChanged: (v) => setState(() => _unitId = v),
            validator: validateRequired,
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            initialValue: _type,
            decoration: const InputDecoration(labelText: "Tipo de ocorrência", border: OutlineInputBorder()),
            items: [for (final type in options.types) DropdownMenuItem(value: type, child: Text(Texts.translate(Texts.reportTypes, type)))],
            onChanged: (v) => setState(() => _type = v),
            validator: validateRequired,
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            initialValue: _when,
            decoration: const InputDecoration(labelText: "Quando aconteceu", border: OutlineInputBorder()),
            items: [for (final when in options.whenOptions) DropdownMenuItem(value: when, child: Text(Texts.translate(Texts.reportWhen, when)))],
            onChanged: (v) => setState(() => _when = v),
            validator: validateRequired,
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _description,
            maxLines: 4,
            maxLength: 500,
            decoration: InputDecoration(
              labelText: "Descrição",
              helperText: "Mínimo de ${options.minDescription} caracteres",
              border: const OutlineInputBorder(),
            ),
            validator: (v) => validateDescription(v, options.minDescription),
          ),
          CheckboxListTile(
            value: _consent,
            onChanged: (v) => setState(() {
              _consent = v ?? false;
              _showConsentError = false;
            }),
            controlAffinity: .leading,
            contentPadding: .zero,
            title: const Text("Autorizo o uso anônimo e agregado deste relato para melhorar a rede de saúde."),
            subtitle: _showConsentError
                ? Text("É preciso consentir para enviar", style: TextStyle(color: theme.colorScheme.error))
                : null,
          ),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: _sending ? null : _submit,
            icon: _sending
                ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.send),
            label: Text(_sending ? "Enviando..." : "Enviar relato"),
          ),
        ],
      ),
    );
  }
}
