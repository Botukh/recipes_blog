from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin, Group
from django.utils.safestring import mark_safe

from .models import (
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
    fields = ('ingredient', 'amount')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'recipe_count')
    search_fields = ('name', 'slug')
    readonly_fields = ('recipe_count',)

    @admin.display(description='Рецептов')
    def recipe_count(self, tag):
        return tag.recipes.count()


class HasRelatedFilter(admin.SimpleListFilter):
    YES = 'yes'
    NO = 'no'

    LOOKUP_CHOICES = (
        (YES, 'Да'),
        (NO, 'Нет'),
    )

    def lookups(self, request, model_admin):
        return self.LOOKUP_CHOICES

    def queryset(self, request, queryset):
        if self.value() == self.YES:
            return queryset.filter(
                **{f'{self.related_name}__isnull': False}
            ).distinct()
        if self.value() == self.NO:
            return queryset.filter(
                **{f'{self.related_name}__isnull': True}
            )
        return queryset


class HasRecipesFilter(HasRelatedFilter):
    title = 'Есть рецепты'
    parameter_name = 'has_recipes'
    related_name = 'recipes'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'unit', 'recipe_count')
    search_fields = ('name', 'unit')
    list_filter = ('unit', HasRecipesFilter)
    readonly_fields = ('recipe_count',)

    @admin.display(description='Рецептов')
    def recipe_count(self, ingredient):
        return ingredient.ingredient_amounts.count()


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время готовки'
    parameter_name = 'cook_time'

    def lookups(self, request, model_admin):
        self.recipes = model_admin.get_queryset(request)

        cooking_times = self.recipes.values_list(
            'cooking_time', flat=True
        ).distinct()

        if len(cooking_times) < 3:
            return []

        min_time = min(cooking_times)
        max_time = max(cooking_times)
        range_step = (max_time - min_time) // 3

        first_limit = min_time + range_step
        second_limit = min_time + 2 * range_step

        self.ranges = {
            'quick': (min_time, first_limit),
            'medium': (first_limit + 1, second_limit),
            'long': (second_limit + 1, max_time),
        }

        return (
            ('quick', f'до {first_limit} мин'
                      f' ({self._get_recipes("quick").count()})'),
            ('medium', f'{first_limit + 1}–{second_limit} мин'
                       f' ({self._get_recipes("medium").count()})'),
            ('long', f'от {second_limit + 1} мин'
                     f' ({self._get_recipes("long").count()})'),
        )

    def _get_recipes(self, key, recipes=None):
        if recipes is None:
            recipes = self.recipes
        return recipes.filter(cooking_time__range=self.ranges[key])

    def queryset(self, request, recipes):
        value = self.value()
        if value in self.ranges:
            return self._get_recipes(value, recipes)
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
        return recipe.in_favorites.count()

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
        return mark_safe(
            f'<img src="{recipe.image.url}" style="max-height:50px;" />'
        )


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

    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Дополнительно', {
            'fields': ('avatar', 'avatar_preview'),
        }),
    )

    @admin.display(description='ФИО')
    def full_name(self, user):
        return f'{user.first_name} {user.last_name}'.strip()

    @admin.display(description='Аватар')
    def avatar_preview(self, user):
        if not user.avatar:
            return '-'
        return mark_safe(
            f'<img src="{user.avatar.url}" style="max-height:40px;" />'
        )

    @admin.display(description='Рецептов')
    def recipe_count(self, user):
        return user.recipes.count()

    @admin.display(description='Подписок')
    def subscriptions_count(self, user):
        return user.subscriptions.count()

    @admin.display(description='Подписчики')
    def followers_count(self, user):
        return user.authors.count()
