"""Django admin configuration for the appCore models.

Source: Standard Django admin registration using django.contrib.admin.
No custom/adopted code - uses standard Django ModelAdmin patterns.
"""
from django.contrib import admin
# Django admin provides the admin interface for managing models
# Source: django.contrib.admin
from django.db import connection
from .models import CustomUser, ArtistProfile, Artwork


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_active')
    list_filter = ('role', 'is_active')


@admin.register(ArtistProfile)
class ArtistProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'website')


@admin.register(Artwork)
class ArtworkAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'created_at')
    list_filter = ('artist', 'created_at')
