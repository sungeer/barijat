import json

import httpx

from barijat.configs import settings
from barijat.utils import tools
from barijat.utils.http_client import httpx_stream
from barijat.utils.log_util import logger
from barijat.models import message_model, content_model

api_key = settings.ai_api_key
workspace_id = settings.ai_workspace_id
robot_id = settings.ai_robot_id

headers = {
    'Content-Type': 'application/json',
    'Access-key': api_key,
    'Workspace-Id': workspace_id
}


async def get_response(conversation_id, content):
    url = f'{settings.ai_url}/v1/oapi/agent/chat'
    data = {
        'robot_id': robot_id,
        'conversation_id': conversation_id,
        'content': content,
        'response_mode': 'streaming'
    }
    error_msg = {'finish': 'error'}
    try:
        async with httpx_stream.stream('POST', url=url, headers=headers, json=data) as response:
            async for line in response.aiter_lines():
                if not line:
                    continue
                yield line
    except httpx.TimeoutException:
        logger.error(f'ai time out: 【{conversation_id}】')
        yield f'data: {tools.dict_to_json(error_msg)}\n\n'
    except (Exception,):
        logger.opt(exception=True).error(f'ai error 【{conversation_id}】.')
        yield f'data: {tools.dict_to_json(error_msg)}\n\n'


async def stream_data(conversation_id, chat_id, trace_id, content):
    full_content = []
    async for line in get_response(conversation_id, content):
        answer = line.replace('data: ', '')
        try:
            answer = tools.json_to_dict(answer)
        except json.JSONDecodeError:
            continue
        is_error = answer.get('finish')
        if is_error:
            yield f'{is_error}\n'
            break
        if answer.get('type') == 'TEXT' and answer.get('status') == 'SUCCEEDED':
            content = answer.get('content')
            full_content.append(content)
            yield f'{content}\n'

    content_str = ''.join(full_content) if full_content else 'error'
    message_id = await message_model.add_message(chat_id, trace_id, 'robot')
    await content_model.add_content(message_id, content_str)