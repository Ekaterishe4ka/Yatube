from django import forms
from django.forms.widgets import Textarea

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Введите текст',
            'group': 'Выберите группу',
            'image': 'Изображение',
        }
        widgets = {
            'text': forms.Textarea(attrs={'rows': 12, 'cols': 45}),
        }
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой относится пост',
            'image': 'Загрузите картинку',
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст комментария',
        }
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'cols': 40}),
        }
        help_texts = {
            'text': 'Текст комментария',
        }
