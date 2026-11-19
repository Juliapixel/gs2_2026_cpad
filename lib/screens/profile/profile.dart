import 'package:cpad/components/notice_banner.dart';
import 'package:cpad/components/section_title.dart';
import 'package:cpad/models/locality.dart';
import 'package:cpad/providers/settings.dart';
import 'package:flutter/material.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';

class Profile extends ConsumerStatefulWidget {
  const Profile({super.key});

  @override
  ConsumerState<Profile> createState() => _ProfileState();
}

class _ProfileState extends ConsumerState<Profile> {
  final _form = GlobalKey<FormState>();
  final _host = TextEditingController();
  final _uf = TextEditingController();
  final _municipality = TextEditingController();
  final _district = TextEditingController();
  bool _filled = false;

  @override
  void dispose() {
    _host.dispose();
    _uf.dispose();
    _municipality.dispose();
    _district.dispose();
    super.dispose();
  }

  void _fill(Settings settings) {
    if (_filled) return;
    _filled = true;
    _host.text = settings.host;
    _uf.text = settings.locality.uf;
    _municipality.text = settings.locality.municipality;
    _district.text = settings.locality.district ?? "";
  }

  Future<void> _save() async {
    if (!_form.currentState!.validate()) return;
    final messenger = ScaffoldMessenger.of(context);
    await ref.read(settingsProvider.notifier).save(
      host: _host.text.trim(),
      locality: Locality(
        uf: _uf.text.trim().toUpperCase(),
        municipality: _municipality.text.trim(),
        district: _district.text.trim().isEmpty ? null : _district.text.trim(),
      ),
    );
    messenger.showSnackBar(const SnackBar(content: Text("Preferências salvas")));
  }

  @override
  Widget build(BuildContext context) {
    final settings = ref.watch(settingsProvider);
    return settings.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text("Não foi possível carregar as preferências: $e")),
      data: (settings) {
        _fill(settings);
        return Form(
          key: _form,
          child: ListView(
            padding: const .all(16),
            children: [
              const SectionTitle("Localidade acompanhada"),
              const SizedBox(height: 8),
              TextFormField(
                controller: _uf,
                maxLength: 2,
                textCapitalization: .characters,
                decoration: const InputDecoration(labelText: "UF", border: OutlineInputBorder(), counterText: ""),
                validator: (v) => (v == null || v.trim().length != 2) ? "Informe a sigla da UF (ex.: SP)" : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _municipality,
                decoration: const InputDecoration(labelText: "Município", border: OutlineInputBorder()),
                validator: (v) => (v == null || v.trim().isEmpty) ? "Informe o município" : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _district,
                decoration: const InputDecoration(
                  labelText: "Distrito (opcional)",
                  helperText: "Ex.: Itaquera, Penha, Sé",
                  border: OutlineInputBorder(),
                ),
              ),
              const SectionTitle("API"),
              const SizedBox(height: 8),
              TextFormField(
                controller: _host,
                autocorrect: false,
                keyboardType: .url,
                decoration: const InputDecoration(
                  labelText: "Endereço da API (host:porta)",
                  border: OutlineInputBorder(),
                ),
                validator: (v) => (v == null || v.trim().isEmpty) ? "Informe o endereço da API" : null,
              ),
              const SizedBox(height: 16),
              FilledButton.icon(onPressed: _save, icon: const Icon(Icons.save_outlined), label: const Text("Salvar")),
              const SizedBox(height: 16),
              const NoticeBanner(
                "Privacidade: o app não coleta dados pessoais. As preferências ficam apenas neste aparelho e os relatos são anônimos.",
                icon: Icons.lock_outline,
              ),
            ],
          ),
        );
      },
    );
  }
}
