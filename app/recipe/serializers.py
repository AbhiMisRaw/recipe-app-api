"""Serializers for API"""

from rest_framework import serializers

from core.models import Recipe


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for Recipe"""

    class Meta:
        model = Recipe
        fields = ["id", "title", "time_minutes", "price", "link"]
        read_only_fields = ["id"]


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for Recipe Detail View"""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ["description", "steps"]
