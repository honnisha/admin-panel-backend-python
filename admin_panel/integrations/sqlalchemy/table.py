import datetime
import logging
from typing import Any, Optional

from faker import Faker

from admin_panel import auth, schema
from admin_panel.auth import UserABC
from admin_panel.integrations.sqlalchemy.fields import SQLAlchemyRelatedField
from admin_panel.schema.table.admin_action import ActionData, ActionMessage, ActionResult, admin_action
from admin_panel.translations import LanguageManager
from admin_panel.translations import TranslateText as _
from admin_panel.utils import humanize_field_name

from .autocomplete import SQLAlchemyAdminAutocompleteMixin

logger = logging.getLogger('admin_panel')


class SQLAlchemyFieldsSchema(schema.FieldsSchema):
    model: Any

    def __init__(self, model=None, *args, **kwargs):
        if model:
            self.model = model

        super().__init__(*args, **kwargs)

    def post_init(self, *args, **kwargs):
        super().post_init(*args, **kwargs)

        # pylint: disable=import-outside-toplevel
        from sqlalchemy import inspect
        from sqlalchemy.dialects.postgresql import ARRAY
        from sqlalchemy.sql import sqltypes
        from sqlalchemy.sql.schema import Column

        added_fields = []
        for attr in inspect(self.model).mapper.column_attrs:
            col: Column = attr.columns[0]
            name = attr.key

            if self.fields and name not in self.fields:
                continue

            field_data = {}
            info = col.info or {}
            field_data["label"] = info.get('label', humanize_field_name(name))
            field_data["help_text"] = info.get('help_text')

            field_data["read_only"] = col.primary_key

            # Whether the field is required on input (best-effort heuristic)
            field_data["required"] = (
                not col.nullable
                and col.default is None
                and col.server_default is None
                and not col.primary_key
            )

            if "choices" in info:
                field_data["choices"] = [(c[0], c[1]) for c in info["choices"]]

            col_type = col.type
            try:
                py_t = col_type.python_type
            except Exception:
                py_t = None

            # Foreign key column
            if col.foreign_keys:
                field_class = SQLAlchemyRelatedField

            elif isinstance(col_type, (sqltypes.BigInteger, sqltypes.Integer)) or py_t is int:
                field_class = schema.IntegerField

            elif isinstance(col_type, sqltypes.String) or py_t is str:
                field_class = schema.StringField
                # Max length is usually stored as String(length=...)
                if getattr(col_type, "length", None):
                    field_data["max_length"] = col_type.length

            elif isinstance(col_type, sqltypes.DateTime) or py_t is datetime:
                field_class = schema.DateTimeField

            elif isinstance(col_type, sqltypes.Boolean) or py_t is bool:
                field_class = schema.BooleanField

            elif isinstance(col_type, sqltypes.JSON):
                field_class = schema.JSONField

            elif isinstance(col_type, ARRAY):
                field_class = schema.ArrayField
                field_data["array_type"] = type(col_type.item_type).__name__.lower()

            elif isinstance(col_type, sqltypes.NullType):
                continue

            else:
                msg = f'SQLAlchemy autogenerate ORM field "{name}" is not supported for type: {col_type}'
                raise AttributeError(msg)

            schema_field = field_class(**field_data)
            setattr(self, name, schema_field)
            added_fields.append(name)

        if not self.fields:
            self.fields = added_fields


class SQLAlchemyDeleteAction:
    @admin_action(
        title=_('delete'),
        confirmation_text=_('delete_confirmation_text'),
        base_color='red-lighten-2',
        variant='outlined',
    )
    async def delete(self, action_data: ActionData):
        return ActionResult(message=ActionMessage(_('deleted_successfully')))


class SQLAlchemyAdminBase(SQLAlchemyAdminAutocompleteMixin, schema.CategoryTable):
    model: Any
    slug = None
    ordering_fields = []

    def __init__(self, model=None, ordering_fields=None):
        if model:
            self.model = model

        if ordering_fields:
            self.ordering_fields = ordering_fields

        if not self.table_schema:
            self.table_schema = SQLAlchemyFieldsSchema(model=self.model)

        if not self.slug:
            self.slug = self.model.__name__.lower()

        # pylint: disable=import-outside-toplevel
        from sqlalchemy import inspect
        from sqlalchemy.sql.schema import Column

        for attr in inspect(self.model).mapper.column_attrs:
            col: Column = attr.columns[0]
            if col.primary_key and not self.pk_name:
                self.pk_name = attr.key
                break

        super().__init__()

    def _get_data(self, pk):
        fake = Faker()
        Faker.seed(pk)

        return {
            'user_id': pk,
            'amount': 10 * fake.pyint(min_value=0, max_value=100),
            'endpoint': fake.word(),
            'description': fake.sentence(nb_words=5),
            'image': f'https://picsum.photos/id/{5039-pk+1}/200/300',
            'created_at': datetime.datetime(2025, 6, 16, 9, 45, 29) - datetime.timedelta(hours=pk, minutes=pk),
        }

    async def retrieve(self, pk: Any, user: auth.UserABC) -> Optional[dict]:
        line_data = self._get_data(int(pk))
        line = await self.table_schema.serialize(line_data, extra={'user': user, 'record': line_data})
        return line

    # pylint: disable=too-many-arguments
    async def get_list(
        self, list_data: schema.ListData, user: auth.UserABC, language_manager: LanguageManager
    ) -> schema.TableListResult:
        data = []
        total_count = 5039

        for i in range(0, list_data.limit):
            pk = total_count - ((list_data.page - 1) * list_data.limit + i)
            if pk < 0:
                continue

            line_data = self._get_data(pk)
            line = await self.table_schema.serialize(line_data, extra={'user': user, 'record': line_data})
            data.append(line)

        return schema.TableListResult(data=data, total_count=total_count)


class SQLAlchemyAdminCreate:
    async def create(self, data: dict, user: UserABC) -> schema.CreateResult:
        return schema.CreateResult(pk=0)


class SQLAlchemyAdminUpdate:
    async def update(self, pk: Any, data: dict, user: auth.UserABC) -> schema.UpdateResult:
        return schema.UpdateResult(pk=0)
