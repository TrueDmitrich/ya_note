from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestPermissions(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.auth_user = User.objects.create(username='auth_user')
        cls.auth_client = Client()
        cls.auth_client.force_login(user=cls.auth_user)
        cls.author_user = User.objects.create(username='author_user')
        cls.author_client = Client()
        cls.author_client.force_login(user=cls.author_user)

        cls.note = Note.objects.create(
            title='Запись 1',
            text='Текст записи 1',
            slug='note_1',
            author=cls.author_user)

    def test_status_code(self):
        values = [
            (self.client, 'notes:home', None, HTTPStatus.OK),
            (self.client, 'users:login', None, HTTPStatus.OK),
            (self.client, 'users:logout', None, HTTPStatus.OK),
            (self.client, 'users:signup', None, HTTPStatus.OK),
            (self.auth_client, 'notes:list', None, HTTPStatus.OK),
            (self.auth_client, 'notes:add', None, HTTPStatus.OK),
            (self.auth_client, 'notes:success', None, HTTPStatus.OK),
            (self.author_client, 'notes:detail', {'slug': self.note.slug, },
             HTTPStatus.OK),
            (self.author_client, 'notes:edit', {'slug': self.note.slug, },
             HTTPStatus.OK),
            (self.author_client, 'notes:delete', {'slug': self.note.slug, },
             HTTPStatus.OK),
            (self.auth_client, 'notes:detail', {'slug': self.note.slug, },
             HTTPStatus.NOT_FOUND),
            (self.auth_client, 'notes:edit', {'slug': self.note.slug, },
             HTTPStatus.NOT_FOUND),
            (self.auth_client, 'notes:delete', {'slug': self.note.slug, },
             HTTPStatus.NOT_FOUND),
        ]

        for client, url_name, kwargs, status_code in values:
            with self.subTest(client=client, url_name=url_name):
                response = client.get(reverse(url_name, kwargs=kwargs))
                self.assertEqual(response.status_code, status_code)

    def test_redirects_to_login_for_notauthuser(self):
        values = [
            (self.client, 'notes:list', None),
            (self.client, 'notes:add', None),
            (self.client, 'notes:success', None),
            (self.client, 'notes:detail', {'slug': self.note.slug, }),
            (self.client, 'notes:edit', {'slug': self.note.slug, }),
            (self.client, 'notes:delete', {'slug': self.note.slug, }),
        ]

        for client, url_name, kwargs in values:
            with self.subTest(client=client, url_name=url_name):
                url = reverse(url_name, kwargs=kwargs)
                response = client.get(url)
                expectes_url = reverse('users:login') + '?next=' + url
                self.assertRedirects(response, expectes_url)
