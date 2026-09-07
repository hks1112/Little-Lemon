from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Djoser: handles /auth/users/ (register), /auth/users/me/, etc.
    path('auth/', include('djoser.urls')),
    # Djoser token auth: handles /auth/token/login/ and /auth/token/logout/
    path('auth/', include('djoser.urls.authtoken')),

    path('api/', include('LittleLemonAPI.urls')),
]
