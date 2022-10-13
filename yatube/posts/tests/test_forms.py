import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, Comment
from posts.forms import PostForm


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth_user')
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='test title',
            description='test description',
            slug='test-slug',
        )
        cls.group_2 = Group.objects.create(
            title='test-other-title',
            slug='test-other-slug',
            description='test-other-description'
        )
        cls.post = Post.objects.create(
            text='test text',
            author=cls.user,
            group=cls.group,
            image=cls.image,
        )
        # Создаем форму, если нужна проверка атрибутов
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями: 
        # создание, удаление, копирование, перемещение, изменение папок и файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованный клиент
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        # При создании валидной формы создаётся новая запись в базе данных
        posts_count = Post.objects.count()
        form_data = {
            'text': 'test text',
            'group': self.group.pk,
            'image': self.post.image,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': self.user}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='test text',
                group=self.group.pk,
                image=self.post.image,
            ).exists()
        )

    def test_edit_post(self): 
        """Валидная форма редактирования, обновляет запись в Post."""
        self.post = Post.objects.create(text='test text',
                                        author=self.user,
                                        group=self.group)
        old_text = self.post
        another_image = SimpleUploadedFile(
            name='another_small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'text_after_edit',
            'group': self.group_2.id,
            'image': another_image
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': old_text.id}),
            data=form_data,
            follow=True)
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': self.post.id}))
        post = Post.objects.get(id=self.post.pk)
        self.assertEqual(post.text, 'text_after_edit')
        self.assertEqual(post.group, self.group_2)
        self.assertEqual(post.image, f'posts/{another_image.name}')

    def test_auth_can_add_comments(self):
        """
        Комментировать посты может 
        только авторизованный пользователь.
        """
        form_data = {
            'post': self.post,
            'author': self.user,
            'text': 'test text'
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        comment = Comment.objects.first()
        self.assertEqual(comment.text, 'test text')
        self.assertEqual(comment.author, self.user)
        self.assertEqual(self.post.comments.count(), 1)
        self.assertEqual(comment.post, self.post)
