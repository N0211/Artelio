import json
import re
import urllib.request
from django.utils.timezone import datetime
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .models import Artwork, ArtistProfile, CustomUser
from .forms import UserRegistrationForm


def home(request):
    featured_artworks = Artwork.objects.all()[:8]
    return render(request, 'appCore/home.html', {'featured_artworks': featured_artworks})

def homepage(request, name):
    print(request.build_absolute_uri()) #optional
    return render(
        request,
        'appCore/homepage.html',
        {
            'name': name,
            'date': datetime.now()
        }
    )

def about(request):
    return render(request, 'appCore/about.html')

def contact(request):
    return render(request, 'appCore/contact.html')

def register(request):
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
    logout(request)
    return redirect('home')

@login_required
def portfolio(request):
    artworks = Artwork.objects.all()
    return render(request, 'appCore/portfolio.html', {'artworks': artworks})

@login_required
def artwork_detail(request, pk):
    artwork = Artwork.objects.get(pk=pk)
    return render(request, 'appCore/artwork_detail.html', {'artwork': artwork})

@login_required
def artist_profile(request, username):
    user = CustomUser.objects.get(username=username)
    profile = ArtistProfile.objects.get(user=user)
    artworks = Artwork.objects.filter(artist=user)
    return render(request, 'appCore/artist_profile.html', {'profile': profile, 'artworks': artworks})

@login_required
def upload_artwork(request):
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
def ai_dashboard(request):
    return render(request, 'appCore/ai_dashboard.html')


@login_required
def artist_dashboard(request):
    is_artist = getattr(request.user, 'role', '') == 'artist'
    context = {
        'is_artist': is_artist,
        'artwork_count': Artwork.objects.filter(artist=request.user).count() if is_artist else 0,
    }
    return render(request, 'appCore/artist_dashboard.html', context)


def _collect_artist_summaries():
    artists = (
        CustomUser.objects
        .filter(role='artist')
        .prefetch_related('artworks')
    )
    summaries = []
    for artist in artists:
        profile = getattr(artist, 'artist_profile', None)
        bio = profile.bio if profile else ''
        website = profile.website if profile else ''
        artworks = artist.artworks.all()
        art_lines = []
        for art in artworks:
            description = (art.description or '').strip()
            if len(description) > 200:
                description = f"{description[:200]}..."
            art_lines.append(f"- {art.title}: {description}")
        summaries.append({
            'username': artist.username,
            'bio': bio,
            'website': website,
            'artworks': art_lines,
        })
    return summaries


def _openai_responses_call(input_text, schema=None):
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise RuntimeError('OPENAI_API_KEY is not set.')

    payload = {
        'model': 'gpt-4o-mini',
        'input': input_text,
    }
    if schema:
        payload['text'] = {'format': schema}

    request = urllib.request.Request(
        'https://api.openai.com/v1/responses',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    with urllib.request.urlopen(request, timeout=40) as response:
        body = response.read().decode('utf-8')

    data = json.loads(body)
    text_parts = []
    for item in data.get('output', []):
        if item.get('type') == 'message':
            for content in item.get('content', []):
                if content.get('type') == 'output_text':
                    text_parts.append(content.get('text', ''))
    return ''.join(text_parts).strip(), data


@login_required
def ai_collaboration(request):
    artists = CustomUser.objects.filter(role='artist')
    context = {'artists': artists}
    if request.method == 'POST':
        primary = request.POST.get('primary_artist')
        goal = request.POST.get('goal', '').strip()
        summaries = _collect_artist_summaries()
        if not summaries:
            messages.error(request, 'No artists found to analyze.')
            return render(request, 'appCore/ai_collab.html', context)

        prompt = (
            "You are helping with an AI Artist Collaboration feature. "
            "Pick the best collaborator for the selected artist and propose a joint idea.\n\n"
            f"Selected artist: {primary}\n"
            f"Collaboration goal: {goal or 'Not specified'}\n\n"
            "Artist data:\n"
        )
        for summary in summaries:
            prompt += (
                f"Artist: {summary['username']}\n"
                f"Bio: {summary['bio']}\n"
                f"Website: {summary['website']}\n"
                "Artworks:\n" + "\n".join(summary['artworks'] or ["- (no artworks)"]) + "\n\n"
            )

        schema = {
            'type': 'json_schema',
            'name': 'collaboration',
            'strict': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'collaborator_username': {'type': 'string'},
                    'rationale': {'type': 'string'},
                    'collaboration_idea': {'type': 'string'},
                    'complementary_strengths': {
                        'type': 'array',
                        'items': {'type': 'string'}
                    },
                },
                'required': [
                    'collaborator_username',
                    'rationale',
                    'collaboration_idea',
                    'complementary_strengths'
                ],
                'additionalProperties': False,
            }
        }

        try:
            result_text, _ = _openai_responses_call(prompt, schema=schema)
            context['result'] = json.loads(result_text) if result_text else None
        except Exception as exc:
            context['error'] = str(exc)

    return render(request, 'appCore/ai_collab.html', context)


