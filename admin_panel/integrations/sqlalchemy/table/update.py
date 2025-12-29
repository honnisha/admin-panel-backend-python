from typing import Any

from admin_panel import auth, schema
from admin_panel.exceptions import AdminAPIException, APIError
from admin_panel.translations import LanguageManager
from admin_panel.translations import TranslateText as _
from admin_panel.utils import get_logger

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
        from sqlalchemy.exc import IntegrityError

        if pk is None:
            raise AdminAPIException(
                APIError(message=_('pk_not_found') % {'pk_name': self.pk_name}, code='pk_not_found'),
                status_code=400,
            )

        col = inspect(self.table_schema.model).mapper.columns[self.pk_name]
        python_type = col.type.python_type

        stmt = self.get_queryset().where(getattr(self.model, self.pk_name) == python_type(pk))

        try:
            async with self.db_async_session() as session:
                record = (await session.execute(stmt)).scalars().first()
                if record is None:
                    msg = _('record_not_found') % {'pk_name': self.pk_name, 'pk': pk}
                    raise AdminAPIException(
                        APIError(message=msg, code='record_not_found'),
                        status_code=400,
                    )

                await self.table_schema.update(record, user, data, session)

        except AdminAPIException as e:
            raise e

        except ConnectionRefusedError as e:
            logger.exception(
                'SQLAlchemy %s update %s #%s db connection error: %s',
                type(self).__name__, self.table_schema.model.__name__, pk, e,
                extra={'data': data},
            )
            msg = _('connection_refused_error') % {'error': str(e)}
            raise AdminAPIException(
                APIError(message=msg, code='connection_refused_error'),
                status_code=400,
            ) from e

        except IntegrityError as e:
            logger.warning(
                'SQLAlchemy %s update %s #%s db error: %s',
                type(self).__name__, self.table_schema.model.__name__, pk, e,
                extra={'data': data},
            )
            orig = e.orig
            message = orig.args[0] if orig.args else type(orig).__name__
            raise AdminAPIException(
                APIError(message=message, code='db_integrity_error'), status_code=500,
            ) from e

        except Exception as e:
            logger.exception(
                'SQLAlchemy %s update %s #%s db error: %s',
                type(self).__name__, self.table_schema.model.__name__, pk, e,
                extra={'data': data}
            )
            raise AdminAPIException(
                APIError(message=_('db_error_update'), code='db_error_update'), status_code=500,
            ) from e

        return schema.UpdateResult(pk=pk)
