from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from modules.roles.decorators import permission_required
from modules.users.activity import log_activity

from .models import AIGenerationDefaults, AIProviderConfig
from .testers import TESTERS

PROVIDER_FIELDS = {
    AIProviderConfig.PROVIDER_OPENAI: {'secondary_label': 'Organisation ID', 'model_placeholder': 'gpt-4o'},
    AIProviderConfig.PROVIDER_ANTHROPIC: {'secondary_label': 'API version', 'model_placeholder': 'claude-sonnet-4'},
    AIProviderConfig.PROVIDER_GEMINI: {'secondary_label': None, 'model_placeholder': 'gemini-2.0-flash'},
}


def _get_or_create_configs():
    configs = {}
    for provider, _label in AIProviderConfig.PROVIDER_CHOICES:
        config, _ = AIProviderConfig.objects.get_or_create(provider=provider)
        configs[provider] = config
    return configs


@permission_required('can_manage_roles')
def ai_integration_view(request):
    defaults = AIGenerationDefaults.load()

    if request.method == 'POST':
        configs = _get_or_create_configs()
        for provider, config in configs.items():
            new_key = request.POST.get(f'{provider}_api_key', '').strip()
            if new_key:
                config.api_key = new_key
                config.is_connected = False
                config.last_tested_at = None
            config.default_model = request.POST.get(f'{provider}_default_model', '').strip()
            config.secondary_field_value = request.POST.get(f'{provider}_secondary', '').strip()
            config.save()

        defaults.default_provider = request.POST.get('default_provider', defaults.default_provider)
        defaults.default_report_size = request.POST.get('default_report_size', defaults.default_report_size)
        try:
            defaults.temperature = float(request.POST.get('temperature', defaults.temperature))
        except ValueError:
            pass
        defaults.house_style_instructions = request.POST.get('house_style_instructions', '').strip()
        defaults.save()

        log_activity(request, 'updated AI integration settings')
        messages.success(request, 'AI integration settings were saved.')
        return redirect('ai_integration')

    configs = _get_or_create_configs()
    providers = []
    for provider, label in AIProviderConfig.PROVIDER_CHOICES:
        config = configs[provider]
        providers.append({
            'key': provider,
            'label': label,
            'config': config,
            'secondary_label': PROVIDER_FIELDS[provider]['secondary_label'],
            'model_placeholder': PROVIDER_FIELDS[provider]['model_placeholder'],
        })

    return render(request, 'ai_integration/settings.html', {
        'active_nav': 'ai_integration',
        'providers': providers,
        'defaults': defaults,
    })


@permission_required('can_manage_roles')
@require_POST
def test_connection(request, provider):
    config = get_object_or_404(AIProviderConfig, provider=provider)

    if not config.api_key:
        return JsonResponse({'connected': False, 'error': 'Save an API key for this provider first.'}, status=400)

    tester = TESTERS.get(provider)
    if not tester:
        return JsonResponse({'connected': False, 'error': 'Unknown provider.'}, status=400)

    connected, error = tester(config.api_key)
    config.is_connected = connected
    config.last_tested_at = timezone.now()
    config.save(update_fields=['is_connected', 'last_tested_at'])

    return JsonResponse({'connected': connected, 'error': error})
