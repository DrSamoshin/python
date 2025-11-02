from datetime import datetime
import logging
import pytest
from httpx import AsyncClient
from uuid import uuid4
from pydantic import BaseModel, ValidationError
from uuid import UUID


logger = logging.getLogger(__name__)


class UserResponse(BaseModel):
    id: UUID
    apple_id: str
    name: None | str
    email: None | str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # add: bool

class ApiRespose(BaseModel):
    status: str
    data: UserResponse

@pytest.mark.integration
class TestUserApi:

    async def test_get_user(self, client: AsyncClient, db):
        apple_id = f"test_{uuid4()}"
        created_response = await client.post(
            url="/v1/users",
            json={"apple_id": apple_id}
        )

        user_id = created_response.json()["data"]["user"]["id"]
        client.headers.update({
            "Authorization": f"Bearer {created_response.json()["data"]["tokens"]["access_token"]}"
        })

        response = await client.get(url="/v1/users")
        logger.info(response.headers)
        await client.delete(url="/v1/users")
        assert response.status_code == 200

        data = response.json()
        api_response = ApiRespose(**data)
        logger.info(api_response)
        # записываем
        await db.execute("INSERT INTO responses (endpoint, method, response_code, response_body) VALUES (?,?,?,?)", ("/v1/users", "GET", response.status_code, str(data)))
        await db.commit()
        # проверяем
        async with db.execute("SELECT * FROM responses") as cursor:
            rows = await cursor.fetchall()
            logger.info(rows)

        assert api_response.status == "success"
        assert api_response.data.id == UUID(user_id)

        # with pytest.raises(ValidationError) as exc_info:
        #     ApiRespose(**data)


# import responses
# import requests
#
# @responses.activate
# def test_fake_response():
#     responses.add(
#         responses.GET,
#         "http://example.com/api",
#         json={"ok": True},
#         status=200,
#     )
#     resp = requests.get("http://example.com/api")
#     assert resp.json() == {"ok": True}


# import pytest
# import requests
# from jsonschema import validate
#
# user_schema = {
#     "type": "object",
#     "properties": {
#         "id": {"type": "integer"},
#         "name": {"type": "string"},
#         "username": {"type": "string"},
#         "email": {"type": "string", "format": "email"}
#     },
#     "required": ["id", "name", "username", "email"]
# }
#
# @pytest.mark.parametrize("user_id", [1, 2, 3])
# def test_user_schema(user_id):
#     r = requests.get(f"https://jsonplaceholder.typicode.com/users/{user_id}")
#     data = r.json()
#
#     validate(instance=data, schema=user_schema)