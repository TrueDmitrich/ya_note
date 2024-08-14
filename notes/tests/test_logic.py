# news/tests/test_logic.py
from http import HTTPStatus
from pytils.translit import slugify

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

# Импортируем из файла с формами список стоп-слов и предупреждение формы.
# Загляните в news/forms.py, разберитесь с их назначением.
from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class Base(TestCase):
    data_note_1 = {
        'title': 'Запись 1',
        'text': 'Текст записи 1',
        'slug': 'note_1'}
    data_note_2 = {
        'title': 'Запись 2',
        'text': 'Текст записи 2',
        'slug': 'note_2'}

    @classmethod
    def setUpTestData(cls):
        cls.user_1 = User.objects.create(username='auth_user_1')
        cls.user_1_client = Client()
        cls.user_1_client.force_login(user=cls.user_1)
        cls.user_2 = User.objects.create(username='auth_user_2')
        cls.user_2_client = Client()
        cls.user_2_client.force_login(user=cls.user_2)


class TestConent(Base):

    def test_note_creation(self):
        values = [(self.client, 0), (self.user_1_client, 1)]
        for client, count in values:
            with self.subTest(client=client):
                client.post(reverse('notes:add'), data=self.data_note_1)
                notes_count = Note.objects.count()
                self.assertEqual(notes_count, count)

    def test_same_slug_note_creaation(self):
        self.user_1_client.post(reverse('notes:add'), data=self.data_note_1)
        self.assertEquals(Note.objects.count(), 1)
        note = Note.objects.get()
        # Проверяем точность создания
        self.assertEqual(note.title, self.data_note_1['title'])
        self.assertEqual(note.text, self.data_note_1['text'])
        self.assertEqual(note.slug, self.data_note_1['slug'])
        self.assertEqual(note.author, self.user_1)
        # Проверяем одинаковый slug
        response = self.user_1_client.post(
            reverse('notes:add'), data=self.data_note_1)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=f'{self.data_note_1["slug"]}' + WARNING
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_slug_auto_translate(self):
        self.data_note_1.pop('slug')
        self.user_1_client.post(reverse('notes:add'), data=self.data_note_1)
        note = Note.objects.get()
        self.assertEquals(note.slug, slugify(self.data_note_1['title'])[:100])


class TestChangeNotes(Base):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user_1_client.post(reverse('notes:add'), data=cls.data_note_1)
        cls.user_2_client.post(reverse('notes:add'), data=cls.data_note_2)
        cls.note_1 = Note.objects.get(pk=1)
        cls.note_2 = Note.objects.get(pk=2)

    def test_user_change_notes(self):
        new_text = 'Измененный текст'

        def get_change_form_data(note) -> dict:
            form_data = {
                'title': note.title,
                'text': new_text,
                'slug': note.slug, }
            return form_data

        # Проверка на своей записи
        response = self.user_1_client.post(
            reverse('notes:edit', kwargs={'slug': self.note_1.slug, }),
            data=get_change_form_data(self.note_1))
        self.assertRedirects(
            response,
            reverse('notes:success')
        )
        self.note_1.refresh_from_db()
        self.assertEqual(self.note_1.text, new_text)

        # Проверка на чужой записи
        response = self.user_1_client.post(
            reverse('notes:edit', kwargs={'slug': self.note_2.slug, }),
            data=get_change_form_data(self.note_2))
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note_2.refresh_from_db()
        self.assertEqual(self.note_2.text, self.data_note_2['text'])

    def test_user_delete_his_notes(self):
        response = self.user_1_client.delete(
            reverse('notes:delete', kwargs={'slug': self.note_1.slug, }))
        self.assertRedirects(
            response,
            reverse('notes:success')
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_user_delete_other_notes(self):
        response = self.user_1_client.delete(
            reverse('notes:delete', kwargs={'slug': self.note_2.slug, }))
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 2)
