RU_ADMIN_DESCRIPTION = '''
Используется для демонстрации возможностей управления, настройки и контроля системы.<br>
<br>
Данные и действия в этом режиме не влияют на рабочее окружение.
'''
EN_ADMIN_DESCRIPTION = '''
Used to demonstrate system management, configuration, and monitoring capabilities.
<br><br>
Data and actions in this mode do not affect the production environment.
'''

RU_LOGIN_GREETINGS_MESSAGE = '''
<div class="text-h6 mb-1">
  Демо режим
</div>
<div class="text-caption">
  Логин: admin<br>
  Пароль: admin
</div>
'''
EN_LOGIN_GREETINGS_MESSAGE = '''
<div class="text-h6 mb-1">
  Demo mode
</div>
<div class="text-caption">
  Login: admin<br>
  Password: admin
</div>
'''

RU_PAYMENT_CREATE_RESULT = '''
<h3>Платеж успешно создан!</h3>
%(desctiption)s<br>
<br>
Данные платежа:<br>
gateway_id=%(gateway_id)s<br>
redirect_url: <a href="%(redirect_url)s" target="_blank"/>%(redirect_url)s</a>
'''
EN_PAYMENT_CREATE_RESULT = '''
<h3>The payment was created successfully!</h3>
%(desctiption)s<br>
<br>
Payment details:
gateway_id=%(gateway_id)s<br>
redirect_url: <a href="%(redirect_url)s" target="_blank"/>%(redirect_url)s</a>
'''
LANGUAGES_PHRASES = {
    'ru': {
        'admin_title': 'Admin Panel Демо',
        'admin_description': RU_ADMIN_DESCRIPTION,
        'login_greetings_message': RU_LOGIN_GREETINGS_MESSAGE,
        'created_at': 'Время создания',
        'graphs_example': 'Пример графиков',
        'amount': 'Сумма',
        'registry_checked': 'Реестр проверен',
        'registry_info_checked': 'Информация по реестру провайдера',
        'payments': 'Платежи',
        'statistics': 'Статистика',
        'image': 'Изображение',
        'payments_search_fields': 'Доступные поля для поиска: id',
        'create_payment': 'Создать платеж',
        'create_payment_description': 'Создать платеж и отправить его на обработку в платежную систему.',
        'payment_create_result': RU_PAYMENT_CREATE_RESULT,
        'description': 'Описание',
        'status': 'Статус',
        'endpoint': 'Эндпоинт',
        'action_with_exception': 'Действие с ошибкой',
        'is_throw_error': 'Выбросить ошибку?',
        'throw_error': 'Пример ошибки валидации поля.',
        'exception_example': 'Пример ошибки исключения.',
    },
    'en': {
        'admin_title': 'Admin Panel Demo',
        'admin_description': EN_ADMIN_DESCRIPTION,
        'login_greetings_message': EN_LOGIN_GREETINGS_MESSAGE,
        'created_at': 'Created time',
        'graphs_example': 'Graphs example',
        'amount': 'Amount',
        'registry_checked': 'Registry checked',
        'registry_info_checked': 'Registry info checked',
        'payments': 'Payments',
        'statistics': 'Statistics',
        'create_payment_description': 'Create a payment and send it to the payment system for processing.',
        'image': 'Image',
        'payments_search_fields': 'Search fields: id',
        'create_payment': 'Create payment',
        'payment_create_result': EN_PAYMENT_CREATE_RESULT,
        'description': 'Description',
        'status': 'Status',
        'endpoint': 'Endpoint',
        'action_with_exception': 'Action with exception',
        'is_throw_error': 'Is throw error?',
        'throw_error': 'Example of a field validation error.',
        'exception_example': 'Exception example.',
    },
}
