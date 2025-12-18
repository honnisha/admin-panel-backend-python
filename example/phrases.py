
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
        'created_at': 'Время создания',
        'graphs_example': 'Пример графиков',
        'amount': 'Сумма',
        'registry_checked': 'Реестр проверен',
        'registry_info_checked': 'Информация по реестру провайдера',
        'payments': 'Платежи',
        'statistics': 'Статистика',
        'image': 'Изображение',
        'delete': 'Удалить',
        'delete_confirmation_text': 'Вы уверены, что хотите удалить данные записи?\nДанное действие нельзя отменить.',
        'payments_search_fields': 'Доступные поля для поиска: id',
        'create_payment': 'Создать платеж',
        'create_payment_description': 'Создать платеж и отправить его на обработку в платежную систему.',
        'payment_create_result': RU_PAYMENT_CREATE_RESULT,
        'description': 'Описание',
        'status': 'Статус',
        'endpoint': 'Эндпоинт',
        'deleted_successfully': 'Записи успешно удалены.',
        'action_with_exception': 'Действие с ошибкой',
        'is_throw_error': 'Выбросить ошибку?',
        'throw_error': 'Пример ошибки валидации поля.',
        'exception_example': 'Пример ошибки исключения.',
    },
    'en': {
        'admin_title': 'Admin Panel Demo',
        'created_at': 'Created time',
        'graphs_example': 'Graphs example',
        'amount': 'Amount',
        'registry_checked': 'Registry checked',
        'registry_info_checked': 'Registry info checked',
        'payments': 'Payments',
        'statistics': 'Statistics',
        'image': 'Image',
        'delete': 'Delete',
        'delete_confirmation_text': 'Are you sure you want to delete those records?\nThis action cannot be undone.',
        'payments_search_fields': 'Search fields: id',
        'create_payment': 'Create payment',
        'create_payment_description': 'Create a payment and send it to the payment system for processing.',
        'payment_create_result': EN_PAYMENT_CREATE_RESULT,
        'description': 'Description',
        'status': 'Status',
        'endpoint': 'Endpoint',
        'deleted_successfully': 'The entries were successfully deleted.',
        'action_with_exception': 'Action with exception',
        'is_throw_error': 'Is throw error?',
        'throw_error': 'Example of a field validation error.',
        'exception_example': 'Exception example.',
    },
}
