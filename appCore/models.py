"""Database models for artists, profiles, and artworks.

Custom models extending Django's auth system and adding art-related data.
Source: Original custom implementation based on Django's auth models.
- CustomUser: Extends django.contrib.auth.models.AbstractUser
- ArtistProfile: Standard Django Model pattern
- Artwork: Standard Django Model pattern with ForeignKey
"""
from django.db import models
# Django's AbstractUser provides the base user model with authentication features
# Source: django.contrib.auth.models.AbstractUser
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class CustomUser(AbstractUser):
    """Custom user with a simple role flag."""
    ROLE_CHOICES = [
        ('visitor', 'Visitor'),
        ('artist', 'Artist'),
        ('admin', 'Admin'),
    ]
    # Role is used to gate artist-only UI/routes.
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='visitor')

    def __str__(self):
        return self.username

class ArtistProfile(models.Model):
    """Extended artist metadata shown on profile pages."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='artist_profile')
    bio = models.TextField(blank=True)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    # Stored in /media/profiles/
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Artwork(models.Model):
    """Artwork uploaded by an artist."""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    # Stored in /media/artworks/
    image = models.ImageField(upload_to='artworks/')
    artist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='artworks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
