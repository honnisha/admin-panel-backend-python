from admin_panel import sqlalchemy
from admin_panel.translations import TranslateText as _
from example.sections.models import Terminal


class TerminalAdmin(sqlalchemy.SQLAlchemyAdmin):
    model = Terminal
    title = _('terminals')
    icon = 'mdi-console-network-outline'

    table_schema = sqlalchemy.SQLAlchemyFieldsSchema(
        model=Terminal,
        list_display=[
            'id',
            'merchant_id',
            'public_id',
            'title',
            'is_h2h',
            'imitation_api',
            'test_mode',
            'is_active',
        ],
    )
    table_filters = sqlalchemy.SQLAlchemyFieldsSchema(
        model=Terminal,
        fields=[
            'id',
        ]
    )
