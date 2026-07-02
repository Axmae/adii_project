from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User

class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'placeholder': 'votre@email.com', 'class': 'form-input'}))
    password = forms.CharField(label='Mot de passe', widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'class': 'form-input'}))

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-input'}))
    nom = forms.CharField(label='Nom', widget=forms.TextInput(attrs={'class': 'form-input'}))
    prenom = forms.CharField(label='Prénom', widget=forms.TextInput(attrs={'class': 'form-input'}))
    matricule = forms.CharField(label='Matricule', widget=forms.TextInput(attrs={'class': 'form-input'}))
    service = forms.CharField(label='Service', widget=forms.TextInput(attrs={'class': 'form-input'}))

    class Meta:
        model = User
        fields = ['email', 'nom', 'prenom', 'matricule', 'service', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.nom = self.cleaned_data['nom']
        user.prenom = self.cleaned_data['prenom']
        user.matricule = self.cleaned_data['matricule']
        user.service = self.cleaned_data['service']
        user.role = 'agent'
        if commit:
            user.save()
        return user

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['nom', 'prenom', 'matricule', 'service', 'email']
        widgets = {f: forms.TextInput(attrs={'class': 'form-input'}) for f in ['nom', 'prenom', 'matricule', 'service']}
