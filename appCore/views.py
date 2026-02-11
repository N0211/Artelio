"""View handlers for the Artelio app (pages + AI tools)."""
from django.utils.timezone import datetime
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme
from .models import Artwork, ArtistProfile, CustomUser
from .forms import ArtistProfileForm, UserRegistrationForm


def home(request):
    """Home page with a small featured artwork strip."""
    featured_artworks = Artwork.objects.all()[:8]
    return render(request, 'appCore/home.html', {'featured_artworks': featured_artworks})

def homepage(request, name):
    # Debug helper: current full URL.
    print(request.build_absolute_uri())  # optional
    return render(
        request,
        'appCore/homepage.html',
        {
            'name': name,
            'date': datetime.now()
        }
    )

def about(request):
    """Static about page."""
    return render(request, 'appCore/about.html')

def contact(request):
    """Static contact page."""
    return render(request, 'appCore/contact.html')

def register(request):
    """User signup with custom role selection."""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'appCore/register.html', {'form': form})

def user_login(request):
    """Manual login handler (unused if LoginView is configured)."""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'appCore/login.html')

def user_logout(request):
    """Logout then return home."""
    logout(request)
    return redirect('home')

@login_required
def portfolio(request):
    """Public gallery of all artworks."""
    artworks = Artwork.objects.all()
    return render(request, 'appCore/portfolio.html', {'artworks': artworks})

@login_required
def artwork_detail(request, pk):
    """Single artwork detail page."""
    artwork = Artwork.objects.get(pk=pk)
    return render(request, 'appCore/artwork_detail.html', {'artwork': artwork})

@login_required
def artist_profile(request, username):
    """Artist bio + gallery page."""
    user = CustomUser.objects.get(username=username)
    profile = ArtistProfile.objects.get(user=user)
    artworks = list(Artwork.objects.filter(artist=user).order_by('-updated_at', '-created_at'))
    past_updated_artworks = artworks[1:] if artworks else []
    # Demo tags/palette for the prototype UI.
    mood_tags = ["Vibrant", "Serene", "Dreamlike", "Dynamic"]
    style_descriptors = ["High Contrast", "Fluid Motion", "Textured Layers"]
    palette = ["#24445f", "#ff6f61", "#f5f2ea", "#4cc9f0", "#f7b500"]
    return render(
        request,
        'appCore/artist_profile.html',
        {
            'profile': profile,
            'artworks': artworks,
            'past_updated_artworks': past_updated_artworks,
            'mood_tags': mood_tags,
            'style_descriptors': style_descriptors,
            'palette': palette,
        }
    )


@login_required
def edit_artist_profile(request):
    """Profile editor for the logged-in artist."""
    profile, _ = ArtistProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ArtistProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            request.user.email = form.cleaned_data['email']
            request.user.save(update_fields=['email'])
            messages.success(request, 'Profile updated successfully!')
            return redirect('artist_dashboard')
    else:
        form = ArtistProfileForm(instance=profile, user=request.user)
    return render(request, 'appCore/artist_profile_edit.html', {'form': form})

@login_required
def upload_artwork(request):
    """Artwork upload form for artists."""
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST.get('description', '')
        image = request.FILES['image']
        artwork = Artwork.objects.create(
            title=title,
            description=description,
            image=image,
            artist=request.user
        )
        messages.success(request, 'Artwork uploaded successfully!')
        return redirect('portfolio')
    return render(request, 'appCore/upload_artwork.html')


@login_required
@require_POST
def delete_artwork(request, pk):
    """Delete an artwork owned by the logged-in user."""
    artwork = get_object_or_404(Artwork, pk=pk, artist=request.user)
    next_url = request.POST.get('next', '')
    if not url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = ''
    if artwork.image:
        artwork.image.delete(save=False)
    artwork.delete()
    messages.success(request, 'Artwork removed successfully!')
    if next_url:
        return redirect(next_url)
    return redirect('artist_dashboard')


@login_required
def ai_dashboard(request):
    """Landing page for AI tools."""
    return render(request, 'appCore/ai_dashboard.html')


