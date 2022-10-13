import shutil
import tempfile

from django.core.cache import cache
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Post, Group, Follow

from posts.forms import PostForm, CommentForm

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
class PostsViewsTests(TestCase):
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
        cls.group_without_posts = Group.objects.create(
            title='test title without posts',
            description='test description without posts',
            slug='no-posts-test-slug',
        )
        cls.post = Post.objects.create(
            text='test text',
            author=cls.user,
            group=cls.group,
            image=cls.image,
        )

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
        # Создаем автора поста
        self.authorized_author = Client()
        self.authorized_author.force_login(self.post.author)
        # Создаем другого авторизованного клиента
        self.another_user = User.objects.create_user(username='another_user')
        self.another_authorized_client = Client()
        self.another_authorized_client.force_login(self.another_user)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.user.username}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}):
            'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

        # Проверка словаря контекста главной страницы (в нём передаётся форма)
    def test_index_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text = first_object.text
        post_author = first_object.author.username
        post_group = first_object.group
        self.assertEqual(post_text, self.post.text)
        self.assertEqual(post_author, self.post.author.username)
        self.assertEqual(post_group, self.post.group)
        self.assertTrue(first_object.image)

    def test_group_posts_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        )
        expected = Group.objects.get(slug=self.group.slug)
        group = response.context['group']
        page_obj = response.context['page_obj']
        self.assertEqual(group, expected)
        self.assertIn(self.post, page_obj)
        self.assertEqual(response.context.get('post').image, self.post.image)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.post.author.username}))
        )
        for i in range(len(response.context['page_obj'])):
            post = response.context['page_obj'][i]
            self.assertEqual(post.author, self.post.author)

        self.assertEqual(response.context.get('author'), self.post.author)
        self.assertTrue(post.image)

    def test_post_detail_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        )
        first_object = response.context['post']
        post_text = first_object.text
        post_author = first_object.author
        post_count = first_object.author.posts.count()
        self.assertEqual(post_text, self.post.text)
        self.assertEqual(post_author, self.post.author)
        self.assertEqual(post_count, PostsViewsTests.user.posts.count())
        self.assertTrue(response.context.get('post').image)

    def test_create_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertIsInstance(response.context.get('form'), PostForm)
        self.assertNotIn('is_edit', response.context)

    def test_edit_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = (self.authorized_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}))
        )
        self.assertIsInstance(response.context.get('form'), PostForm)
        post_id = response.context.get('post_id')
        self.assertEqual(post_id, self.post.pk)

    def test_create_post_home_group_list_profile_pages(self):
        """Созданный пост отобразился на главной,
        на странице группы, в профайле пользователя."""
        list_urls = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.post.author.username}),
        )
        for tested_url in list_urls:
            response = self.authorized_author.get(tested_url)
            self.assertEqual(len(response.context['page_obj'].object_list), 1)

    def test_no_post_in_another_group_posts(self):
        """Пост не попал в группу, для которой не был предназначен."""
        response = (self.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group_without_posts.slug}))
        )
        posts = response.context['page_obj']
        self.assertEqual(0, len(posts))

    def test_cache_index_pages(self):
        """Проверяем работу кэша главной страницы."""
        first_view = self.authorized_client.get(reverse('posts:index'))
        post_1 = Post.objects.get(pk=1)
        post_1.text = 'Changed text'
        post_1.save()
        second_view = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(first_view.content, second_view.content)
        cache.clear()
        third_view  = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(first_view.content, third_view.content)


    def test_authorized_client_follow(self):
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.another_user})
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.another_user).exists()
        )

    def test_authorized_client_unfollow(self):
        Follow.objects.create(
            user=self.user,
            author=self.another_user
        )
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.another_user})
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.another_user
            ).exists()
        )

    def test_new_post_doesnt_shown_to_follower(self):
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(self.post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth_user')
        cls.group = Group.objects.create(
            title='test title',
            description='test description',
            slug='test-slug',
        )
        cls.posts = []
        for i in range(13):
            cls.posts.append(
                Post(text=f'Test post {i+1}',
                     author=cls.author,
                     group=cls.group)
            )
        Post.objects.bulk_create(cls.posts)

    def test_paginator(self):
        """Тест паджинатора."""
        list_urls = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.author}),
        }
        for tested_url in list_urls:
            response = self.client.get(tested_url)
            self.assertEqual(len(response.context.get(
                'page_obj').object_list), 10)

        for tested_url in list_urls:
            response = self.client.get(tested_url, {'page': 2})
            self.assertEqual(len(response.context.get(
                'page_obj').object_list), 3)



