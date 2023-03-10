from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()
LEN_TEXT = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_post_have_correct_object_names(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        value = str(self.post)
        expected_value = self.post.text[:LEN_TEXT]
        self.assertEqual(value, expected_value)

    def test_group_have_correct_object_names(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        value = str(self.group)
        expected_value = self.group.title
        self.assertEqual(value, expected_value)
