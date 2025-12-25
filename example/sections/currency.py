from admin_panel import sqlalchemy
from admin_panel.translations import TranslateText as _
from example.sections.models import Currency


class CurrencyAdmin(sqlalchemy.SQLAlchemyAdmin):
    model = Currency
    title = _('currencies')
    icon = 'mdi-currency-usd'

    table_schema = sqlalchemy.SQLAlchemyFieldsSchema(
        model=Currency,
    )
    table_filters = sqlalchemy.SQLAlchemyFieldsSchema(
        model=Currency,
        fields=[
            'id',
        ]
    )
