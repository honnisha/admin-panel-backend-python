import pytest

from admin_panel.auth import AuthData
from admin_panel.exceptions import AdminAPIException
from admin_panel import sqlalchemy
from admin_panel.schema.admin_schema import AdminSchemaData
from example.sections.models import User, UserFactory


@pytest.mark.asyncio
async def test_login(sqlite_sessionmaker):
    auth = sqlalchemy.SQLAlchemyJWTAdminAuthentication(
        secret='123',
        db_async_session=sqlite_sessionmaker,
        user_model=User,
    )
    user = await UserFactory(username='123', password='test', is_admin=True)
    result = await auth.login(data=AuthData(username='123', password='test'))
    assert result.user.username == user.username


@pytest.mark.asyncio
async def test_login_not_admin(sqlite_sessionmaker):
    auth = sqlalchemy.SQLAlchemyJWTAdminAuthentication(
        secret='123',
        db_async_session=sqlite_sessionmaker,
        user_model=User,
    )
    await UserFactory(username='123', password='test')
    with pytest.raises(AdminAPIException) as e:
        await auth.login(data=AuthData(username='123', password='test'))

    assert e.value.get_error().code == 'not_an_admin'


@pytest.mark.asyncio
async def test_login_not_found(sqlite_sessionmaker):
    auth = sqlalchemy.SQLAlchemyJWTAdminAuthentication(
        secret='123',
        db_async_session=sqlite_sessionmaker,
        user_model=User,
    )
    with pytest.raises(AdminAPIException) as e:
        await auth.login(data=AuthData(username='123', password='test'))

    assert e.value.get_error().code == 'user_not_found'


@pytest.mark.asyncio
async def test_authenticate(sqlite_sessionmaker):
    auth = sqlalchemy.SQLAlchemyJWTAdminAuthentication(
        secret='123',
        db_async_session=sqlite_sessionmaker,
        user_model=User,
    )
    user = await UserFactory(username='123', password='test', is_admin=True)

    token = auth.get_token(user)
    result_user = await auth.authenticate(headers={'Authorization': f'Token {token}'})
    AdminSchemaData(groups={}, profile=result_user)

    assert result_user.username == user.username


@pytest.mark.asyncio
async def test_authenticate_not_admin(sqlite_sessionmaker):
    auth = sqlalchemy.SQLAlchemyJWTAdminAuthentication(
        secret='123',
        db_async_session=sqlite_sessionmaker,
        user_model=User,
    )
    user = await UserFactory(username='123', password='test')
    with pytest.raises(AdminAPIException) as e:
        token = auth.get_token(user)
        await auth.authenticate(headers={'Authorization': f'Token {token}'})

    assert e.value.get_error().code == 'user_not_found'
