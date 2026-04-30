"""URL routes for the appCore Django app.

Source: Original custom URL configuration.
Uses Django's built-in auth views.
"""
# Django's URL routing system
# Source: django.urls
from django.urls import path
# Django's built-in authentication views (LoginView, LogoutView)
# Source: django.contrib.auth.views
from django.contrib.auth import views as auth_views
from appCore import views

urlpatterns = [
    # Public pages
    path("", views.home, name="home"),
    path("appCore/<name>", views.homepage, name="homepage"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),

    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='appCore/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('register/', views.register, name='register'),

    # Portfolio URLs
    path('portfolio/', views.portfolio, name='portfolio'),
    path('artwork/<int:pk>/', views.artwork_detail, name='artwork_detail'),
    path('artwork/<int:pk>/delete/', views.delete_artwork, name='delete_artwork'),
    path('artist/edit/', views.edit_artist_profile, name='edit_artist_profile'),
    path('artist/<str:username>/', views.artist_profile, name='artist_profile'),
    path('upload/', views.upload_artwork, name='upload_artwork'),

# Artists page
    path('artists/', views.artists_listing, name='artists_listing'),
    path('api/artists/search/', views.artist_search_api, name='artist_search_api'),

# AI features
    path('ai/', views.ai_dashboard, name='ai_dashboard'),
    path('ai/collaboration/', views.ai_collaboration, name='ai_collaboration'),
    path('ai/compare/', views.ai_compare, name='ai_compare'),
    path('ai/search/', views.ai_candidate_search, name='ai_candidate_search'),
    path('ai/style/', views.ai_style_analysis, name='ai_style_analysis'),
    path('ai/style/<str:username>/', views.ai_style_analysis, name='ai_style_analysis'),
    # Artist dashboard
    path('dashboard/', views.artist_dashboard, name='artist_dashboard'),
]
