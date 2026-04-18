from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Resume
from .forms import ProfileForm


@login_required
def profile(request):
    resumes = request.user.resumes.all()
    return render(request, 'accounts/profile.html', {'resumes': resumes})


@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
def resume_delete(request, slug):
    resume = get_object_or_404(Resume, slug=slug, user=request.user)
    if request.method == 'POST':
        resume.delete()
        messages.success(request, f'"{resume.title}" deleted.')
    return redirect('accounts:profile')


@login_required
def resume_open(request, slug):
    resume = get_object_or_404(Resume, slug=slug, user=request.user)
    request.session['resume_state'] = {
        'html':         resume.html_content,
        'css':          resume.css_content,
        'framework':    resume.framework,
        'paper':        resume.paper_size,
        'photo_url':    getattr(resume, 'photo_url', ''),
        'resume_slug':  resume.slug,
        'resume_title': resume.title,
    }
    request.session.pop('new_resume_requested', None)
    request.session.modified = True
    return redirect('builder:workspace')


@require_POST
def resume_toggle_public(request, slug):
    resume = get_object_or_404(Resume, slug=slug, user=request.user)
    resume.is_public = not resume.is_public
    resume.save(update_fields=['is_public'])
    status = 'public' if resume.is_public else 'private'
    messages.success(request, f'"{resume.title}" is now {status}.')
    return redirect('accounts:profile')

