"""
URL configuration for Insight project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import include, path
from django.conf.urls import url
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    # User authentication views
    path('register/', views.register, name='register'),
    path('login/', views.login_request, name='login'),
    path('logout/', views.logout_request, name='logout'),

    # Post-related views
    path('post/create/', views.create_post, name='create_post'),
    path('post/update/<int:pk>/', views.update_post, name='update_post'),
    path('post/delete/<int:pk>/', views.delete_post, name='delete_post'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),

    # Comment-related views
    path('post/<int:post_id>/comment/update/<int:comment_id>/', views.update_comment, name='update_comment'),
    path('post/<int:post_id>/comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),

    # Reaction toggle view
    path('reaction/toggle/', views.toggle_reaction, name='toggle_reaction'),
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
]

