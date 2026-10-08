from django.test import Client, TestCase

from django.contrib.auth import get_user_model
from django.urls import reverse

from .forms import CommentForm
from .models import Comment, Post, Tag


class PostTagTests(TestCase):
    def setUp(self):
        self.python_tag = Tag.objects.create(name='Python', slug='python')
        self.django_tag = Tag.objects.create(name='Django', slug='django')
        self.python_post = Post.objects.create(
            title='Python post',
            slug='python-post',
            content='Post about Python',
        )
        self.python_post.tags.add(self.python_tag)
        self.django_post = Post.objects.create(
            title='Django post',
            slug='django-post',
            content='Post about Django',
        )
        self.django_post.tags.add(self.django_tag)

    def test_index_filters_posts_by_tag(self):
        response = self.client.get(reverse('blog:index'), {'tag': 'python'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.python_post.title)
        self.assertNotContains(response, self.django_post.title)

    def test_index_shows_all_posts_without_a_tag_filter(self):
        response = self.client.get(reverse('blog:index'))

        self.assertContains(response, self.python_post.title)
        self.assertContains(response, self.django_post.title)

    def test_detail_shows_post_tags_instead_of_generic_article_badge(self):
        response = self.client.get(
            reverse('blog:detail', kwargs={'slug': self.python_post.slug})
        )

        self.assertContains(response, 'Python</a>')
        self.assertNotContains(response, 'class="blog-tag">ARTÍCULO</span>')


class PostSortTests(TestCase):
    def setUp(self):
        self.older_post = Post.objects.create(
            title='Older post',
            slug='older-post',
            content='Older content',
        )
        self.newer_post = Post.objects.create(
            title='Newer post',
            slug='newer-post',
            content='Newer content',
        )
        Post.objects.filter(pk=self.older_post.pk).update(created_at='2026-01-01T00:00:00Z')
        Post.objects.filter(pk=self.newer_post.pk).update(created_at='2026-02-01T00:00:00Z')
        self.tag = Tag.objects.create(name='Python', slug='python')
        self.older_post.tags.add(self.tag)
        Comment.objects.create(post=self.older_post, name='Guest', content='First comment')
        Comment.objects.create(post=self.older_post, name='Guest', content='Second comment')

    def get_post_titles(self, response):
        return [post.title for post in response.context['posts']]

    def test_newest_is_the_default_sort(self):
        response = self.client.get(reverse('blog:index'))

        self.assertEqual(self.get_post_titles(response), ['Newer post', 'Older post'])
        self.assertEqual(response.context['selected_sort'], 'newest')

    def test_oldest_sort(self):
        response = self.client.get(reverse('blog:index'), {'sort': 'oldest'})

        self.assertEqual(self.get_post_titles(response), ['Older post', 'Newer post'])

    def test_comment_count_sorts(self):
        most_comments = self.client.get(reverse('blog:index'), {'sort': 'most_comments'})
        fewest_comments = self.client.get(reverse('blog:index'), {'sort': 'fewest_comments'})

        self.assertEqual(self.get_post_titles(most_comments), ['Older post', 'Newer post'])
        self.assertEqual(self.get_post_titles(fewest_comments), ['Newer post', 'Older post'])

    def test_sort_preserves_tag_filter(self):
        response = self.client.get(
            reverse('blog:index'),
            {'tag': 'python', 'sort': 'oldest'},
        )

        self.assertEqual(self.get_post_titles(response), ['Older post'])
        self.assertEqual(response.context['selected_tag'], 'python')
        self.assertEqual(response.context['selected_sort'], 'oldest')
        self.assertContains(response, 'aria-label="Ordenar publicaciones"')
        self.assertContains(response, '?tag=python&amp;sort=oldest')
        self.assertContains(response, 'class="active">Más antiguo</a>')


class CommentFormTests(TestCase):
    def setUp(self):
        self.post = Post.objects.create(
            title='Test post',
            slug='test-post',
            content='Post content',
        )
        self.url = reverse('blog:detail', kwargs={'slug': self.post.slug})

    def test_name_is_not_a_form_field(self):
        self.assertNotIn('name', CommentForm().fields)

    def test_anonymous_comment_uses_anonymous_name(self):
        self.client.post(self.url, {'content': 'A comment', 'name': 'Impersonated'})

        comment = self.post.comments.get()
        self.assertEqual(comment.name, 'Anónimo')

    def test_authenticated_comment_uses_username(self):
        user = get_user_model().objects.create_user(username='rama', password='password')
        self.client.force_login(user)

        self.client.post(self.url, {'content': 'A comment', 'name': 'Impersonated'})

        comment = self.post.comments.get()
        self.assertEqual(comment.name, 'rama')

    def test_comment_returns_to_anonymous_name_after_logout(self):
        user = get_user_model().objects.create_user(username='rama', password='password')
        self.client.force_login(user)
        self.client.post(self.url, {'content': 'Logged-in comment'})
        self.client.post(reverse('blog:logout'))
        self.client.post(self.url, {'content': 'Anonymous comment'})

        comments = list(self.post.comments.order_by('id'))
        self.assertEqual([comment.name for comment in comments], ['rama', 'Anónimo'])


class AccountTests(TestCase):
    def setUp(self):
        self.url = reverse('blog:account')

    def test_account_page_hides_contact_navigation_and_section(self):
        response = self.client.get(self.url)

        self.assertNotContains(response, 'Contacto')
        self.assertNotContains(response, 'CONTACTO')
        self.assertNotContains(response, 'GITHUB')
        self.assertContains(response, 'class="home-button">Continuar</button>')

    def test_logged_out_page_hides_contact_navigation_and_section(self):
        response = self.client.get(reverse('blog:logged_out'))

        self.assertNotContains(response, 'Contacto')
        self.assertNotContains(response, 'CONTACTO')
        self.assertNotContains(response, 'GITHUB')

    def test_new_user_is_created_and_logged_in(self):
        response = self.client.post(self.url, {
            'username': 'new-reader',
            'password': 'Uncommon-Passphrase-482!',
        })

        user = get_user_model().objects.get(username='new-reader')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_superuser)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

        response = self.client.get(self.url)
        self.assertContains(response, 'Cuenta creada y sesión iniciada correctamente.')
        self.assertContains(response, 'Deslogearse')
        self.assertContains(response, 'class="home-button">Ir al blog</a>')

    def test_existing_user_can_log_in(self):
        user = get_user_model().objects.create_user(
            username='existing-reader',
            password='Uncommon-Passphrase-482!',
        )

        response = self.client.post(self.url, {
            'username': 'existing-reader',
            'password': 'Uncommon-Passphrase-482!',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_wrong_password_for_existing_user_does_not_create_account(self):
        get_user_model().objects.create_user(
            username='existing-reader',
            password='Uncommon-Passphrase-482!',
        )

        response = self.client.post(self.url, {
            'username': 'existing-reader',
            'password': 'Wrong-Passphrase-482!',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'no son correctos')
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_short_password_is_rejected_for_new_account(self):
        response = self.client.post(self.url, {
            'username': 'new-reader',
            'password': 'short',
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors['password'])
        self.assertFalse(get_user_model().objects.filter(username='new-reader').exists())

    def test_superuser_sees_logout_action_in_headers(self):
        admin = get_user_model().objects.create_superuser(
            username='admin',
            password='Uncommon-Passphrase-482!',
            email='admin@example.com',
        )
        self.client.force_login(admin)

        blog_response = self.client.get(reverse('blog:index'))
        home_response = self.client.get(reverse('home'))

        self.assertContains(blog_response, 'Deslogearse')
        self.assertContains(home_response, 'Deslogearse')
        self.assertContains(blog_response, 'home-btn account-logout-button')
        self.assertContains(home_response, 'home-btn account-logout-button')

    def test_logout_requires_post_and_closes_session(self):
        user = get_user_model().objects.create_user(username='reader', password='password')
        self.client.force_login(user)

        response = self.client.get(reverse('blog:logout'))

        self.assertEqual(response.status_code, 405)
        response = self.client.post(reverse('blog:logout'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('blog:logged_out'))
        self.assertNotIn('_auth_user_id', self.client.session)
        logged_out_response = self.client.get(reverse('blog:logged_out'))
        self.assertContains(logged_out_response, 'Cerramos tu sesión')
        self.assertContains(logged_out_response, 'class="home-button">Volver al inicio</a>')
        self.assertContains(logged_out_response, '<a href="/" class="home-button">Volver al inicio</a>')

    def test_logout_requires_a_csrf_token(self):
        user = get_user_model().objects.create_user(username='reader', password='password')
        client = Client(enforce_csrf_checks=True)
        client.force_login(user)

        response = client.post(reverse('blog:logout'))
        self.assertEqual(response.status_code, 403)

        client.get(reverse('home'))
        csrf_token = client.cookies['csrftoken'].value
        response = client.post(
            reverse('blog:logout'),
            {'csrfmiddlewaretoken': csrf_token},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('blog:logged_out'))


class DeleteCommentTests(TestCase):
    def setUp(self):
        self.post = Post.objects.create(
            title='Test post',
            slug='test-post',
            content='Post content',
        )
        self.comment = Comment.objects.create(
            post=self.post,
            name='Guest',
            content='A comment',
        )
        self.url = reverse(
            'blog:delete_comment',
            kwargs={'slug': self.post.slug, 'comment_id': self.comment.id},
        )

    def test_superuser_can_delete_comment(self):
        admin = get_user_model().objects.create_superuser(
            username='admin',
            password='password',
            email='admin@example.com',
        )
        self.client.force_login(admin)

        response = self.client.post(self.url)

        self.assertRedirects(response, reverse('blog:detail', kwargs={'slug': self.post.slug}))
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_regular_user_cannot_delete_comment(self):
        user = get_user_model().objects.create_user(username='rama', password='password')
        self.client.force_login(user)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk).exists())
