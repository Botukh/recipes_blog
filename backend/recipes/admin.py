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
    LOOKUPS = ((YES, 'Да'), (NO, 'Нет'))

    def lookups(self, request, model_admin):
        return self.LOOKUPS

    def queryset(self, request, queryset):
        if self.value() == self.YES:
            return queryset.filter(ingredient_recipes__isnull=False).distinct()
        if self.value() == self.NO:
            return queryset.filter(ingredient_recipes__isnull=True)
        return queryset


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'unit', 'recipe_count')
    search_fields = ('name', 'unit')
    list_filter = ('unit', HasRecipeFilter)
    readonly_fields = ('recipe_count',)

    @admin.display(description='Рецептов')
    def recipe_count(self, ingredient):
        return ingredient.ingredient_recipes.count()


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время готовки'
    parameter_name = 'cook_time'

    def _count(self, time_range, qs=None):
        if qs is None:
            qs = Recipe.objects.all()
        return qs.filter(cooking_time__range=time_range).count()

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        cooking_times = qs.aggregate(
            min_time=Min('cooking_time'),
            max_time=Max('cooking_time')
        )
        min_time = cooking_times['min_time'] or 0
        max_time = cooking_times['max_time'] or 1000

        quick_limit = min_time + (max_time - min_time) // 3
        medium_limit = min_time + 2 * (max_time - min_time) // 3

        self.quick_limit = quick_limit
        self.medium_limit = medium_limit

        return (
            (
                'quick',
                f'до {quick_limit} мин '
                f'({self._count((min_time, quick_limit), qs)})'
            ),
            (
                'medium',
                f'{quick_limit}-{medium_limit - 1} мин '
                f'({self._count((quick_limit, medium_limit), qs)})'
            ),
            (
                'long',
                f'от {medium_limit} мин '
                f'({self._count((medium_limit, max_time + 1), qs)})'
            ),
        )

    def queryset(self, request, queryset):
        val = self.value()
        min_time = queryset.aggregate(min=Min('cooking_time'))['min'] or 0
        max_time = queryset.aggregate(max=Max('cooking_time'))['max'] or 1000

        quick_limit = min_time + (max_time - min_time) // 3
        medium_limit = min_time + 2 * (max_time - min_time) // 3

        ranges = {
            'quick': (min_time, quick_limit),
            'medium': (quick_limit, medium_limit),
            'long': (medium_limit, max_time + 1),
        }

        if val in ranges:
            return queryset.filter(cooking_time__range=ranges[val])
        return queryset


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
        return '\n'.join(
            f'{ri.ingredient.name} ({ri.amount}{ri.ingredient.unit})'
            for ri in recipe.recipe_ingredients.select_related('ingredient')
        )

    @admin.display(description='Теги')
    def tag_list(self, recipe):
        return '\n'.join(tag.name for tag in recipe.tags.all())

    @admin.display(description='Изображение')
    def image_preview(self, recipe):
        if not recipe.image:
            return '-'
        return mark_safe(f'<img src="{recipe.image.url}" style="max-height:50px;" />')


@admin.register(Favorite, ShoppingCart)
class RecipeRelationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'user__email', 'recipe__name')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = (
        'user__username', 'user__email', 'author__username', 'author__email')


class RecipeInline(admin.TabularInline):
    model = Recipe
    extra = 0
    readonly_fields = ('name',)
    can_delete = False
    show_change_link = True


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
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    readonly_fields = ('avatar_preview',)
    inlines = (RecipeInline,)

    @admin.display(description='ФИО')
    def full_name(self, user):
        return f'{user.first_name} {user.last_name}'.strip()

    @admin.display(description='Аватар')
    def avatar_preview(self, user):
        if not user.avatar:
            return '-'
        return mark_safe(f'<img src="{user.avatar.url}" style="max-height:40px;" />')

    @admin.display(description='Рецептов')
    def recipe_count(self, user):
        return user.recipes.count()

    @admin.display(description='Подписок')
    def subscriptions_count(self, user):
        return user.subscriptions.count()

    @admin.display(description='Подписчики')
    def followers_count(self, user):
        return user.followers.count()
