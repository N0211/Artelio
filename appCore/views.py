"""View handlers for the Artelio app (pages + AI tools).

Source: Original custom Django views.
All code is custom implementation - no adapted code in this file.
Uses standard Django shortcuts, decorators, and ORM patterns.
"""
# Django's timezone utility
# Source: django.utils.timezone
from django.utils.timezone import datetime
# Django's HTTP response classes
# Source: django.http
from django.http import HttpResponse, JsonResponse
# Django's shortcut functions (render, redirect, get_object_or_404)
# Source: django.shortcuts
from django.shortcuts import render, redirect, get_object_or_404
# Django's authentication functions
# Source: django.contrib.auth
from django.contrib.auth import login, logout, authenticate
# Django's login_required decorator
# Source: django.contrib.auth.decorators
from django.contrib.auth.decorators import login_required
# Django's messaging framework
# Source: django.contrib.messages
from django.contrib import messages
# Django's require_POST decorator
# Source: django.views.decorators.http
from django.views.decorators.http import require_POST
# Django's settings configuration
# Source: django.conf.settings
from django.conf import settings
# Django's URL validation utility
# Source: django.utils.http
from django.utils.http import url_has_allowed_host_and_scheme
from .models import Artwork, ArtistProfile, CustomUser
from .forms import ArtistProfileForm, UserRegistrationForm
from .ai_utils import (
    compare_artists,
    suggest_collaboration,
    analyze_style,
    search_candidates
)


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
def artists_listing(request):
    """Page showing featured/trending artists with search functionality."""
    query = request.GET.get('q', '').strip()
    
    if query:
        # Search artists by username
        artists = CustomUser.objects.filter(role='artist', username__icontains=query)[:10]
    else:
        # Get trending artists (those with most artworks)
        from django.db.models import Count
        artists = list(CustomUser.objects.filter(role='artist').annotate(
            artwork_count=Count('artworks')
        ).order_by('-artwork_count')[:10])
        
        # If no artists with artworks, get any artists
        if not artists:
            artists = list(CustomUser.objects.filter(role='artist')[:10])
    
    # Get featured (hardcoded for now - could be made dynamic)
    featured_artists = ["artist_one", "artist_two"]
    featured = []
    for username in featured_artists:
        try:
            user = CustomUser.objects.get(username=username)
            artwork_count = Artwork.objects.filter(artist=user).count()
            profile = getattr(user, 'artist_profile', None)
            featured.append({
                'user': user,
                'artwork_count': artwork_count,
                'profile': profile
            })
        except CustomUser.DoesNotExist:
            pass
    
    return render(request, 'appCore/artists_listing.html', {
        'artists': artists,
        'featured': featured,
        'query': query
    })


