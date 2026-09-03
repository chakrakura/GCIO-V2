class NoCacheForAuthenticatedMiddleware:
    """Stop browsers from serving a cached/back-button copy of an authenticated page
    after logout. Without this, the server-side login_required redirect is correct on
    a fresh request, but pressing Back can still repaint a page from the browser's
    cache without ever re-requesting it.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response['Pragma'] = 'no-cache'
        return response
