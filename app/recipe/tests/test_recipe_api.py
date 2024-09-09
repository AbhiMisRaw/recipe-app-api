"""Test for recipe api"""

import os
import tempfile

from PIL import Image

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)

RECIPE_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Create and return Recipe Details URL."""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def image_upload_url(recipe_id):
    """
    Create and return an image upload url.
    """
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


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
        self.user = create_user(
            email="user@example.com",
            password="testpass1234",
        )
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
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test for creating recipe"""
        payload = {
            "title": "Sample Recipe",
            "time_minutes": 30,
            "price": Decimal("5.99"),
            "steps": "Sample Recipe Steps",
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
            "steps": "Test Update Recipe tasks",
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

    def test_create_recipe_with_new_tags(self):
        """Test for creating a recipe with new tags."""
        payload = {
            "title": "Paneer Butter Masala",
            "time_minutes": 30,
            "price": Decimal("270"),
            "tags": [
                {"name": "Indian food"},
                {"name": "Paneer"},
                {"name": "veg"},
            ],
            "description": "Sample description",
            "steps": "These are the steps below:",
        }

        res = self.client.post(RECIPE_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 3)
        for tag in payload["tags"]:
            exists = recipe.tags.filter(
                name=tag["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test for creating a recipe with existing tag."""

        tag_indian = Tag.objects.create(
            user=self.user,
            name="Indian",
        )
        payload = {
            "title": "Chola Bhatura",
            "time_minutes": 90,
            "price": Decimal("170"),
            "tags": [
                {"name": "Indian"},
                {"name": "Breakfast"},
                {"name": "veg"},
            ],
            "description": "Sample description",
            "steps": "These are the steps below:",
        }
        res = self.client.post(RECIPE_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 3)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload["tags"]:
            exists = recipe.tags.filter(
                name=tag["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating tag when updating a recipe."""
        recipe = create_recipe(user=self.user)
        payload = {"tags": [{"name": "Lunch"}]}
        url = detail_url(recipe_id=recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name="Lunch")
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """test assigning an existing tag when updating a recipe."""
        tag_breakfast = Tag.objects.create(user=self.user, name="Breakfast")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name="Lunch")
        payload = {"tags": [{"name": "Lunch"}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """tags for clearing all tags related to recipe."""

        tag = Tag.objects.create(user=self.user, name="Dessert")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {"tags": []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        """Test creating a recipe with new ingredients."""

        payload = {
            "title": "Cauliflower Tacos",
            "steps": "These are the steps below",
            "time_minutes": 60,
            "price": Decimal("89.40"),
            "ingredients": [
                {"name": "Cauliflower"},
                {"name": "Salt"},
                {"name": "Red Chilli"},
            ],
        }
        res = self.client.post(RECIPE_URL, payload, format="json")
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 3)
        for ingredient in payload["ingredients"]:
            exists = recipe.ingredients.filter(
                user=self.user, name=ingredient["name"]
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self):
        """Test for creating a recipe with existing ingredients."""
        ingredient = Ingredient.objects.create(user=self.user, name="Lemon")
        payload = {
            "title": "Lemon Water",
            "steps": "These are the steps below",
            "time_minutes": 5,
            "price": Decimal("10.00"),
            "ingredients": [
                {"name": "Lemon"},
                {"name": "Black Salt"},
            ],
        }
        res = self.client.post(RECIPE_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for ingredient in payload["ingredients"]:
            exists = recipe.ingredients.filter(
                user=self.user, name=ingredient["name"]
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        """
        Test for creating an ingredient when updating a recipe.
        """

        recipe = create_recipe(user=self.user)

        payload = {"ingredients": [{"name": "Limes"}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredients = Ingredient.objects.get(
            user=self.user,
            name="Limes",
        )
        self.assertIn(new_ingredients, recipe.ingredients.all())

    def test_update_recipe_assign_ingredients(self):
        """
        Test for updating ingredients.
        """
        ingredient1 = Ingredient.objects.create(
            user=self.user,
            name="Pepper",
        )
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(
            user=self.user,
            name="Chilli",
        )
        payload = {"ingredients": [{"name": "Chilli"}]}
        url = detail_url(recipe_id=recipe.id)
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """
        Test for creating and clearing all ingredients.
        """
        ingdt = Ingredient.objects.create(
            user=self.user,
            name="Garlic",
        )
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingdt)

        payload = {"ingredients": []}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)

    def test_filter_by_tags(self):
        """
        Test filtering recipes by tags.
        """
        r1 = create_recipe(user=self.user, title="Thai vegetable curry")
        r2 = create_recipe(user=self.user, title="Kachori")
        tag1 = Tag.objects.create(user=self.user, name="Vegan")
        tag2 = Tag.objects.create(user=self.user, name="Vegetarian")
        r1.tags.add(tag1)
        r2.tags.add(tag2)
        r3 = create_recipe(user=self.user, title="Veg Soya Biryani")
        params = {"tags": f"{tag1.id},{tag2.id}"}
        res = self.client.get(RECIPE_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_ingredients(self):
        """
        Test filtering recipes by ingredients.
        """
        r1 = create_recipe(user=self.user, title="Veg Samosa")
        r2 = create_recipe(user=self.user, title="Ghuziya")
        ingd1 = Ingredient.objects.create(user=self.user, name="Maida Flour")
        ingd2 = Ingredient.objects.create(user=self.user, name="Sugar")
        ingd3 = Ingredient.objects.create(user=self.user, name="potato")
        r1.ingredients.add(ingd1)
        r1.ingredients.add(ingd3)
        r2.ingredients.add(ingd1)
        r2.ingredients.add(ingd2)
        r3 = create_recipe(user=self.user, title="Dhokla")

        params = {"ingredients": f"{ingd1.id},{ingd3.id}"}
        res = self.client.get(RECIPE_URL, params)
        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class ImageUploadTests(TestCase):
    """
    Test for the image upload API.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@example.com",
            "passwrod123",
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self) -> None:
        self.recipe.image.delete()

    def test_upload_image(self):
        """
        Test uploading an image to a recipe.
        """

        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)
            payload = {"image": image_file}
            res = self.client.post(url, payload, format="multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_failed_upload_image(self):
        """
        Test failed uploading an image to a recipe.
        """

        url = image_upload_url(self.recipe.id)
        payload = {"image": "imagefile"}
        res = self.client.post(url, payload, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
