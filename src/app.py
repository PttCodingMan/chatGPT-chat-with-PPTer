import PyPtt
import openai
from SingleLog import DefaultLogger as Logger

from src import config

openai.api_key = config.API_KEY


# 清除 PTT 文章裡面之前的回應
def clear_response(text: str):
    content = []

    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith(':'):
            continue
        content.append(line)

    return '\n'.join(content)


# 清除 PTT 文章裡面的簽名檔
def clear_signature(text: str):
    if text.count('--') < 2:
        return text

    for _ in range(2):
        text = text[:text.rfind('\n--')]

    return text


# 将输入的文本发送给 chatGPT，并将结果输出到屏幕上
def chat(text):

    text = f"""你現在扮演一個只會説一句話以內的大學生，正在使用繁體中文與網友說話。請回覆以下句子「{text}」"""

    completions = openai.Completion.create(
        engine="text-davinci-003",
        prompt=text,
        max_tokens=512,
        temperature=0.5,
    )

    # logger.info('ChatGPT: ', completions['choices'])

    message = original_msg = completions.choices[0].text

    # 整理一下內容

    if message.startswith("，"):
        message = message[1:]

    if message.startswith("。"):
        message = message[1:]

    message = message.strip()

    if '：' in message:
        message = message.split('：')[1]

    if '。' in message:
        message = message[:message.rfind('。') + 1]

    if '\n\n' in message:
        message = message[message.rfind('\n\n'):]

    result = message.strip()

    if not result:
        logger.info('ChatGPT no result: ', original_msg)

    return result


if __name__ == '__main__':
    logger = Logger('chatGPT')

    ptt_bot = None

    board = 'Wanted'

    while True:
        try:

            if ptt_bot is None:

                for _ in range(3):
                    try:
                        ptt_bot = PyPtt.API()
                        ptt_bot.login(config.PTT_ID, config.PTT_PW, kick_other_session=True)
                        break
                    except PyPtt.LoginError:
                        logger.info('登入失敗')
                        ptt_bot = None
                    except PyPtt.WrongIDorPassword:
                        logger.info('帳號密碼錯誤')
                        ptt_bot = None
                    except PyPtt.LoginTooOften:
                        logger.info('請稍等一下再登入')
                        ptt_bot = None

                if ptt_bot is None:
                    exit(1)

            current_index = ptt_bot.get_newest_index(
                board=board,
                index_type=PyPtt.NewIndex.BOARD)

            logger.info(f'current_index: {current_index}')

            must_comment_post = None
            comment_count = 0
            for index in range(5):
                post = ptt_bot.get_post(
                    board=board,
                    index=current_index - index
                )

                if post is None:
                    continue

                if post['author'].startswith(config.PTT_ID):
                    continue

                if 'content' not in post:
                    continue

                content = clear_response(post["content"])
                content = clear_signature(content)

                logger.info(f'post content', content)

                response = chat(content)

                logger.info(f'推文', response)

                ptt_bot.comment(board=board, comment_type=PyPtt.CommentType.ARROW, index=current_index - index, content=response)

        finally:
            ptt_bot.logout()

            # break for demo
            # 如果你想一直執行就拿掉，記得記錄一下回過的文 :D
            break

