from barijat.utils.db_util import db


async def add_message(chat_id, trace_id, sender):
    sql_str = '''
        INSERT INTO 
            messages 
            (chat_id, trace_id, sender) 
        VALUES 
            (:chat_id, :trace_id, :sender)
    '''

    last_id_str = 'SELECT LAST_INSERT_ID()'

    values = {
        'chat_id': chat_id,
        'trace_id': trace_id,
        'sender': sender
    }
    await db.execute(sql_str, values)

    last_id = await db.fetch_one(last_id_str)
    lastrowid = last_id[0]

    return lastrowid

async def get_messages(chat_id):
    sql_str = '''
        SELECT
            trace_id,
            MAX(CASE WHEN sender = 'user' THEN content END) AS 问题,
            MAX(CASE WHEN sender = 'robot' THEN content END) AS 回答,
            MAX(CASE WHEN sender = 'user' THEN created_time END) AS 问题时间,
            MAX(CASE WHEN sender = 'robot' THEN created_time END) AS 回答时间
        FROM
            (
                SELECT
                    m.trace_id, ct.content, m.sender, m.created_time
                FROM
                    chats c
                    LEFT JOIN messages M ON c.id = m.chat_id
                    LEFT JOIN contents CT ON m.id = ct.message_id
                WHERE
                    c.conversation_id = :chat_id
            ) AS subquery
        GROUP BY
            trace_id
        LIMIT 100;
    '''
    values = {'chat_id': chat_id}
    chats = await db.fetch_all(sql_str, values)
    return chats