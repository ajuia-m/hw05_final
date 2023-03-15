from django import forms
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Comment, Follow, Post, Group, User


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='SadStudent')
        cls.other_user = User.objects.create_user(username="Someone")
        cls.author = User.objects.create(username='Some_guy')
        cls.group = Group.objects.create(
            title='Тестовая',
            slug='test',
            description='Тестовое',
        )
        cls.group0 = Group.objects.create(
            title='Тестовая0',
            slug='test0',
            description='Тестовое0',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test',
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text="test",
            post=cls.post
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)
        # Создаем авторизованный клиент для подписчиков
        self.other_client = Client()
        self.other_client.force_login(self.other_user)

    def context_checker(self, page_context):
        """Метод проверки контекста."""
        self.assertEqual(page_context.author, PostPagesTests.post.author)
        self.assertEqual(page_context.group, PostPagesTests.post.group)
        self.assertEqual(page_context.text, PostPagesTests.post.text)
        self.assertEqual(page_context.image, PostPagesTests.post.image)
        self.assertEqual(page_context.comments.last(), PostPagesTests.comment)

    def test_index_has_correct_context(self):
        """
        Проверяет, что шаблон index сформирован с правильным контекстом."""
        response = (
            self.authorized_client.get(reverse('posts:index')))
        page_context = response.context['page_obj'][0]
        self.context_checker(page_context)

    def test_group_list_has_correct_context(self):
        """
        Проверяет, что шаблон group_list
        сформирован с правильным контекстом.
        """

        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': PostPagesTests.group.slug}))
        post_group = response.context['group']
        self.assertEqual(post_group, PostPagesTests.group)
        self.context_checker(response.context['page_obj'][0])

    def test_profile_has_correct_context(self):
        """
        Проверяет, что шаблон Profile
        сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': PostPagesTests.user.username}))
        profile_context = response.context
        post_profile = profile_context['author']
        self.assertEqual(post_profile, PostPagesTests.user)
        page_context = response.context['page_obj'][0]
        self.context_checker(page_context)

    def test_create_has_correct_context(self):
        """
        Проверяет, что шаблон Create_Post
        сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields[value]
                self.assertIsInstance(form_field, expected)

    # Проверка словаря контекста страницы Edit Post
    def test_editpost_has_correct_context(self):
        """
        Проверяет, что шаблон Edit_Post
        сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostPagesTests.post.pk}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField, }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                forms_field = response.context.get('form').fields[value]
                self.assertIsInstance(forms_field, expected)

    # Проверка словаря контекста страницы Post Detail
    def test_postdetail_has_correct_context(self):
        """Проверяет, что шаблон Post_Detail
        сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostPagesTests.post.pk}))
        self.assertEqual(response.context['post'], PostPagesTests.post)
        self.context_checker(response.context['post'])

    def test_paginator_views(self):
        pag_obj = []
        for i in range(12):
            another_post = Post(
                author=PostPagesTests.post.author,
                group=PostPagesTests.group,
                text=f'Текст поста проверки паджинатора{i}'
            )
            pag_obj.append(another_post)
        Post.objects.bulk_create(pag_obj)
        # Тестирование паджинатора на первой и на второй странице ↓
        paginator_data = {
            reverse('posts:index'): 'index',
            reverse('posts:group_list',
                    kwargs={'slug': PostPagesTests.group.slug}):
            'group_list',
            reverse('posts:profile',
                    kwargs={'username': PostPagesTests.user.username}):
            'profile',
            reverse('posts:index')
            + '?page=2':
            'index',
            reverse('posts:group_list',
                    kwargs={'slug': PostPagesTests.group.slug})
                        + '?page=2':
                'group_list',
                reverse('posts:profile',
                        kwargs={'username': PostPagesTests.user.username})
                        + '?page=2':
            'profile'}
        for data, page in paginator_data.items():
            with self.subTest(page=page):
                response = self.client.get(data)
            if '?page=2' in data:
                self.assertEqual(len(response.context['page_obj']), 3)
            else:
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_post_is_correct_not_shown(self):
        """Проверка: пост не отображается там где не надо."""
        form_fields = {reverse("posts:group_list",
                               kwargs={"slug": self.group0.slug}):
                       PostPagesTests.post,
                       }
        for value, expected in form_fields.items():
            response = self.authorized_client.get(value)
            form_field = response.context["page_obj"]
            self.assertNotIn(expected, form_field)

    def test_cache(self):
        """Проверка кеша."""
        new_post = Post.objects.create(
            author=PostPagesTests.user,
            text='Текст поста теста кеша'
        )
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        resp_cont = response.content
        new_post.delete()
        response = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.assertEqual(resp_cont, response)
        cache.clear()
        response = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.assertNotEqual(resp_cont, response)

    # Проверяем возможность подписаться
    def test_follow(self):
        count = Follow.objects.count()
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostPagesTests.author.username}
            )
        )
        follow = Follow.objects.last()
        self.assertEqual(Follow.objects.count(), count + 1)
        self.assertEqual(PostPagesTests.author, follow.author)
        self.assertEqual(follow.user, PostPagesTests.user)

    # Проверяем возможность отписаться
    def test_unfollow_author(self):
        count = Follow.objects.count()
        Follow.objects.create(user=self.user, author=self.author)
        self.assertEqual(Follow.objects.count(), count + 1)
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author.username}
            )
        )
        self.assertEqual(Follow.objects.count(), count)

    # Проверяем появление поста у подписчиков
    def test_shown_post_for_followers(self):
        Follow.objects.create(user=self.other_user, author=self.user)
        response = self.other_client.get(
            reverse('posts:follow_index')
        )
        post = Post.objects.get(author=self.user)
        self.assertIn(post.text, response.content.decode())

    # Проверяем отсутствие поста у неподписанных
    def test_absence_post_for_others(self):
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(PostPagesTests.post.text,
                         response.context.get('page_obj'))
