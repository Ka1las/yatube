import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Comment, Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='An')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
            pub_date='Тестовая дата',
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template_guest_client(self):
        """URL-адрес использует соответствующий шаблон гост. клиентов."""
        templates_page_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_list', kwargs={'slug': 'test-slug'}
            ),
            'posts/profile.html': reverse(
                'posts:profile', kwargs={'username': 'An'}
            ),
            'posts/post_detail.html': reverse(
                'posts:post_detail', kwargs={'post_id': '1'}
            ),
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(
                    response, template,
                    f'{reverse_name} использует неправильный риверс'
                )

    def test_pages_uses_correct_template_authorized_client(self):
        """URL-адрес использует соответствующий шаблон автор. клиентов."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}): (
                'posts/group_list.html'
            ),
            reverse('posts:profile', kwargs={'username': 'An'}): (
                'posts/profile.html'
            ),
            reverse('posts:post_detail', kwargs={'post_id': '1'}): (
                'posts/post_detail.html'
            ),
            reverse('posts:post_edit', kwargs={'post_id': '1'}): (
                'posts/create_post.html'
            ),
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(
                    response, template,
                    f'{reverse_name} использует неправильный риверс'
                )

    def test_index_paje_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        response_page_obj = response.context.get('page_obj').object_list[0]
        response_title = response.context.get('title')
        response_posts = response.context.get('posts')
        context_name = {
            response_page_obj.author: self.user,
            response_page_obj.text: self.post.text,
            response_page_obj.group: self.group,
        }
        for response_page_obj, expected in context_name.items():
            with self.subTest(response_page_obj=response_page_obj):
                self.assertEqual(response_page_obj, expected)
        self.assertEqual(response_title, 'Последние обновления на сайте')
        self.assertQuerysetEqual(
            response_posts, self.user.posts.all(), transform=lambda x: x
        )

    def test_group_list_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        )
        response_page_obj = response.context.get('page_obj').object_list[0]
        response_title = response.context.get('title')
        response_group = response.context.get('group')
        context_name = {
            response_page_obj.author: self.user,
            response_page_obj.text: self.post.text,
            response_page_obj.group: self.group,
        }
        for response_page_obj, expected in context_name.items():
            with self.subTest(response_page_obj=response_page_obj):
                self.assertEqual(response_page_obj, expected)
        self.assertEqual(response_title, 'Группы сообщества')
        self.assertEqual(response_group, self.group)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': 'An'})
        )
        response_page_obj = response.context.get('page_obj').object_list[0]
        response_title = response.context.get('title')
        response_author = response.context.get('author')
        response_post_count = response.context.get('post_count')
        response_posts = response.context.get('posts')
        context_name = {
            response_page_obj.author: self.user,
            response_page_obj.text: self.post.text,
            response_page_obj.group: self.group,
        }
        for response_page_obj, expected in context_name.items():
            with self.subTest(response_page_obj=response_page_obj):
                self.assertEqual(response_page_obj, expected)
        self.assertEqual(response_title, 'Профайл пользователя An')
        self.assertEqual(response_author, self.user)
        self.assertEqual(response_post_count, 1)
        self.assertQuerysetEqual(
            response_posts, self.user.posts.all(), transform=lambda x: x
        )

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        response_post = response.context.get('post')
        response_author = response.context.get('author')
        response_pub_date = response.context.get('pub_date')
        response_post_count = response.context.get('post_count')
        context_name = {
            response_post.author: self.user,
            response_post.text: self.post.text,
            response_post.group: self.group,
        }
        for response_post, expected in context_name.items():
            with self.subTest(response_post=response_post):
                self.assertEqual(response_post, expected)
        self.assertEqual(response_author, self.user)
        self.assertEqual(response_post_count, 1)
        self.assertEqual(response_pub_date, self.post.pub_date)

    def test_post_post_edit_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client .get(
            reverse('posts:post_edit', kwargs={'post_id': '1'})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
        is_edit = response.context['is_edit']
        self.assertTrue(is_edit)
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_post_group_list(self):
        """Проверяем, что на group_list.html выводятся посты с группой.
        """
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}))
        first_post_slug = response.context['page_obj'][0].group.slug
        self.assertEqual(first_post_slug, 'test-slug')
        group_posts_1 = len(response.context['page_obj'])
        self.assertEqual(group_posts_1, 1)

    def test_post_image_context(self):
        list = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        for page in list:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                image = response.context['page_obj'][0].image
                self.assertEqual(image, self.post.image)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='An')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )

        batch_size = 13
        posts = [Post(
            text=f'Текст поста №{i}',
            author=cls.user,
            group=cls.group) for i in range(batch_size)
        ]
        Post.objects.bulk_create(posts, batch_size)

    def test_first_page_contains_ten_records(self):
        """Paginator предоставляет ожидаемое количество постов
         на первую страницую."""
        templates = {
            1: reverse('posts:index'),
            2: reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            3: reverse('posts:profile', kwargs={'username': 'An'})
        }
        for i in templates.keys():
            with self.subTest(i=i):
                response = self.client.get(templates[i])
                self.assertEqual(len(response.context.get(
                    'page_obj'
                ).object_list), 10)

    def test_second_page_contains_three_records(self):
        """Paginator предоставляет ожидаемое количество постов
         на вторую страницую."""
        templates = {
            1: reverse('posts:index'),
            2: reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            3: reverse('posts:profile', kwargs={'username': 'An'})
        }
        for i in templates.keys():
            with self.subTest(i=i):
                response = self.client.get(templates[i], {'page': 2})
                self.assertEqual(len(response.context.get(
                    'page_obj'
                ).object_list), 3)

    def test_error_page(self):
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')


class CommentViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='An')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )

        cls.post = Post.objects.create(
            text='test_post',
            group=cls.group,
            author=cls.user
        )

    def test_add_comment_for_guest(self):
        """Неавторизованный пользователь не может оставить комментарий"""
        response = self.guest_client.get(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(
            response.status_code,
            HTTPStatus.FOUND,
            ('Неавторизированный пользователь'
             ' не может оставлять комментарий')
        )

    def test_comment_for_auth_user(self):
        """Авторизированный пользователь может оставить комментарий"""
        response = self.authorized_client.get(
            reverse('posts:add_comment', kwargs={
                'post_id': self.post.pk
            }), follow=True
        )
        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            ('Авторизированный пользователь'
             ' должен иметь возможность'
             ' оставлять комментарий')
        )
        comments_count = Comment.objects.filter(
            post=self.post.pk
        ).count()
        form_data = {
            'text': 'test_comment',
        }

        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        comments = Post.objects.filter(
            id=self.post.pk
        ).values_list('comments', flat=True)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(
            comments.count(),
            comments_count + 1
        )
        self.assertTrue(
            Comment.objects.filter(
                post=self.post.pk,
                author=self.user.pk,
                text=form_data['text']
            ).exists()
        )

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='test_new_post',
            author=self.user,
        )
        response_old = self.authorized_client.get(
            reverse('posts:index')
        )
        old_posts = response_old.content
        self.assertEqual(
            old_posts,
            posts,
            'Не возвращает кэшированную страницу.'
        )
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts, 'Нет сброса кэша.')


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='An')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.other_user = User.objects.create_user(username='other_user')
        cls.authorized_other_user = Client()
        cls.authorized_other_user.force_login(cls.other_user)

        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )

        cls.post = Post.objects.create(
            text='test_post',
            group=cls.group,
            author=cls.user
        )

    def test_follow(self):
        """Тест работы подписки на автора."""
        self.authorized_other_user.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user.username}
            )
        )
        follower = Follow.objects.filter(
            user=self.other_user,
            author=self.user
        ).exists()
        self.assertTrue(
            follower,
            'Не работает подписка на автора'
        )

    def test_unfollow(self):
        """Тест работы отписки от автора."""
        self.authorized_other_user.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user.username}
            )
        )
        follower = Follow.objects.filter(
            user=self.other_user,
            author=self.user
        ).exists()
        self.assertFalse(
            follower,
            'Не работает подписка на автора'
        )

    def test_new_author_post_for_follower(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан"""
        self.authorized_other_user.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user.username}
            )
        )
        response_old = self.authorized_other_user.get(
            reverse('posts:follow_index')
        )
        old_posts = response_old.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_old.context.get('page_obj').object_list),
            1,
            'Не загружается правильное колличество старых постов'
        )
        self.assertIn(
            self.post,
            old_posts,
            'Старый пост не верен'
        )
        new_post = Post.objects.create(
            text='test_new_post',
            group=self.group,
            author=self.user
        )
        cache.clear()
        response_new = self.authorized_other_user.get(
            reverse('posts:follow_index')
        )
        new_posts = response_new.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_new.context.get('page_obj').object_list),
            2,
            'Нету нового поста'
        )
        self.assertIn(
            new_post,
            new_posts,
            'Новый пост не верен'
        )

    def test_new_author_post_for_unfollower(self):
        """Новая запись пользователя не появляется в ленте тех,
        кто на него не подписан"""
        response_old = self.authorized_other_user.get(
            reverse('posts:follow_index')
        )
        old_posts = response_old.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_old.context.get('page_obj').object_list),
            0,
            'Не загружается правильное колличество старых постов'
        )
        self.assertNotIn(
            self.post,
            old_posts,
            'Старый пост не должен загружаться'
        )
        new_post = Post.objects.create(
            text='test_new_post',
            group=self.group,
            author=self.user
        )
        cache.clear()
        response_new = self.authorized_other_user.get(
            reverse('posts:follow_index')
        )
        new_posts = response_new.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_new.context.get('page_obj').object_list),
            0,
            'Новый пост не должен появляться'
        )
        self.assertNotIn(
            new_post,
            new_posts,
            'Новый пост не должен появляться'
        )
