import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем запись в базе данных для проверки сушествующего slug
        cls.user = User.objects.create_user(username='AnotherSadUser')
        cls.group = Group.objects.create(
            title='Test',
            slug='Test',
            description='Test',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Test',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post_form(self):
        """Проверяем создание поста c картинкой"""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif')

        form_data = {
            'text': 'Новый пост',
            'group': PostsFormTests.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, reverse('posts:profile',
                              kwargs={
                                  'username': PostsFormTests.user.username}))
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создалась запись с нашим слагом
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
                image='posts/small.gif',
            ))

    def test_edit_post_form(self):
        """Проверяем внесение изменений в пост"""
        new_text = 'Update'
        post = PostsFormTests.post
        self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostsFormTests.post.pk}),

            data={'text': new_text},
        )
        self.assertEqual(new_text, Post.objects.get(pk=post.pk).text)

    def test_create_a_comment(self):
        """Проверяем успешность создания комментария."""
        comment_text = 'тест'
        comments_count = Comment.objects.count()
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': PostsFormTests.post.pk}),
            data={'text': comment_text}
        )
        self.assertLess(comments_count, Comment.objects.count())
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              kwargs={'post_id': PostsFormTests.post.pk})
        )

    # Проверяем, что анонимный пользователь не может создать пост
    def test_anonymus_cant_create_a_post(self):
        """Проверяем, что анонимный пользователь не может создать пост."""
        posts_count = Post.objects.count()
        post_text = 'Текст поста анонима'
        self.client.get(
            reverse('posts:post_create'),
            data={'text': post_text}
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_anonymus_cant_create_a_comment(self):
        """Проверяем, что аноним не может комментировать запись"""
        comments_count = Comment.objects.count()
        comment_text = 'Текст комментария анонима'
        self.client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': PostsFormTests.post.pk}),
            data={'text': comment_text}
        )
        self.assertEqual(comments_count, Comment.objects.count())
