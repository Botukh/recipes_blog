from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin, Group
from django.utils.safestring import mark_safe

from recipes.models import (
    User,
    Tag,
    Product,
    Recipe,
    RecipeProduct,
    Favorite,
    ShoppingCart,
    Subscription,
)

admin.site.unregister(Group)


class RecipeProductInline(admin.TabularInline):
    model = RecipeProduct
    extra = 1
    autocomplete_fields = ("product",)
    min_num = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "recipe_count")
    search_fields = ("name", "slug")
    readonly_fields = ("recipe_count",)

    @admin.display(description="Рецептов")
    def recipe_count(self, tag):
        return tag.recipe_set.count()


class HasRecipeFilter(admin.SimpleListFilter):
    title = "Есть в рецептах"
    parameter_name = "has_recipes"

    def lookups(self, request, model_admin):
        return (("yes", "Да"), ("no", "Нет"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "yes":
            return queryset.filter(product_recipes__isnull=False).distinct()
        if value == "no":
            return queryset.filter(product_recipes__isnull=True)
        return queryset


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "unit", "recipe_count")
    search_fields = ("name", "unit", "slug")
    list_filter = (HasRecipeFilter,)
    readonly_fields = ("recipe_count",)

    @admin.display(description="Рецептов")
    def recipe_count(self, product):
        return product.product_recipes.count()


class CookingTimeFilter(admin.SimpleListFilter):
    title = "Время готовки"
    parameter_name = "cook_time"

    QUICK = 30
    MEDIUM = 60

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        quick = qs.filter(cooking_time__lt=self.QUICK).count()
        medium = qs.filter(
            cooking_time__gte=self.QUICK, cooking_time__lt=self.MEDIUM).count()
        long = qs.filter(cooking_time__gte=self.MEDIUM).count()
        return (
            ("quick", f"до {self.QUICK} мин ({quick})"),
            ("medium", f"{self.QUICK}-{self.MEDIUM - 1} мин ({medium})"),
            ("long", f"от {self.MEDIUM} мин ({long})"),
        )

    def queryset(self, request, queryset):
        val = self.value()
        if val == "quick":
            return queryset.filter(cooking_time__lt=self.QUICK)
        if val == "medium":
            return queryset.filter(
                cooking_time__gte=self.QUICK,
                cooking_time__lt=self.MEDIUM)
        if val == "long":
            return queryset.filter(cooking_time__gte=self.MEDIUM)
        return queryset


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "cooking_time",
        "author",
        "favorites_count",
        "product_list",
        "image_preview",
    )
    search_fields = (
        "name",
        "author__username",
        "author__email",
    )
    list_filter = ("tags", "author", CookingTimeFilter)
    inlines = (RecipeProductInline,)
    readonly_fields = ("favorites_count", "image_preview")

    @admin.display(description="В избранном")
    def favorites_count(self, recipe):
        return recipe.favorite_set.count()

    @admin.display(description="Продукты")
    def product_list(self, recipe):
        products = recipe.recipe_products.select_related("product")
        return ", ".join(
            f"{rp.product.name} ({rp.measure}{rp.product.unit})"
            for rp in products
        )

    @admin.display(description="Изображение")
    def image_preview(self, recipe):
        if not recipe.image:
            return "-"
        return mark_safe(
            f'<img src="{recipe.image.url}" style="max-height:50px;" />')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'user__email', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
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
    readonly_fields = ("name",)
    can_delete = False
    show_change_link = True


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "id",
        "username",
        "full_name",
        "email",
        "avatar_preview",
        "recipe_count",
        "subscriptions_count",
        "followers_count",
    )
    search_fields = ("username", "email")
    list_filter = ("is_staff", "is_superuser", "is_active")
    readonly_fields = ("avatar_preview",)
    inlines = (RecipeInline,)

    @admin.display(description="ФИО")
    def full_name(self, user):
        return f"{user.first_name} {user.last_name}".strip()

    @admin.display(description="Аватар")
    def avatar_preview(self, user):
        if not user.avatar:
            return "-"
        return mark_safe(
            f'<img src="{user.avatar.url}" style="max-height:40px;" />')

    @admin.display(description="Рецептов")
    def recipe_count(self, user):
        return user.recipes.count()

    @admin.display(description="Подписок")
    def subscriptions_count(self, user):
        return user.subscriptions.count()

    @admin.display(description="Подписчики")
    def followers_count(self, user):
        return user.followers.count()
