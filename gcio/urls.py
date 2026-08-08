"""
URL configuration for gcio project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('modules.users.urls')),
    path('dashboard/', include('modules.dashboard.urls')),
    path('roles/', include('modules.roles.urls')),
    path('organizations/', include('modules.organizations.urls')),
    path('taxonomy/', include('modules.taxonomy.urls')),
    path('reports/', include('modules.reports.urls')),
    path('ai-integration/', include('modules.ai_integration.urls')),
    path('market-data/', include('modules.market_data.urls')),
    path('portal/', include('modules.client_portal.urls')),
    path('', include('modules.login.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