@login_required
def artist_dashboard(request):
    """Artist dashboard with profile summary and gallery."""
    is_artist = getattr(request.user, 'role', '') == 'artist'
    profile = ArtistProfile.objects.filter(user=request.user).first()
    artworks = list(Artwork.objects.filter(artist=request.user).order_by('-updated_at', '-created_at'))
    past_updated_artworks = artworks[1:] if artworks else []
    # Demo tags/palette for the prototype UI.
    mood_tags = ["Vibrant", "Serene", "Dreamlike", "Dynamic"]
    style_descriptors = ["High Contrast", "Fluid Motion", "Textured Layers"]
    palette = ["#24445f", "#ff6f61", "#f5f2ea", "#4cc9f0", "#f7b500"]
    context = {
        'is_artist': is_artist,
        'artwork_count': Artwork.objects.filter(artist=request.user).count() if is_artist else 0,
        'profile': profile,
        'artworks': artworks,
        'past_updated_artworks': past_updated_artworks,
        'mood_tags': mood_tags,
        'style_descriptors': style_descriptors,
        'palette': palette,
    }
    return render(request, 'appCore/artist_dashboard.html', context)





@login_required
def ai_collaboration(request):
    """AI tool: suggest a collaborator and joint idea."""
    artists = CustomUser.objects.filter(role='artist')
    context = {'artists': artists}
    if request.method == 'POST':
        primary = request.POST.get('primary_artist')
        goal = request.POST.get('goal', '').strip()

        # Mock AI response for collaboration suggestion
        mock_result = {
            'collaborator_username': 'artist_two',
            'rationale': 'Artist Two\'s realistic portrait style would complement Artist One\'s abstract compositions, creating a dynamic visual dialogue.',
            'collaboration_idea': 'Create a series of "Dual Perspectives" artworks where each piece features both abstract and realistic elements, exploring how different artistic approaches can represent the same concept.',
            'complementary_strengths': [
                'Technical precision in realistic rendering',
                'Innovative abstract concept development',
                'Shared passion for contemporary themes',
                'Complementary color theory approaches'
            ]
        }
        context['result'] = mock_result

    return render(request, 'appCore/ai_collab.html', context)


@login_required
def ai_compare(request):
    """AI tool: compare two artists."""
    artists = CustomUser.objects.filter(role='artist')
    context = {'artists': artists}
    if request.method == 'POST':
        artist_a = request.POST.get('artist_a')
        artist_b = request.POST.get('artist_b')

        # Mock AI response for artist comparison
        mock_result = {
            'similarities': [
                'Both artists work primarily with digital media',
                'Shared interest in vibrant color palettes',
                'Focus on contemporary themes and cute digital aesthetics'
            ],
            'differences': [
                'Artist A specializes in soft yet detailed colors and palettes, while artist B focuses on a cutesy type of pixel art',
                'Artist A uses more experimental techniques, Artist B focuses on pixel details on their artworks',
                'Different target audiences: Artist A appeals to modern art collectors, Artist B artwork can be more targeted for pixel art games and such'
            ],
            'recommendation': 'For a collaborative project, consider combining Artist A\'s innovative abstract elements with Artist B\'s detail to precision for a unique fusion of styles of big pixel artworks.'
        }
        context['result'] = mock_result

    return render(request, 'appCore/ai_compare.html', context)


@login_required
def ai_candidate_search(request):
    """AI tool: rank artists for a project brief."""
    artists = CustomUser.objects.filter(role='artist')
    context = {'artists': artists}
    if request.method == 'POST':
        brief = request.POST.get('brief', '').strip()

        # Mock AI response for candidate search
        mock_result = {
            'results': [
                {
                    'username': 'artist_one',
                    'score': 9.2,
                    'reason': 'Exceptional digital painting skills with a portfolio perfectly matching the fantasy art style requirements.'
                },
                {
                    'username': 'artist_two',
                    'score': 8.7,
                    'reason': 'Strong background in character design and illustration, with proven commercial experience.'
                },
                {
                    'username': 'artist_three',
                    'score': 7.9,
                    'reason': 'Talented concept artist with innovative approaches to world-building and atmospheric scenes.'
                }
            ]
        }
        context['result'] = mock_result
        context['brief'] = brief

    return render(request, 'appCore/ai_search.html', context)