@login_required
def artist_search_api(request):
    """AJAX API for artist search with autocomplete."""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 1:
        return JsonResponse({'results': []})
    
    # Search artists by username (case-insensitive)
    artists = CustomUser.objects.filter(
        role='artist', 
        username__icontains=query
    )[:5]
    
    results = []
    for artist in artists:
        profile = getattr(artist, 'artist_profile', None)
        results.append({
            'username': artist.username,
            'bio': profile.bio if profile and profile.bio else '',
            'artwork_count': Artwork.objects.filter(artist=artist).count()
        })
    
    return JsonResponse({'results': results})


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
    
    # AI-generated style analysis (fallback to defaults if no artworks)
    mood_tags = ["Vibrant", "Serene", "Dreamlike", "Dynamic"]
    style_descriptors = ["High Contrast", "Fluid Motion", "Textured Layers"]
    palette = ["#24445f", "#ff6f61", "#f5f2ea", "#4cc9f0", "#f7b500"]
    ai_style_analysis = None
    
    # Only analyze if artist has artworks
    if artworks and len(artworks) > 0:
        artwork_titles = [a.title for a in artworks]
        artwork_descriptions = ' | '.join([a.description if a.description else a.title for a in artworks[:5]])
        
        # Try to get AI analysis
        ai_response = analyze_style(artwork_titles, artwork_descriptions)
        
        if ai_response:
            # Parse AI response for tags and palette
            ai_style_analysis = {}
            for line in ai_response.split('\n'):
                if line.startswith('DOMINANT_STYLE:'):
                    style = line.replace('DOMINANT_STYLE:', '').strip()
                    ai_style_analysis['dominant_style'] = style
                    # Generate style descriptors from the analysis
                    if 'abstract' in style.lower():
                        style_descriptors = ["Abstract Forms", "Fluid Motion", "Expressive", "Experimental"]
                    elif 'digital' in style.lower():
                        style_descriptors = ["Digital Art", "Pixel Perfect", "Modern Tech", "Clean Lines"]
                    elif 'traditional' in style.lower():
                        style_descriptors = ["Classical", "Detailed", "Time-Honored", "Brushwork"]
                    elif 'realistic' in style.lower():
                        style_descriptors = ["True to Life", "High Detail", "Natural", "Photographic"]
                    else:
                        style_descriptors = [style, "Distinctive", "Original", "Polished"]
                elif line.startswith('COLOR_TENDENCIES:'):
                    colors = line.replace('COLOR_TENDENCIES:', '').strip()
                    ai_style_analysis['color_tendencies'] = colors
                    # Generate palette from color description
                    if 'warm' in colors.lower():
                        palette = ["#ff6f61", "#f7b500", "#ff9a8b", "#ffb347", "#e85d04"]
                    elif 'cool' in colors.lower():
                        palette = ["#4cc9f0", "#24445f", "#0077b6", "#90e0ef", "#48cae4"]
                    elif 'vibrant' in colors.lower() or 'bright' in colors.lower():
                        palette = ["#ff006e", "#8338ec", "#3a86ff", "#fb5607", "#ffbe0b"]
                    elif 'pastel' in colors.lower():
                        palette = ["#ffc6ff", "#fffffc", "#a0c4ff", "#bdb2ff", "#fdffb6"]
                    elif 'dark' in colors.lower() or 'moody' in colors.lower():
                        palette = ["#1a1a2e", "#16213e", "#0f3460", "#533483", "#e94560"]
                elif line.startswith('MOOD_THEME:'):
                    mood_theme = line.replace('MOOD_THEME:', '').strip()
                    ai_style_analysis['mood_theme'] = mood_theme
                    # Generate mood tags from the analysis
                    if 'serene' in mood_theme.lower() or 'calm' in mood_theme.lower():
                        mood_tags = ["Serene", "Peaceful", "Tranquil", "Harmonious"]
                    elif 'dynamic' in mood_theme.lower() or 'energetic' in mood_theme.lower():
                        mood_tags = ["Dynamic", "Energetic", "Bold", "Vibrant"]
                    elif 'dreamlike' in mood_theme.lower() or 'fantasy' in mood_theme.lower():
                        mood_tags = ["Dreamlike", "Ethereal", "Magical", "Imaginative"]
                    elif 'melancholy' in mood_theme.lower() or 'sad' in mood_theme.lower():
                        mood_tags = ["Contemplative", "Introspective", "Nostalgic", "Poignant"]
                    else:
                        mood_tags = mood_theme.split(',')[:4] if ',' in mood_theme else [mood_theme, "Expressive", "Artistic", "Contemporary"]
    
    context = {
        'is_artist': is_artist,
        'artwork_count': Artwork.objects.filter(artist=request.user).count() if is_artist else 0,
        'profile': profile,
        'artworks': artworks,
        'past_updated_artworks': past_updated_artworks,
        'mood_tags': mood_tags,
        'style_descriptors': style_descriptors,
        'palette': palette,
        'ai_style_analysis': ai_style_analysis,
    }
    return render(request, 'appCore/artist_dashboard.html', context)





