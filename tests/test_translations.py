import pytest

from admin_panel.exceptions import AdminAPIException, APIError, FieldError
from admin_panel.translations import TranslateText as _
from example.main import CustomLanguageManager


@pytest.mark.asyncio
async def test_translate_exception(mocker):
    exception = AdminAPIException(
        error=APIError(
            message=_('admin_title'),
            code='test',
            field_errors={
                'test': FieldError(_('throw_error'))
            },
        ),
        status_code=400,
        error_code='test',
    )
    language_manager = CustomLanguageManager('ru')

    translation = {
        'error': {
            'code': 'test',
            'field_errors': {
                'test': {
                    'code': None,
                    'message': 'Пример ошибки валидации поля.',
                },
            },
            'message': 'Admin Panel Демо',
        },
        'error_code': 'test',
        'status_code': 400,
    }
    assert exception.model_dump(mode='json', context={'language_manager': language_manager}) == translation


@pytest.mark.asyncio
async def test_translate_context(mocker):
    CustomLanguageManager('ru')
    assert str(_('throw_error')) == 'Пример ошибки валидации поля.'
