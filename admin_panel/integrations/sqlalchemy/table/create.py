from admin_panel import schema
from admin_panel.auth import UserABC
from admin_panel.exceptions import AdminAPIException, APIError
from admin_panel.translations import LanguageManager
from admin_panel.translations import TranslateText as _
from admin_panel.utils import get_logger

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

        try:
            async with self.db_async_session() as session:
                record = await self.table_schema.create(user, data, session)
                pk_value = getattr(record, self.pk_name, None)

        except AdminAPIException as e:
            raise e

        except ConnectionRefusedError as e:
            logger.exception(
                'SQLAlchemy %s create %s db error: %s',
                type(self).__name__, self.table_schema.model.__name__, e,
                extra={'data': data},
            )
            msg = _('connection_refused_error') % {'error': str(e)}
            raise AdminAPIException(
                APIError(message=msg, code='connection_refused_error'),
                status_code=500,
            ) from e

        except IntegrityError as e:
            logger.warning(
                'SQLAlchemy %s create %s db error: %s',
                type(self).__name__, self.table_schema.model.__name__, e,
                extra={'data': data},
            )
            orig = e.orig
            message = orig.args[0] if orig.args else type(orig).__name__
            raise AdminAPIException(
                APIError(message=message, code='db_integrity_error'), status_code=500,
            ) from e

        except Exception as e:
            logger.exception(
                'SQLAlchemy %s create %s db error: %s',
                type(self).__name__, self.table_schema.model.__name__, e,
                extra={'data': data},
            )
            raise AdminAPIException(
                APIError(message=_('db_error_create'), code='db_error_create'), status_code=500,
            ) from e

        logger.info(
            '%s model %s #%s created by %s',
            type(self).__name__, self.table_schema.model.__name__, pk_value, user.username,
            extra={'data': data},
        )
        return schema.CreateResult(pk=pk_value)
