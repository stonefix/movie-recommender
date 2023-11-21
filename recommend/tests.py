from django.test import TestCase


class HealthCheckTest(TestCase):
    def test_health_check(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