@login_required
def ai_compare(request):
    artists = CustomUser.objects.filter(role='artist')
    context = {'artists': artists}
    if request.method == 'POST':
        artist_a = request.POST.get('artist_a')
        artist_b = request.POST.get('artist_b')
        summaries = _collect_artist_summaries()
        if not summaries:
            messages.error(request, 'No artists found to analyze.')
            return render(request, 'appCore/ai_compare.html', context)

        prompt = (
            "You are an AI Artist Comparison tool. Compare the two artists and provide "
            "similarities, differences, and a short recommendation.\n\n"
            f"Artist A: {artist_a}\n"
            f"Artist B: {artist_b}\n\n"
            "Artist data:\n"
        )
        for summary in summaries:
            prompt += (
                f"Artist: {summary['username']}\n"
                f"Bio: {summary['bio']}\n"
                f"Website: {summary['website']}\n"
                "Artworks:\n" + "\n".join(summary['artworks'] or ["- (no artworks)"]) + "\n\n"
            )

        schema = {
            'type': 'json_schema',
            'name': 'comparison',
            'strict': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'similarities': {'type': 'array', 'items': {'type': 'string'}},
                    'differences': {'type': 'array', 'items': {'type': 'string'}},
                    'recommendation': {'type': 'string'},
                },
                'required': ['similarities', 'differences', 'recommendation'],
                'additionalProperties': False,
            }
        }

        try:
            result_text, _ = _openai_responses_call(prompt, schema=schema)
            context['result'] = json.loads(result_text) if result_text else None
        except Exception as exc:
            context['error'] = str(exc)

    return render(request, 'appCore/ai_compare.html', context)


@login_required
def ai_candidate_search(request):
    artists = CustomUser.objects.filter(role='artist')
    context = {'artists': artists}
    if request.method == 'POST':
        brief = request.POST.get('brief', '').strip()
        summaries = _collect_artist_summaries()
        if not summaries:
            messages.error(request, 'No artists found to analyze.')
            return render(request, 'appCore/ai_search.html', context)

        prompt = (
            "You are an AI Candidate Search tool for artist discovery. Rank the best artists "
            "for the given project brief using the available data.\n\n"
            f"Project brief: {brief}\n\n"
            "Artist data:\n"
        )
        for summary in summaries:
            prompt += (
                f"Artist: {summary['username']}\n"
                f"Bio: {summary['bio']}\n"
                f"Website: {summary['website']}\n"
                "Artworks:\n" + "\n".join(summary['artworks'] or ["- (no artworks)"]) + "\n\n"
            )

        schema = {
            'type': 'json_schema',
            'name': 'candidate_search',
            'strict': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'results': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'username': {'type': 'string'},
                                'score': {'type': 'number'},
                                'reason': {'type': 'string'},
                            },
                            'required': ['username', 'score', 'reason'],
                            'additionalProperties': False,
                        },
                    },
                },
                'required': ['results'],
                'additionalProperties': False,
            }
        }

        try:
            result_text, _ = _openai_responses_call(prompt, schema=schema)
            context['result'] = json.loads(result_text) if result_text else None
            context['brief'] = brief
        except Exception as exc:
            context['error'] = str(exc)
            context['brief'] = brief

    return render(request, 'appCore/ai_search.html', context)
