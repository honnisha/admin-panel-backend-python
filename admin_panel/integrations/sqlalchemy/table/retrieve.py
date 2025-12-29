from typing import Any

from admin_panel import auth, schema
from admin_panel.exceptions import AdminAPIException, APIError
from admin_panel.integrations.sqlalchemy.table.base import record_to_dict
from admin_panel.translations import LanguageManager
from admin_panel.translations import TranslateText as _
from admin_panel.utils import get_logger

logger = get_logger()


class SQLAlchemyAdminRetrieveMixin:
    async def retrieve(
            self,
            pk: Any,
            user: auth.UserABC,
            language_manager: LanguageManager,
    ) -> schema.RetrieveResult:
        # pylint: disable=import-outside-toplevel
        from sqlalchemy import inspect

        col = inspect(self.model).mapper.columns[self.pk_name]
        python_type = col.type.python_type

        assert self.pk_name
        stmt = self.get_queryset().where(getattr(self.model, self.pk_name) == python_type(pk))

        try:
            async with self.db_async_session() as session:
                record = (await session.execute(stmt)).scalars().first()
                data = await self.table_schema.serialize(
                    record_to_dict(record),
                    extra={"record": record, "user": user},
                )
                return schema.RetrieveResult(data=data)

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
