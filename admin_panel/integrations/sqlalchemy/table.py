import logging
from typing import Any, Optional

from admin_panel import auth, schema
from admin_panel.auth import UserABC
from admin_panel.exceptions import AdminAPIException, APIError
from admin_panel.integrations.sqlalchemy.fields_schema import SQLAlchemyFieldsSchema
from admin_panel.schema.table.admin_action import ActionData, ActionMessage, ActionResult, admin_action
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


def record_to_dict(record):
    # pylint: disable=import-outside-toplevel
    from sqlalchemy import inspect
    return {
        attr.key: getattr(record, attr.key)
        for attr in inspect(record).mapper.column_attrs
    }


class SQLAlchemyAdminBase(SQLAlchemyAdminAutocompleteMixin, schema.CategoryTable):
    model: Any
    slug = None
    ordering_fields = []
    search_enabled = True

    table_schema: SQLAlchemyFieldsSchema

    db_async_session: Any = None

    def __init__(self, *args, model=None, db_async_session=None, ordering_fields=None, **kwargs):
        if model:
            self.model = model

        if not self.table_schema:
            self.table_schema = SQLAlchemyFieldsSchema(model=self.model)

        stmt = self.get_queryset()
        if not self.model and stmt:
            model = stmt.column_descriptions[0]["entity"]

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

        # pylint: disable=import-outside-toplevel
        from sqlalchemy import inspect
        from sqlalchemy.sql.schema import Column

        for attr in inspect(self.model).mapper.column_attrs:
            col: Column = attr.columns[0]
            if col.primary_key and not self.pk_name:
                self.pk_name = attr.key
                break

        super().__init__(*args, **kwargs)

    def get_queryset(self):
        # pylint: disable=import-outside-toplevel
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        stmt = select(self.model).options(selectinload('*'))

        # Eager-load related fields
        for slug, field in self.table_schema.get_fields().items():

            # pylint: disable=protected-access
            if field._type == "related" and field.rel_name:

                if not hasattr(self.model, field.rel_name):
                    msg = f'Model {self.model.__name__} do not contain rel_name:"{field.rel_name}" for field "{slug}" {field}'
                    raise AttributeError(msg)

                stmt = stmt.options(selectinload(getattr(self.model, field.rel_name)))

        return stmt

    # pylint: disable=too-many-arguments
    async def get_list(
        self,
        list_data: schema.ListData,
        user: auth.UserABC,
        language_manager: LanguageManager,
    ) -> schema.TableListResult:
        # pylint: disable=import-outside-toplevel
        from sqlalchemy import func, select
        from sqlalchemy.orm import load_only, selectinload

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

        stmt = self.get_queryset()

        # Eager-load related fields
        for slug, field in self.table_schema.get_fields().items():
            # pylint: disable=protected-access
            if field._type == "related":
                if hasattr(self.model, slug):
                    stmt = stmt.options(selectinload(getattr(self.model, field.rel_name)))

        data = []
        async with self.db_async_session() as session:
            records = (await session.execute(stmt)).scalars().all()
            for record in records:
                line = await self.table_schema.serialize(
                    record_to_dict(record),
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
        from sqlalchemy import inspect

        col = inspect(self.model).mapper.columns[self.pk_name]
        python_type = col.type.python_type

        assert self.pk_name
        stmt = self.get_queryset().where(getattr(self.model, self.pk_name) == python_type(pk))

        try:
            async with self.db_async_session() as session:
                record = (await session.execute(stmt)).scalars().first()
                return await self.table_schema.serialize(
                    record_to_dict(record),
                    extra={"record": record, "user": user},
                )

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


class SQLAlchemyAdminCreate:
    async def create(
            self,
            data: dict,
            user: UserABC,
            language_manager: LanguageManager,
    ) -> schema.CreateResult:
        # pylint: disable=import-outside-toplevel
        from sqlalchemy.exc import IntegrityError

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

        except IntegrityError as e:
            logger.warning(
                'SQLAlchemy %s create db error: %s', type(self).__name__, e,
            )
            orig = e.orig
            message = orig.args[0] if orig.args else type(orig).__name__
            raise AdminAPIException(
                APIError(message=message, code='db_integrity_error'), status_code=500,
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
        from sqlalchemy import inspect

        if pk is None:
            raise AdminAPIException(
                APIError(message=_('pk_not_found') % {'pk_name': self.pk_name}, code='pk_not_found'),
                status_code=400,
            )

        col = inspect(self.model).mapper.columns[self.pk_name]
        python_type = col.type.python_type

        stmt = self.get_queryset().where(getattr(self.model, self.pk_name) == python_type(pk))

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
