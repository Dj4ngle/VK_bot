# Почта с LMS
daninza7@gmail.com
# ФИО
Овчинников Данила Алексеевич
# Мой telegram
@danilaovchinnikov


В корне проекта нужно создать config.yml файл со следующей структурой:

session:
  key: ключ_сессии
admin:
  email: почта_админа
  password: пароль_админа
database:
  host: адресс_базы
  port: порт_базы
  user: логин_пользователя_базы
  password: пароль_пользователя_базы
  database: названия_базы
bot:
  token: токен_из_вк
  group_id: ид_группы
  bot_id: ид_бота
