import uuid
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from .constants import MIN_COOKING_TIME, MIN_MEASURE


username_validator = RegexValidator(
    regex=r'^[\w.@+-]+$',
    message='Username may contain letters, digits and ./@/+/-/_ only.',
)


class User(AbstractUser):
    email = models.EmailField('Email', unique=True, max_length=254)
    username = models.CharField(
        'Username',
        max_length=150,
        unique=True,
        validators=[username_validator],
    )
    avatar = models.ImageField(
        'Avatar', upload_to='recipes/', blank=True, null=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name',
                       'last_name']

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Tag(models.Model):
    name = models.CharField('Название', max_length=128, unique=True)
    slug = models.SlugField('Слаг', max_length=64, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=128)
    unit = models.CharField('Ед. изм.', max_length=32)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'unit'),
                name='ingredient_unique_name_unit',
            ),
        )

    def __str__(self):
        return self.name


author_fk = dict(
    on_delete=models.CASCADE,
    related_name='recipes',
    verbose_name='Автор рецепта',
)

tag_m2m = dict(verbose_name='Теги')
ingredient_m2m = dict(verbose_name='Ингредиенты', through='RecipeIngredient')


class Recipe(models.Model):
    author = models.ForeignKey(User, **author_fk)
    name = models.CharField('Название', max_length=256)
    image = models.ImageField('Изображение', upload_to='recipes/images/')
    text = models.TextField('Описание')
    cooking_time = models.PositiveIntegerField(
        'Время приготовления, мин',
        validators=[MinValueValidator(MIN_COOKING_TIME)],
    )
    tags = models.ManyToManyField(Tag, **tag_m2m)
    ingredients = models.ManyToManyField(Ingredient, **ingredient_m2m)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes',
    )
    measure = models.PositiveIntegerField(
        'Количество',
        validators=[MinValueValidator(MIN_MEASURE)],
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='recipe_ingredient_unique',
            ),
        )


class UserRecipeBase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        abstract = True
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='%(class)s_unique',
            ),
        )

    def __str__(self):
        return f'{self.user} / {self.recipe}'


class Favorite(UserRecipeBase):
    class Meta(UserRecipeBase.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'


class ShoppingCart(UserRecipeBase):
    class Meta(UserRecipeBase.Meta):
        verbose_name = 'Покупка'
        verbose_name_plural = 'Список покупок'


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='subscription_unique',
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='no_self_subscribe',
            ),
        )

    def __str__(self):
        return f'{self.user} → {self.author}'
