from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class LoginViewTest(TestCase):
    def setUp(self):
        self.login_url = reverse("login")
        # test uchun user
        self.user = User.objects.create_user(
            phone="+998901234567",
            password="StrongPass123",
            full_name="Test User",
        )

    def test_login_success_redirects_to_dashboard(self):
        # to'g'ri telefon va parol bilan kirsa, dashboard'ga yo'naltiriladi
        response = self.client.post(self.login_url, {
            "phone": "+998901234567",
            "password": "StrongPass123",
        })
        self.assertRedirects(response, reverse("dashboard"))

    def test_login_wrong_password_shows_error(self):
        # noto'g'ri parol bilan kirsa, xato xabari chiqadi
        response = self.client.post(self.login_url, {
            "phone": "+998901234567",
            "password": "wrong-password",
        })
        self.assertEqual(response.status_code, 200)
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("noto'g'ri", str(messages[0]))
