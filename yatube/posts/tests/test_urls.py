from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post, Comment

User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = User.objects.create_user(username='An')
        Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        Post.objects.create(
            author=user,
            text='Тестовая группа',
        )

    def setUp(self):
        self.guest_client = Client()
        self.admin_user = User.objects.get(username='An')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.admin_user)
        self.post = Post.objects.create(
            author=self.admin_user, text='test_text'
        )
        self.other_user = User.objects.create_user(username='other_user')
        self.other_client = Client()
        self.other_client.force_login(self.other_user)

    def test_all_guests(self):
        """Проверяем доступность страниц не требующих авторизации."""
        url_names = {
            '/': 200,
            '/about/author/': 200,
            '/about/tech/': 200,
            '/group/test-slug/': 200,
            '/profile/An/': 200,
            f'/posts/{self.post.id}/': 200,
            '/unexisting_paje/': 404,
        }
        for url, expected_url_name in url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    expected_url_name,
                    f'Тест страницы {url}'
                    ' для пользователя провален'
                )

    def test_all_authorized(self):
        """Проверяем доступность страниц требующих авторизации."""
        url_names = {
            '/create/': 200,
            f'/posts/{self.post.id}/edit/': 200,
        }
        for url, expected_url_name in url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    response.status_code,
                    expected_url_name,
                    f'Тест страницы {url}'
                    ' для пользователя провален'
                )

    # Проверка вызываемых шаблонов для каждого адреса
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/An/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html'
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(
                    response, template,
                    f'{url} использует неправильный шаблон'
                )

    def test_no_author_edit(self):
        """
        Проверям доступность авторизированного пользователя(не автора поста)
        изменить запись.
         """
        response = self.other_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}), {
                'text': 'my new text',
            }
        )
        post = Post.objects.get(pk=self.post.id)
        self.assertNotEqual('my new text', post.text)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}),
        )

    def test_author_edit(self):
        """Проверям доступность авторизированного
        пользователя(автора поста).
        """
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}), {
                'text': 'my new text',
            }
        )
        post = Post.objects.get(pk=self.post.id)
        self.assertEqual('my new text', post.text)

    def test_profile_post_edit_not_auth(self):
        """Страница /<username>/<post_id>/edit/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk}),
            follow=True
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.id}/edit/',
        )

    def test_profile_post_edit_auth_not_author(self):
        """Страница /<username>/<post_id>/edit/ перенаправит
         авторизированного пользователя(не автора поста) на страницу поста.
        """
        response = self.other_client.post(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk}),
            follow=True
        )
        self.assertRedirects(response, (
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        ))
