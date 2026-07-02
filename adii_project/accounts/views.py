from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm, RegisterForm, ProfileForm
from .models import User

def home(request):
    return render(request, 'home.html')

def auth_view(request):
    mode = request.GET.get('mode', 'user')
    login_form = LoginForm()
    register_form = RegisterForm()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'login':
            email = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=email, password=password)
            if user:
                if mode == 'admin' and not user.is_admin():
                    messages.error(request, "Accès refusé. Vous n'êtes pas administrateur.")
                elif mode == 'technicien' and not user.is_technicien():
                    messages.error(request, "Accès refusé. Vous n'êtes pas technicien.")
                else:
                    login(request, user)
                    return redirect(get_redirect(user))
            else:
                messages.error(request, "Email ou mot de passe incorrect.")
            login_form = LoginForm(request.POST)
        elif action == 'register':
            register_form = RegisterForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                login(request, user)
                messages.success(request, "Compte créé avec succès !")
                return redirect('agent_dashboard')
            else:
                messages.error(request, "Veuillez corriger les erreurs.")

    return render(request, 'auth.html', {
        'login_form': login_form,
        'register_form': register_form,
        'mode': mode
    })

def get_redirect(user):
    if user.is_admin():
        return '/admin-dashboard/'
    elif user.is_technicien():
        return '/technicien/'
    elif user.is_secretaire():
        return '/secretaire/'
    return '/agent/'

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour.")
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'profile.html', {'form': form})