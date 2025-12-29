from typing import Any

from admin_panel import auth, schema
from admin_panel.exceptions import AdminAPIException, APIError
from admin_panel.translations import LanguageManager
from admin_panel.translations import TranslateText as _
from admin_panel.utils import DeserializeAction, get_logger

logger = get_logger()


class SQLAlchemyAdminUpdate:
    # pylint: disable=too-many-locals
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
            msg = _('record_not_found') % {'pk_name': self.pk_name, 'pk': pk}
            raise AdminAPIException(
                APIError(message=msg, code='record_not_found'),
                status_code=400,
            )

        for field_slug in data.keys():
            field = self.table_schema.get_field(field_slug)
            if not field:
                available = list(self.table_schema.get_fields().keys())
                msg = _('field_not_fuld_in_schema') % {'field_slug': field_slug, 'available': available}
                raise AdminAPIException(
                    APIError(message=msg, code='field_not_fuld_in_schema'),
                    status_code=400,
                )

        deserialized_data = await self.table_schema.deserialize(
            data,
            action=DeserializeAction.UPDATE,
            extra={"record": record, "model": self.model, "user": user},
        )

        try:
            for k, v in deserialized_data.items():
                setattr(record, k, v)
            async with self.db_async_session() as session:
                await session.commit()

        except ConnectionRefusedError as e:
            logger.exception(
                'SQLAlchemy %s update db connection error: %s', type(self).__name__, e,
            )
            msg = _('connection_refused_error') % {'error': str(e)}
            raise AdminAPIException(
                APIError(message=msg, code='connection_refused_error'),
                status_code=400,
            ) from e

        except Exception as e:
            logger.exception(
                'SQLAlchemy %s update db error: %s',
                type(self).__name__,
                e,
                extra={
                    'data': data,
                    'deserialized_data': deserialized_data,
                }
            )
            raise AdminAPIException(
                APIError(message=_('db_error_update'), code='db_error_update'), status_code=500,
            ) from e

        return schema.UpdateResult(pk=pk)
