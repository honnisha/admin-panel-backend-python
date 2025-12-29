from admin_panel import schema
from admin_panel.auth import UserABC
from admin_panel.exceptions import APIError, AdminAPIException
from admin_panel.translations import LanguageManager
from admin_panel.translations import TranslateText as _
from admin_panel.utils import DeserializeAction, get_logger

logger = get_logger()


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
            pk_value = getattr(record, self.pk_name, None)

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
                'SQLAlchemy %s create db error: %s', type(self).__name__,
                e,
                extra={
                    'data': data,
                    'deserialized_data': deserialized_data,
                }
            )
            raise AdminAPIException(
                APIError(message=_('db_error_create'), code='db_error_create'), status_code=500,
            ) from e

        return schema.CreateResult(pk=pk_value)
