from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth_user')
        cls.group = Group.objects.create(
            title='test title',
            description='test description',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='test text',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        self.user = User.objects.create_user(username='HasNoName')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(PostsURLTests.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_guest(self):
        """
        Страницы доступные любому пользователю.
        """
        url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
        }
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template_logged_in(self):
        """
        Страницы доступные авторизованному пользователю.
        """
        url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
        }
        for address in url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_author_only_available(self):
        """
        Страница доступная только автору.
        """
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect(self):
        """
        Проверка редиректа:
        - при попытке изменить пост гостем,
        - при попытке создания поста гостем.
        """
        response_edit_guest = self.guest_client.get(
            f'/posts/{self.post.id}/edit/')
        response_create_guest = self.guest_client.get(
            '/create/')
        self.assertRedirects(
            response_edit_guest,
            f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )
        self.assertRedirects(
            response_create_guest, '/auth/login/?next=/create/'
        )

    def test_url_edit_not_author_correct_template(self):
        """
        Проверка redirect при попытке изменить пост
        для авторизованного пользователя не-автора.
        """
        self.not_author = User.objects.create_user(username='not_author')
        self.not_author_client = Client()
        self.not_author_client.force_login(self.not_author)

        response = self.not_author_client.get(
            f'/posts/{self.post.pk}/edit/')
        self.assertRedirects(
            response,
            f'/posts/{self.post.pk}/'
        )
