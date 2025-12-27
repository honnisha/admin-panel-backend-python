from admin_panel import sqlalchemy
from admin_panel.translations import TranslateText as _
from example.sections.models import Merchant


class MerchantAdmin(sqlalchemy.SQLAlchemyAdmin):
    model = Merchant
    title = _('merchants')
    icon = 'mdi-card-account-details-outline'

    ordering_fields = [
        'id',
        'user_id',
    ]
    search_fields = [
        'id',
        'title',
    ]

    table_schema = sqlalchemy.SQLAlchemyFieldsSchema(
        model=Merchant,
        readonly_fields=[
            'created_at',
        ]
    )
    table_filters = sqlalchemy.SQLAlchemyFieldsSchema(
        model=Merchant,
        fields=[
            'id',
            'user_id',
        ]
    )
