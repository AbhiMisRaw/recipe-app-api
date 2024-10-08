"""
Test for the Tags aPI.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Tag
from recipe.serializers import TagSerializer
from .test_recipe_api import create_recipe

TAGS_URL = reverse("recipe:tag-list")


def detail_tag_url(tag_id):
    """Create and return a tag detail url."""
    return reverse("recipe:tag-detail", args=[tag_id])


def create_user(email="user@example.com", password="test1234"):
    """Create a user and return it"""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagsAPITest(TestCase):
    """Testr unauthicated API requests."""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        """Testing auth is required for retrieving tags."""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITest(TestCase):
    """Test for authentiucated user."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving a list of tags."""
        Tag.objects.create(user=self.user, name="Vegan")
        Tag.objects.create(user=self.user, name="Dessert")

        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test list of tags is l;imited to authenticated user."""
        user2 = create_user(email="user2@example.com")
        Tag.objects.create(user=user2, name="Fruity")
        tag = Tag.objects.create(user=self.user, name="Strawberry")

        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], tag.name)
        self.assertEqual(res.data[0]["id"], tag.id)

    def test_tags_update(self):
        """Test for udpating tags."""
        tag = Tag.objects.create(user=self.user, name="After dinner")
        payload = {"name": "Dessert"}
        url = detail_tag_url(tag.id)
        res = self.client.patch(url, payload)
        tag.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(tag.name, payload["name"])

    def test_delete_tags(self):
        """Test for deleting tag."""
        tag = Tag.objects.create(user=self.user, name="Breakfast")
        url = detail_tag_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())

    def test_filter_tags_assigned_to_recipe(self):
        """
        Test for Tags to those assigned to recipes.
        """

        tag1 = Tag.objects.create(user=self.user, name="Breakfast")
        tag2 = Tag.objects.create(user=self.user, name="Lunch")

        recipe = create_recipe(user=self.user, title="Chole Bhature")
        recipe.tags.add(tag1)
        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_tags_filter_unique_result(self):
        """
        Test for filter unique tags return a unique list.
        """
        tag1 = Tag.objects.create(user=self.user, name="Breakfast")

        recipe1 = create_recipe(user=self.user, title="Chole Bhature")
        recipe2 = create_recipe(user=self.user, title="Aalo Khasta")

        recipe1.tags.add(tag1)
        recipe2.tags.add(tag1)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)
