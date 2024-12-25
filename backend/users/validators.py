from django.core.validators import RegexValidator

username_regex_validator = RegexValidator(
    regex=r'^[\w.@+-]+$',
    message='Неверный формат имени пользователя'
)
