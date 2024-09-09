"""
Terst for the ingredients API.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from core.models import (
    Ingredient,
    Recipe,
)

from .test_recipe_api import create_recipe

from recipe.serializers import IngredientSerializer

INGREDIENT_URL = reverse("recipe:ingredient-list")


def detail_url(ingredient_id):
    """
    Helper function for retrieving detail url
    """
    return reverse(
        "recipe:ingredient-detail",
        args=[
            ingredient_id,
        ],
    )


def create_user(
    email="user@example.com",
    password="testpass123",
):
    """Helper function for creating a user."""
    return get_user_model().objects.create(
        email=email,
        password=password,
    )


# def create_recipe(user, **params):
#     """Create and return a sample recipe"""
#     defaults = {
#         "title": "Sample Recipe value",
#         "time_minutes": 22,
#         "price": Decimal("22.5"),
#         "description": "Sample Description of recipe",
#         "steps": "Sampele Recipe Steps",
#         "link": "www.example.com/recipe.pdf",
#     }
#     defaults.update(params)
#     recipe = Recipe.objects.create(user=user, **defaults)
#     return recipe


def create_ingredient(name="Test ingredient"):
    return Ingredient.objects.create(name=name)


class PublicIngredientAPITest(TestCase):
    """Test for unauthenticated API Requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for4 retrievingf ingredients."""
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientAPITest(TestCase):
    """Test for authenticated user."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()

        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving a list of ingredients."""

        Ingredient.objects.create(user=self.user, name="Ingredient A")
        Ingredient.objects.create(user=self.user, name="Ingredient b")

        res = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_limited_to_user(self):
        """Test for ingredients to limited authenticated user."""
        user2 = create_user(email="user2@example.com")
        Ingredient.objects.create(user=user2, name="Salt")
        ingredient = Ingredient.objects.create(
            user=self.user,
            name="Schezwan Sauce",
        )

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], ingredient.name)
        self.assertEqual(res.data[0]["id"], ingredient.id)

    def test_update_ingredient(self):
        """
        Test for updating an ingredient
        """
        ingredient = Ingredient.objects.create(user=self.user, name="Spice")

        payload = {"name": "Red Spice"}
        url = detail_url(ingredient_id=ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload["name"])

    def test_delete_ingredients(self):
        """
        Test for deleting ingredients.
        """
        ingredient = Ingredient.objects.create(
            user=self.user,
            name="Red Chilli",
        )
        url = detail_url(ingredient_id=ingredient.id)

        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())

    def test_filter_ingredients_assigned_to_recipe(self):
        """
        Test listing ingredients by those assigned to recipes.
        """
        ingd2 = Ingredient.objects.create(user=self.user, name="Sugar")
        ingd1 = Ingredient.objects.create(user=self.user, name="potato")
        recipe = Recipe.objects.create(
            title="Aalo Paties",
            time_minutes=5,
            price=Decimal("15.90"),
            user=self.user,
            steps="These are the steps below.",
        )
        recipe.ingredients.add(ingd2)

        res = self.client.get(INGREDIENT_URL, {"assigned_only": 1})
        s2 = IngredientSerializer(ingd2)
        s1 = IngredientSerializer(ingd1)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s1.data, res.data)

    def test_filtered_ingredients_unique(self):
        """
        Test for filtering ingredients returns a unique list.
        """
        ing = Ingredient.objects.create(user=self.user, name="Paneer")
        Ingredient.objects.create(user=self.user, name="Ginger")
        recipe1 = create_recipe(user=self.user, title="Paneer Bhurji")
        recipe2 = create_recipe(user=self.user, title="Paneer Samosa")
        recipe1.ingredients.add(ing)
        recipe2.ingredients.add(ing)

        res = self.client.get(INGREDIENT_URL, {"assigned_only": 1})
        self.assertEqual(len(res.data), 1)