@login_required
def ai_collaboration(request):
    """AI tool: suggest a collaborator and joint idea."""
    artists = CustomUser.objects.filter(role='artist')
    context = {'artists': artists}
    if request.method == 'POST':
        primary_artist = request.POST.get('primary_artist')
        goal = request.POST.get('goal', '').strip()
        collaborator_name = request.POST.get('collaborator_name', '')
        
        # Get collaborator bio if selected
        collaborator_bio = ""
        if collaborator_name:
            try:
                collab_user = CustomUser.objects.get(username=collaborator_name)
                if hasattr(collab_user, 'artist_profile'):
                    collaborator_bio = collab_user.artist_profile.bio
            except CustomUser.DoesNotExist:
                pass
        
        # Get primary artist bio
        primary_bio = ""
        try:
            primary_user = CustomUser.objects.get(username=primary_artist)
            if hasattr(primary_user, 'artist_profile'):
                primary_bio = primary_user.artist_profile.bio
        except CustomUser.DoesNotExist:
            pass
        
        # Call AI function
        ai_response = suggest_collaboration(primary_artist, goal, collaborator_name, collaborator_bio)
        
        if ai_response:
            # Parse the AI response
            result = {'raw_response': ai_response}
            for line in ai_response.split('\n'):
                if line.startswith('RATIONALE:'):
                    result['rationale'] = line.replace('RATIONALE:', '').strip()
                elif line.startswith('IDEA:'):
                    result['collaboration_idea'] = line.replace('IDEA:', '').strip()
                elif line.startswith('STRENGTHS:'):
                    strengths = line.replace('STRENGTHS:', '').strip()
                    result['complementary_strengths'] = [s.strip() for s in strengths.split('|') if s.strip()]
            
            # Set default values if not found
            if 'rationale' not in result:
                result['rationale'] = 'Analysis generated based on artist profiles.'
            if 'collaboration_idea' not in result:
                result['collaboration_idea'] = 'Consider exploring collaborative themes.'
            if 'complementary_strengths' not in result:
                result['complementary_strengths'] = ['Creativity', 'Technical skill', 'Artistic vision']
            
            result['collaborator_username'] = collaborator_name or 'AI-suggested'
            context['result'] = result
        else:
            context['error'] = 'Unable to generate collaboration suggestion. Please check your API key.'

    return render(request, 'appCore/ai_collab.html', context)


@login_required
def ai_compare(request):
    """AI tool: compare two artists."""
    artists = CustomUser.objects.filter(role='artist')
    context = {'artists': artists}
    if request.method == 'POST':
        artist_a = request.POST.get('artist_a')
        artist_b = request.POST.get('artist_b')

        # Get artist bios
        artist_a_bio = ""
        artist_b_bio = ""
        
        try:
            user_a = CustomUser.objects.get(username=artist_a)
            if hasattr(user_a, 'artist_profile'):
                artist_a_bio = user_a.artist_profile.bio
        except CustomUser.DoesNotExist:
            pass
        
        try:
            user_b = CustomUser.objects.get(username=artist_b)
            if hasattr(user_b, 'artist_profile'):
                artist_b_bio = user_b.artist_profile.bio
        except CustomUser.DoesNotExist:
            pass
        
        # Call AI function
        ai_response = compare_artists(artist_a, artist_b, artist_a_bio, artist_b_bio)
        
        if ai_response:
            # Parse the AI response
            result = {'raw_response': ai_response}
            for line in ai_response.split('\n'):
                if line.startswith('SIMILARITIES:'):
                    similarities = line.replace('SIMILARITIES:', '').strip()
                    result['similarities'] = [s.strip() for s in similarities.split('|') if s.strip()]
                elif line.startswith('DIFFERENCES:'):
                    differences = line.replace('DIFFERENCES:', '').strip()
                    result['differences'] = [d.strip() for d in differences.split('|') if d.strip()]
                elif line.startswith('RECOMMENDATION:'):
                    result['recommendation'] = line.replace('RECOMMENDATION:', '').strip()
            
            # Set default values if not found
            if 'similarities' not in result:
                result['similarities'] = ['Both work in digital media']
            if 'differences' not in result:
                result['differences'] = ['Unique styles']
            if 'recommendation' not in result:
                result['recommendation'] = 'Consider a collaborative project.'
            
            context['result'] = result
        else:
            context['error'] = 'Unable to generate comparison. Please check your API key.'

    return render(request, 'appCore/ai_compare.html', context)


