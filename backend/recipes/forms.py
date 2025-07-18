from django import forms

from .models import RecipeIngredient, Ingredient


class RecipeIngredientForm(forms.ModelForm):
    unit_display = forms.CharField(
        label='Ед. изм.',
        required=False,
        disabled=True,
        widget=forms.TextInput(attrs={
            'style': 'width: 8em; background-color: #f9f9f9;',
        })
    )

    class Meta:
        model = RecipeIngredient
        fields = ('ingredient', 'amount', 'unit_display')

    def __init__(self, *args, **kwargs):
        """Инициализирует форму RecipeIngredientForm."""
        super().__init__(*args, **kwargs)

        ingredient = None
        if 'ingredient' in self.initial:
            ingredient_id = self.initial['ingredient']
            try:
                ingredient = Ingredient.objects.get(id=ingredient_id)
            except Ingredient.DoesNotExist:
                pass
        if not ingredient and hasattr(self.instance, 'ingredient'):
            ingredient = self.instance.ingredient
        if ingredient:
            self.fields['unit_display'].initial = ingredient.unit
