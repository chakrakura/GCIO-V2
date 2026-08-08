from django.db import models


class AIProviderConfig(models.Model):
    PROVIDER_OPENAI = 'openai'
    PROVIDER_ANTHROPIC = 'anthropic'
    PROVIDER_GEMINI = 'gemini'
    PROVIDER_CHOICES = [
        (PROVIDER_OPENAI, 'ChatGPT'),
        (PROVIDER_ANTHROPIC, 'Claude'),
        (PROVIDER_GEMINI, 'Gemini'),
    ]

    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, unique=True)
    api_key = models.CharField(max_length=255, blank=True)
    default_model = models.CharField(max_length=100, blank=True)
    # OpenAI: organisation ID. Anthropic: API version. Unused for Gemini.
    secondary_field_value = models.CharField(max_length=255, blank=True)
    is_connected = models.BooleanField(default=False)
    last_tested_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_provider_display()

    @property
    def masked_key(self):
        if not self.api_key:
            return ''
        if len(self.api_key) <= 8:
            return '•' * len(self.api_key)
        return f'{self.api_key[:5]}...{self.api_key[-4:]}'


class AIGenerationDefaults(models.Model):
    SIZE_SHORT = 'short'
    SIZE_STANDARD = 'standard'
    SIZE_DEEP = 'deep'
    SIZE_CHOICES = [
        (SIZE_SHORT, 'Short note · ~400 words · 2 pages'),
        (SIZE_STANDARD, 'Standard insight · ~900 words · 5 pages'),
        (SIZE_DEEP, 'Deep dive · ~2000 words · 10 pages'),
    ]

    default_provider = models.CharField(
        max_length=20, choices=AIProviderConfig.PROVIDER_CHOICES, default=AIProviderConfig.PROVIDER_GEMINI
    )
    default_report_size = models.CharField(max_length=20, choices=SIZE_CHOICES, default=SIZE_STANDARD)
    temperature = models.FloatField(default=0.4)
    house_style_instructions = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'AI generation defaults'
        verbose_name_plural = 'AI generation defaults'

    def __str__(self):
        return 'AI generation defaults'

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