@login_required
def ai_candidate_search(request):
    """AI tool: rank artists for a project brief."""
    artists = CustomUser.objects.filter(role='artist')
    context = {'artists': artists}
    if request.method == 'POST':
        brief = request.POST.get('brief', '').strip()

        # Build artists data from database
        artists_data = []
        for artist in artists:
            artist_info = f"Artist: {artist.username}"
            if hasattr(artist, 'artist_profile'):
                profile = artist.artist_profile
                if profile.bio:
                    artist_info += f", Bio: {profile.bio}"
                # Get artwork titles
                artworks = Artwork.objects.filter(artist=artist)[:5]
                if artworks:
                    artwork_titles = ', '.join([a.title for a in artworks])
                    artist_info += f", Artworks: {artwork_titles}"
            artists_data.append(artist_info)
        
        artists_summary = '\n'.join(artists_data)
        
        # Call AI function
        ai_response = search_candidates(brief, artists_summary)
        
        if ai_response and 'results' in ai_response:
            context['result'] = ai_response
        else:
            # Try to parse error message
            if ai_response and 'error' in ai_response:
                context['error'] = ai_response['error']
            else:
                context['error'] = 'Unable to generate candidate rankings. Please check your API key.'
        
        context['brief'] = brief

    return render(request, 'appCore/ai_search.html', context)


@login_required
def ai_style_analysis(request, username=None):
    """AI tool: analyze an artist's style based on their artworks."""
    if username:
        # Analyze specific artist's style
        try:
            artist = CustomUser.objects.get(username=username)
            artworks = Artwork.objects.filter(artist=artist)
            artwork_titles = [a.title for a in artworks]
            artwork_descriptions = ' | '.join([a.description if a.description else a.title for a in artworks])
            
            # Call AI function
            ai_response = analyze_style(artwork_titles, artwork_descriptions)
            
            context = {'artist': artist, 'username': username}
            if ai_response:
                # Parse the AI response
                result = {'raw_response': ai_response}
                for line in ai_response.split('\n'):
                    if line.startswith('DOMINANT_STYLE:'):
                        result['dominant_style'] = line.replace('DOMINANT_STYLE:', '').strip()
                    elif line.startswith('COLOR_TENDENCIES:'):
                        result['color_tendencies'] = line.replace('COLOR_TENDENCIES:', '').strip()
                    elif line.startswith('MOOD_THEME:'):
                        result['mood_theme'] = line.replace('MOOD_THEME:', '').strip()
                    elif line.startswith('TECHNICAL_STRENGTHS:'):
                        result['technical_strengths'] = line.replace('TECHNICAL_STRENGTHS:', '').strip()
                    elif line.startswith('RECOMMENDATIONS:'):
                        result['recommendations'] = line.replace('RECOMMENDATIONS:', '').strip()
                
                # Set default values
                if 'dominant_style' not in result:
                    result['dominant_style'] = 'Digital art style'
                if 'color_tendencies' not in result:
                    result['color_tendencies'] = 'Varied color palette'
                if 'mood_theme' not in result:
                    result['mood_theme'] = 'Contemporary themes'
                if 'technical_strengths' not in result:
                    result['technical_strengths'] = 'Strong digital skills'
                if 'recommendations' not in result:
                    result['recommendations'] = 'Continue developing unique style'
                
                context['result'] = result
            else:
                context['error'] = 'Unable to analyze style. Please check your API key.'
            
            return render(request, 'appCore/ai_style_analysis.html', context)
        except CustomUser.DoesNotExist:
            messages.error(request, 'Artist not found.')
            return redirect('ai_dashboard')
    else:
        # Show form to select artist
        artists = CustomUser.objects.filter(role='artist')
        return render(request, 'appCore/ai_style_analysis.html', {'artists': artists})
