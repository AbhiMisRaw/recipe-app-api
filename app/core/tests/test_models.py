"""
Tests for models
"""

from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def create_user(email="user@example.com", password="test1234"):
    """Create a user and return it"""
    return get_user_model().objects.create_user(email=email, password=password)


class ModelTests(TestCase):
    """Tests models"""

    def test_create_user_with_email_successfull(self):
        """Tests creating a user with an email is successfull"""
        email = "test@example.com"
        password = "testpass1234"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalize(self):
        """Test email is normalized for new users."""
        sample_email = [
            ["test1@EXAMPLE.com", "test1@example.com"],
            ["Test2@Example.com", "Test2@example.com"],
            ["TEST3@EXAMPLE.COM", "TEST3@example.com"],
            ["test4@example.COM", "test4@example.com"],
        ]
        for email, expected in sample_email:
            user = get_user_model().objects.create_user(
                email,
                "sample123",
            )
            self.assertEqual(user.email, expected)

    def test_user_without_email_raises_error(self):
        """Testing user with no email raises error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "sample123")

    def test_create_superuser(self):
        """Test creating a superuser"""
        user = get_user_model().objects.create_superuser(
            "test@example.com",
            "test123",
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """Test creating a recipe is successfull"""
        user = get_user_model().objects.create_user(
            "test@example.com",
            "testpass123",
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title="Sample recipe name",
            time_minutes=5,
            price=Decimal("5.50"),
            description="Sample Recipe Desciption",
            steps="Sample Recipes Steps.",
        )
        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """Teast for creating a tag"""
        user = create_user()
        tag = models.Tag.objects.create(user=user, name="Tag1")
        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        """Test for creating an ingredieant is successfull."""

        user = create_user()
        ingredient = models.Ingredient.objects.create(
            user=user,
            name="Ingredient 1",
        )
        self.assertEqual(str(ingredient), ingredient.name)

    @patch("core.models.uuid.uuid4")
    def test_recipe_file_name_uuid(self, mock_uuid):
        """
        Test for generating image path.
        """
        uuid = "test-uuid"
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, "example.jpg")

        self.assertEqual(file_path, f"uploads/recipe/{uuid}.jpg")
