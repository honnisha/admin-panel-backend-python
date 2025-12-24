import logging
from typing import Any, Optional

from admin_panel import auth, schema
from admin_panel.auth import UserABC
from admin_panel.exceptions import AdminAPIException, APIError
from admin_panel.integrations.sqlalchemy.fields_schema import SQLAlchemyFieldsSchema
from admin_panel.schema.table.admin_action import ActionData, ActionMessage, ActionResult, admin_action
from admin_panel.schema.table.fields.function_field import FunctionField
from admin_panel.translations import LanguageManager
from admin_panel.translations import TranslateText as _
from admin_panel.utils import DeserializeAction

from .autocomplete import SQLAlchemyAdminAutocompleteMixin

logger = logging.getLogger('admin_panel')


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
    search_enabled = True

    db_async_session: Any = None

    def __init__(self, model=None, db_async_session=None, ordering_fields=None):
        if model:
            self.model = model

        if not self.model:
            msg = f'{type(self).__name__}.model is required for SQLAlchemy'
            raise AttributeError(msg)

        if not self.slug:
            self.slug = self.model.__name__.lower()

        if db_async_session:
            self.db_async_session = db_async_session

        if not self.db_async_session:
            msg = f'{type(self).__name__}.db_async_session is required for SQLAlchemy'
            raise AttributeError(msg)

        if ordering_fields:
            self.ordering_fields = ordering_fields

        if not self.table_schema:
            self.table_schema = SQLAlchemyFieldsSchema(model=self.model)

        # pylint: disable=import-outside-toplevel
        from sqlalchemy import inspect
        from sqlalchemy.sql.schema import Column

        for attr in inspect(self.model).mapper.column_attrs:
            col: Column = attr.columns[0]
            if col.primary_key and not self.pk_name:
                self.pk_name = attr.key
                break

        super().__init__()

    # pylint: disable=too-many-arguments
    async def get_list(
        self,
        list_data: schema.ListData,
        user: auth.UserABC,
        language_manager: LanguageManager,
    ) -> schema.TableListResult:
        # pylint: disable=import-outside-toplevel
        from sqlalchemy import func, select
        from sqlalchemy.orm import load_only
        from sqlalchemy.orm import selectinload

        fields = self.table_schema.get_fields()

        # Count
        try:
            async with self.db_async_session() as session:
                total_count = await session.scalar(
                    select(func.count()).select_from(self.model)
                )
        except ConnectionRefusedError as e:
            logger.exception(
                'SQLAlchemy %s get_list db error: %s', type(self).__name__, e,
            )
            msg = _('connection_refused_error') % {'error': str(e)}
            raise AdminAPIException(
                APIError(message=msg, code='connection_refused_error'),
                status_code=500,
            ) from e

        total_count = int(total_count or 0)

        # Fetch rows (optionally only required columns)
        col_names = [
            slug for slug, f in fields.items()
            if not issubclass(f.__class__, FunctionField)
        ]

        stmt = select(self.model)

        # Eager-load related fields
        for slug, field in fields.items():
            if getattr(field, "_type", None) == "related":
                if hasattr(self.model, slug):
                    stmt = stmt.options(selectinload(getattr(self.model, slug)))

        if col_names:
            attrs = [getattr(self.model, name) for name in col_names if hasattr(self.model, name)]
            if attrs:
                stmt = stmt.options(load_only(*attrs))

        async with self.db_async_session() as session:
            records = (await session.execute(stmt)).scalars().all()

        data = []
        for record in records:
            line_data = {}
            for field_slug, field in fields.items():
                if issubclass(field.__class__, FunctionField):
                    continue
                line_data[field_slug] = getattr(record, field_slug)

            line = await self.table_schema.serialize(
                line_data,
                extra={"record": record, "user": user},
            )
            data.append(line)

        return schema.TableListResult(data=data, total_count=total_count)

    async def retrieve(
            self,
            pk: Any,
            user: auth.UserABC,
            language_manager: LanguageManager,
    ) -> Optional[dict]:
        # pylint: disable=import-outside-toplevel
        from sqlalchemy import inspect, select

        col = inspect(self.model).mapper.columns[self.pk_name]
        python_type = col.type.python_type

        assert self.pk_name
        stmt = select(self.model).where(getattr(self.model, self.pk_name) == python_type(pk))

        try:
            async with self.db_async_session() as session:
                record = (await session.execute(stmt)).scalars().first()
        except Exception as e:
            logger.exception(
                'SQLAlchemy %s retrieve db error: %s', type(self).__name__, e,
            )
            raise AdminAPIException(
                APIError(message=_('db_error_retrieve'), code='db_error_retrieve'), status_code=500,
            ) from e

        if record is None:
            msg = _('record_not_found') % {'pk_name': self.pk_name, 'pk': pk}
            raise AdminAPIException(
                APIError(message=msg, code='record_not_found'),
                status_code=400,
            )

        line_data: dict[str, Any] = {}
        for field_slug, field in self.table_schema.get_fields().items():
            if issubclass(field.__class__, FunctionField):
                continue

            line_data[field_slug] = getattr(record, field_slug)

        return await self.table_schema.serialize(
            line_data,
            extra={"record": record, "user": user},
        )


