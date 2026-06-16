from django import forms
from django.contrib.auth import get_user_model

from .models import Post, Comment


User = get_user_model()


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
        )


ProfileEditForm = UserForm
UserEditForm = UserForm
ProfileForm = UserForm


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('title', 'text', 'pub_date', 'location', 'category', 'image')


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
