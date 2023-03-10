from http import HTTPStatus

from django.core.cache import cache
from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД
        cls.user = User.objects.create_user(username='testuser')
        cls.group = Group.objects.create(
            title='TEST',
            slug='test',
            description='TEST AAAAAA!!!!'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый TEST',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        settings.DEBUG = True

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)
        settings.DEBUG = False

    def test_posts_urls_expected(self):
        """Страницы доступны."""
        test_urls_locations = {
            '/': HTTPStatus.OK,
            '/group/test/': HTTPStatus.OK,
            '/profile/testuser/': HTTPStatus.OK,
            '/posts/1/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for address, codes in test_urls_locations.items():
            with self.subTest(address=address):
                status_code = self.client.get(address).status_code
                self.assertEqual(status_code, codes)

    def test_posts_urls_expected_authorized(self):
        """Страницы доступны авторизованному пользователю."""
        urls_status = {
            reverse('posts:post_create'): HTTPStatus.OK,
            '/posts/1/edit/': HTTPStatus.OK,
        }
        for urls, status_code in urls_status.items():
            with self.subTest(urls=urls):
                response = self.authorized_client.get(urls)
                self.assertEqual(response.status_code, status_code)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            '/': 'posts/index.html',
            '/group/test/': 'posts/group_list.html',
            '/profile/testuser/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/unexisting_page/': 'core/404.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
