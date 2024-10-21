from barijat.utils.tools import jsonify, abort
from barijat.utils import jwt_util
from barijat.utils.schemas import access_token_schema
from barijat.utils.decorators import validate_request
from barijat.models import user_model


@validate_request(access_token_schema)
async def get_access_token(request):
    body = await request.json()
    phone_number = body['phone_number']
    password = body['password']

    db_user = await user_model.get_user_by_phone(phone_number)
    if not db_user:
        return abort(404, 'User not found')

    db_password = db_user.password_hash
    is_pwd = jwt_util.validate_password(password, db_password)
    if not is_pwd:
        return abort(403, 'Incorrect password')

    access_token = jwt_util.generate_token({'id': db_user.id})
    jwt_token = {'access_token': access_token, 'token_type': 'bearer'}
    return jsonify(jwt_token)
