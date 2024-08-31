"""Test for recipe api"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)

RECIPE_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Create and return Recipe Details URL."""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        "title": "Sample Recipe value",
        "time_minutes": 22,
        "price": Decimal("22.5"),
        "description": "Sample Description of recipe",
        "steps": "Sampele Recipe Steps",
        "link": "www.example.com/recipe.pdf",
    }
    defaults.update(params)
    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """Test unaunticated API request"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITest(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user(email="user@example.com", password="testpass1234")
        self.client.force_authenticate(self.user)

    def test_retrive_recipes(self):
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to authenticated user."""
        other_user = create_user(email="other@example.com", password="test123")
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test for retrieving a recipe"""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.get(detail_url(recipe.id))

        serializer = RecipeSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test for creating recipe"""
        payload = {
            "title": "Sample Recipe",
            "time_minutes": 30,
            "price": Decimal("5.99"),
            # "steps": "Sample Recipe Steps",
        }
        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update of a recipe"""
        original_link = "www.example.com/reciepe.pdf"
        recipe = create_recipe(
            user=self.user, title="Sample Recipe title", link=original_link
        )
        payload = {"title": "New Recipe Title Update Test"}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Test full update of a recipe"""
        original_link = "www.example.com/reciepe.pdf"
        recipe = create_recipe(
            user=self.user,
            title="Sample Recipe title",
            link=original_link,
            description="Sample description",
            time_minutes=10,
        )
        updated_link = "www.example.com/update/reciepe.pdf"
        payload = {
            "title": "New Recipe Title Update Test",
            "link": updated_link,
            "description": "Updated Test recipe description",
            "time_minutes": 40,
            "price": Decimal("19.50"),
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_error(self):
        """Test for changing user results an error"""
        new_user = create_user(email="other@gmail.com", password="test123")
        recipe = create_recipe(user=self.user)
        payload = {"user": new_user.id}
        url = detail_url(recipe_id=recipe.id)
        self.client.patch(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test for deleteing recipe"""
        recipe = create_recipe(self.user)
        url = detail_url(recipe_id=recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_recipe_other_user_delete(self):
        """Test for other user's recipe's delete error"""
        new_user = create_user(email="user2@example.com", password="1234test")
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())
