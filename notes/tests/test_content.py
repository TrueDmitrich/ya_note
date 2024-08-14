from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestConent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user_1 = User.objects.create(username='auth_user_1')
        cls.user_1_client = Client()
        cls.user_1_client.force_login(user=cls.user_1)
        cls.user_2 = User.objects.create(username='auth_user_2')
        cls.user_2_client = Client()
        cls.user_2_client.force_login(user=cls.user_2)

        cls.note_user_1 = Note.objects.create(
            title='Запись 1',
            text='Текст записи 1',
            slug='note_1',
            author=cls.user_1)
        cls.note_user_2 = Note.objects.create(
            title='Запись 2',
            text='Текст записи 2',
            slug='note_2',
            author=cls.user_2)

    def test_notes_list(self):
        response = self.user_1_client.get(reverse('notes:list'))
        self.assertIn(self.note_user_1, response.context['object_list'])
        self.assertNotIn(self.note_user_2, response.context['object_list'])

    def test_form_exist(self):
        values = [('notes:add', None),
                  ('notes:edit', {'slug': self.note_user_1.slug, })]

        for name, kwargs in values:
            with self.subTest(name=name):
                response = self.user_1_client.get(reverse(name, kwargs=kwargs))
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
