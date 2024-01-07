from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from .models import Post, MainTag, SubTag
from . models import Post, Comment, Reaction
User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    bio = forms.CharField(required=False, widget=forms.Textarea)
    profile_pic = forms.ImageField(required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('bio', 'profile_pic',)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.bio = self.cleaned_data['bio']
        user.profile_pic = self.cleaned_data['profile_pic']
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    pass


class NewUserForm(UserCreationForm):
    pass


class UserLoginForm(AuthenticationForm):
    pass


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'status', 'main_tag', 'subtag', 'featured_image', 'excerpt']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'main_tag': forms.Select(attrs={'class': 'form-control'}),
            'subtag': forms.Select(attrs={'class': 'form-control'}),
            'featured_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, user, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.fields['subtag'].queryset = SubTag.objects.filter(user=user)
        self.fields['subtag'].required = False


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