class SQLAlchemyAdminCreate:
    async def create(
            self,
            data: dict,
            user: UserABC,
            language_manager: LanguageManager,
    ) -> schema.CreateResult:
        deserialized_data = await self.table_schema.deserialize(
            data,
            action=DeserializeAction.CREATE,
            extra={'model': self.model, 'user': user},
        )
        try:
            record = self.model(**deserialized_data)
            async with self.db_async_session() as session:
                session.add(record)
                await session.commit()
                await session.refresh(record)

        except ConnectionRefusedError as e:
            logger.exception(
                'SQLAlchemy %s create db error: %s', type(self).__name__, e,
            )
            msg = _('connection_refused_error') % {'error': str(e)}
            raise AdminAPIException(
                APIError(message=msg, code='connection_refused_error'),
                status_code=500,
            ) from e

        except Exception as e:
            logger.exception(
                'SQLAlchemy %s create db error: %s', type(self).__name__, e,
            )
            raise AdminAPIException(
                APIError(message=_('db_error_create'), code='db_error_create'), status_code=500,
            ) from e

        pk_value = getattr(record, self.pk_name, None)
        return schema.CreateResult(pk=pk_value)


class SQLAlchemyAdminUpdate:
    async def update(
            self,
            pk: Any,
            data: dict,
            user: auth.UserABC,
            language_manager: LanguageManager,
    ) -> schema.UpdateResult:
        # pylint: disable=import-outside-toplevel
        from sqlalchemy import inspect, select

        if pk is None:
            raise AdminAPIException(
                APIError(message=_('pk_not_found') % {'pk_name': self.pk_name}, code='pk_not_found'),
                status_code=400,
            )

        col = inspect(self.model).mapper.columns[self.pk_name]
        python_type = col.type.python_type

        stmt = select(self.model).where(getattr(self.model, self.pk_name) == python_type(pk))

        async with self.db_async_session() as session:
            record = (await session.execute(stmt)).scalars().first()

        if record is None:
            return None

        deserialized_data = await self.table_schema.deserialize(
            data,
            action=DeserializeAction.UPDATE,
            extra={"record": record, "model": self.model, "user": user},
        )

        for k, v in deserialized_data.items():
            setattr(record, k, v)

        try:
            async with self.db_async_session() as session:
                await session.commit()

        except ConnectionRefusedError as e:
            logger.exception(
                'SQLAlchemy %s update db error: %s', type(self).__name__, e,
            )
            msg = _('connection_refused_error') % {'error': str(e)}
            raise AdminAPIException(
                APIError(message=msg, code='connection_refused_error'),
                status_code=400,
            ) from e

        except Exception as e:
            logger.exception(
                'SQLAlchemy %s update db error: %s', type(self).__name__, e,
            )
            raise AdminAPIException(
                APIError(message=_('db_error_update'), code='db_error_update'), status_code=500,
            ) from e

        return schema.UpdateResult(pk=pk)


# pylint: disable=too-many-ancestors
class SQLAlchemyAdmin(
        SQLAlchemyAdminUpdate,
        SQLAlchemyAdminCreate,
        SQLAlchemyDeleteAction,
        SQLAlchemyAdminBase,
):
    pass
