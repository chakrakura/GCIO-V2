from django.core.management.base import BaseCommand

from modules.market_data.models import MarketInstrument
from modules.market_data.services import refresh_all_instruments


class Command(BaseCommand):
    help = 'Refresh all active market instruments from Yahoo Finance. Intended to be run on a schedule (cron).'

    def handle(self, *args, **options):
        instruments = MarketInstrument.objects.filter(is_active=True)
        results = refresh_all_instruments(instruments)

        ok_count = sum(1 for _, ok, _ in results if ok)
        for instrument, ok, message in results:
            if ok:
                self.stdout.write(self.style.SUCCESS(f'{instrument.symbol}: {instrument.formatted_value}'))
            else:
                self.stdout.write(self.style.ERROR(f'{instrument.symbol}: {message}'))

        self.stdout.write(f'Refreshed {ok_count}/{len(results)} instruments.')
