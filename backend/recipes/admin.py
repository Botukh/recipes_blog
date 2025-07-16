from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin, Group
from django.db.models import Min, Max
from django.utils.safestring import mark_safe

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Tag,
    User,
)

admin.site.unregister(Group)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ('ingredient',)
    min_num = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'recipe_count')
    search_fields = ('name', 'slug')
    readonly_fields = ('recipe_count',)

    @admin.display(description='Рецептов')
    def recipe_count(self, tag):
        return tag.recipe_set.count()


class HasRecipeFilter(admin.SimpleListFilter):
    title = 'Есть в рецептах'
    parameter_name = 'has_recipes'
    YES, NO = 'yes', 'no'

    def lookups(self, request, model_admin):
        return ((self.YES, 'Да'), (self.NO, 'Нет'))

    def queryset(self, request, ingredients):
        if self.value() == self.YES:
            return ingredients.filter(
                ingredient_recipes__isnull=False).distinct()
        if self.value() == self.NO:
            return ingredients.filter(ingredient_recipes__isnull=True)
        return ingredients


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'unit', 'recipe_count')
    search_fields = ('name',)
    list_filter = ('unit', HasRecipeFilter)
    readonly_fields = ('recipe_count',)

    @admin.display(description='Рецептов')
    def recipe_count(self, ingredient):
        return ingredient.ingredient_recipes.count()


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время готовки'
    parameter_name = 'cook_time'

    def lookups(self, request, model_admin):
        recipes = model_admin.get_queryset(request)
        cooking_times = recipes.aggregate(
            min_time=Min('cooking_time'),
            max_time=Max('cooking_time'),
        )
        min_time = cooking_times['min_time']
        max_time = cooking_times['max_time']
        if min_time is None or max_time is None:
            return []

        limits = [
            (min_time, min_time + (max_time - min_time) // 3),
            (min_time + (max_time - min_time) // 3,
             min_time + 2 * (max_time - min_time) // 3),
            (min_time + 2 * (max_time - min_time) // 3, max_time + 1)
        ]
        self.ranges = {
            'quick': limits[0],
            'medium': limits[1],
            'long': limits[2],
        }

        return (
            ('quick', f'до {limits[0][1]} мин '
             f'({recipes.filter(cooking_time__range=limits[0]).count()})'),
            ('medium', f'{limits[1][0]}–{limits[1][1] - 1} мин '
             f'({recipes.filter(cooking_time__range=limits[1]).count()})'),
            ('long', f'от {limits[2][0]} мин '
             f'({recipes.filter(cooking_time__range=limits[2]).count()})'),
        )

    def queryset(self, request, recipes):
        if not hasattr(self, 'ranges'):
            return recipes
        val = self.value()
        if val in self.ranges:
            return recipes.filter(cooking_time__range=self.ranges[val])
        return recipes


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'cooking_time',
        'author',
        'favorites_count',
        'ingredient_list',
        'tag_list',
        'image_preview',
    )
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags', 'author', CookingTimeFilter)
    inlines = (RecipeIngredientInline,)
    readonly_fields = ('favorites_count', 'image_preview')

    @admin.display(description='В избранном')
    def favorites_count(self, recipe):
        return recipe.favorite_set.count()

    @admin.display(description='Ингредиенты')
    def ingredient_list(self, recipe):
        return mark_safe('<br>'.join(
            f'{ri.ingredient.name} ({ri.amount}{ri.ingredient.unit})'
            for ri in recipe.ingredient_amounts.select_related('ingredient')
        ))

    @admin.display(description='Теги')
    def tag_list(self, recipe):
        return mark_safe('<br>'.join(tag.name for tag in recipe.tags.all()))

    @admin.display(description='Изображение')
    def image_preview(self, recipe):
        if not recipe.image:
            return '-'
        return f'<img src="{recipe.image.url}" style="max-height:50px;" />'


@admin.register(Favorite, ShoppingCart)
class RecipeRelationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'user__email', 'recipe__name')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = (
        'user__username', 'user__email', 'author__username', 'author__email'
    )


class RecipeInline(admin.TabularInline):
    model = Recipe
    extra = 0
    readonly_fields = ('name',)
    can_delete = False
    show_change_link = True


class HasRelatedFilter(admin.SimpleListFilter):
    def lookups(self, request, model_admin):
        return (('yes', 'Да'), ('no', 'Нет'))

    def queryset(self, request, users):
        value = self.value()
        if value == 'yes':
            return users.filter(**{f'{self.related_name}__isnull': False})
        if value == 'no':
            return users.filter(**{f'{self.related_name}__isnull': True})
        return users


class HasRecipesFilter(HasRelatedFilter):
    title = 'Есть рецепты'
    parameter_name = 'has_recipes'
    related_name = 'recipes'


class HasSubscriptionsFilter(HasRelatedFilter):
    title = 'Есть подписки'
    parameter_name = 'has_subscriptions'
    related_name = 'subscriptions'


class HasFollowersFilter(HasRelatedFilter):
    title = 'Есть подписчики'
    parameter_name = 'has_followers'
    related_name = 'authors'


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        'id',
        'username',
        'full_name',
        'email',
        'avatar_preview',
        'recipe_count',
        'subscriptions_count',
        'followers_count',
    )
    search_fields = ('username', 'email')
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
        HasRecipesFilter,
        HasSubscriptionsFilter,
        HasFollowersFilter,
    )
    readonly_fields = ('avatar_preview',)
    inlines = (RecipeInline,)

    @admin.display(description='ФИО')
    def full_name(self, user):
        return f'{user.first_name} {user.last_name}'.strip()

    @admin.display(description='Аватар')
    def avatar_preview(self, user):
        if not user.avatar:
            return '-'
        return f'<img src="{user.avatar.url}" style="max-height:40px;" />'

    @admin.display(description='Рецептов')
    def recipe_count(self, user):
        return user.recipes.count()

    @admin.display(description='Подписок')
    def subscriptions_count(self, user):
        return user.subscriptions.count()

    @admin.display(description='Подписчики')
    def followers_count(self, user):
        return Subscription.objects.filter(author=user).count()
