"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
# from django.contrib import admin
# from django.urls import path

# urlpatterns = [
#    path('admin/', admin.site.urls),
#]

from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

from lacarta import auth0

urlpatterns = [
    path('', RedirectView.as_view(url='/admin/', permanent=False)),

    # Login y logout del admin por Auth0. Van ANTES de admin.site.urls para que
    # Django use estas vistas en lugar del formulario de usuario y contraseña.
    path('admin/login/', auth0.iniciar_sesion, name='auth0_login'),
    path('admin/logout/', auth0.cerrar_sesion, name='auth0_logout'),
    path('auth/callback/', auth0.callback, name='auth0_callback'),
    # Sin contraseñas en Django: "Cambiar contraseña" del admin no tiene sentido
    path('admin/password_change/', RedirectView.as_view(url='/admin/', permanent=False)),

    path('admin/', admin.site.urls),
]