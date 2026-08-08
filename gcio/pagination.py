from django.core.paginator import Paginator

PER_PAGE = 20


def paginate(request, queryset, per_page=PER_PAGE):
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    querydict = request.GET.copy()
    querydict.pop('page', None)
    base_qs = querydict.urlencode()

    return page_obj, base_qs
