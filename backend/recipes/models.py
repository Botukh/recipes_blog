from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from .constants import MIN_COOKING_TIME, MIN_INGREDIENT_AMOUNT


username_validator = RegexValidator(
    regex=r'^[\w.@+-]+$',
    message='Username may contain letters, digits and ./@/+/-/_ only.',
)


class User(AbstractUser):
    email = models.EmailField('Почта', unique=True, max_length=254)
    username = models.CharField('Логин', max_length=150, unique=True)
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    avatar = models.ImageField(
        'Аватар', upload_to='users/', blank=True, null=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Tag(models.Model):
    name = models.CharField('Название', max_length=32, unique=True)
    slug = models.SlugField('Слаг', max_length=32, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=128)
    unit = models.CharField('Ед. изм.', max_length=64)

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


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='recipes', verbose_name='Автор'
    )
    name = models.CharField('Название', max_length=256)
    image = models.ImageField('Изображение', upload_to='recipes/images/')
    text = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (мин)',
        validators=[MinValueValidator(
            MIN_COOKING_TIME,
            message=f'Минимум — {MIN_COOKING_TIME} минута'
        )]
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='ingredient_amounts'
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name='ingredient_amounts'
    )
    amount = models.PositiveIntegerField(
        'Количество',
        validators=[MinValueValidator(
            MIN_INGREDIENT_AMOUNT,
            message=f'Минимум — {MIN_INGREDIENT_AMOUNT}'
        )]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient_per_recipe'
            )
        ]

    def __str__(self):
        return f'{self.ingredient.name} в {self.recipe.name}'


class UserRecipeBase(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='in_%(class)ss',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='in_%(class)ss',
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='%(class)s_unique'
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
        verbose_name='Пользователь'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authors',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            )
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
