from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from modules.roles.decorators import permission_required
from modules.users.activity import log_activity

from .models import MarketInstrument
from .services import refresh_all_instruments, refresh_instrument


@permission_required('can_manage_market_data')
def market_data_view(request):
    instruments = MarketInstrument.objects.all()
    return render(request, 'market_data/market_data.html', {
        'active_nav': 'market_data',
        'instruments': instruments,
    })


@permission_required('can_manage_market_data')
def market_data_refresh_all(request):
    if request.method == 'POST':
        results = refresh_all_instruments(MarketInstrument.objects.filter(is_active=True))
        ok_count = sum(1 for _, ok, _ in results if ok)
        log_activity(request, 'refreshed market data', f'{ok_count}/{len(results)} instruments')
        if ok_count == len(results):
            messages.success(request, f'Refreshed all {ok_count} instruments from Yahoo Finance.')
        else:
            failed = [inst.label for inst, ok, _ in results if not ok]
            messages.error(request, f'Refreshed {ok_count}/{len(results)}. Failed: {", ".join(failed)}.')
    return redirect('market_data')


@permission_required('can_manage_market_data')
def market_data_refresh_one(request, instrument_id):
    instrument = get_object_or_404(MarketInstrument, pk=instrument_id)
    if request.method == 'POST':
        ok, message = refresh_instrument(instrument)
        log_activity(request, 'refreshed market instrument', instrument.label)
        if ok:
            messages.success(request, f'{instrument.label} updated: {instrument.formatted_value}')
        else:
            messages.error(request, f'{instrument.label} failed: {message}')
    return redirect('market_data')


@permission_required('can_manage_market_data')
def market_data_toggle(request, instrument_id, field):
    if field not in ('is_active', 'is_hero_stat'):
        return redirect('market_data')
    instrument = get_object_or_404(MarketInstrument, pk=instrument_id)
    if request.method == 'POST':
        setattr(instrument, field, not getattr(instrument, field))
        instrument.save(update_fields=[field])
        log_activity(request, f'toggled {field}', instrument.label)
    return redirect('market_data')
