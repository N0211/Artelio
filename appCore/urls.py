from django.urls import path
from django.contrib.auth import views as auth_views
from appCore import views

urlpatterns = [
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
    path('artist/<str:username>/', views.artist_profile, name='artist_profile'),
    path('upload/', views.upload_artwork, name='upload_artwork'),

    # AI features
    path('ai/', views.ai_dashboard, name='ai_dashboard'),
    path('ai/collaboration/', views.ai_collaboration, name='ai_collaboration'),
    path('ai/compare/', views.ai_compare, name='ai_compare'),
    path('ai/search/', views.ai_candidate_search, name='ai_candidate_search'),
    path('dashboard/', views.artist_dashboard, name='artist_dashboard'),
]
