import collections
import json
import traceback
from urllib.parse import unquote

from fastapi import FastAPI, Request

from genemoji.src.slack import SlackAPIWrapper
from genemoji.src.env import BOT_TOKEN, TEAM_NAME, SLACK_EMAIL, SLACK_PASSWORD
from genemoji.src.usecases import GENEMOJI_TEXTS, gen_d_upload_emoji

setattr(SlackAPIWrapper, gen_d_upload_emoji.__name__, gen_d_upload_emoji)

app = FastAPI()
slack = SlackAPIWrapper(BOT_TOKEN, TEAM_NAME, SLACK_EMAIL, SLACK_PASSWORD)

app_mention_id_cache = collections.deque([], 100)


@app.get('/')
async def health():
    return ""


@app.post('/')
async def handler(req: Request):
    body = await req.json()
    # print(json.dumps(body, indent=2))
    if body.get("type") == "url_verification":
        return body["challenge"]

    event = body.get("event", {})
    if event.get("type") == "app_mention":
        if "client_msg_id" in event:
            client_msg_id = event["client_msg_id"]
            if client_msg_id in app_mention_id_cache:
                return
            else:
                app_mention_id_cache.append(client_msg_id)
        text = event["text"].encode('unicode-escape').decode(
            'unicode-escape').replace("\xa0", " ")
        channel = event["channel"]
        user = event["user"]
        for genemoji_text in GENEMOJI_TEXTS:
            idx = text.find(genemoji_text)
            if idx >= 0:
                elms = text[idx + len(genemoji_text) + 1:].split(" ")
                if len(elms) < 2:
                    slack.chat_post_message(
                        "後ろに [name] [text] ([color]) が必要です", channel)
                    break
                name = elms[0]
                char = elms[1].replace("\\n", "\n")
                color = None
                if len(elms) > 2 and "<@" not in elms[2]:
                    color = elms[2]
                print(user, name, char, color)

                try:
                    slack.gen_d_upload_emoji(name, char, color)
                except Exception:
                    slack.chat_post_message(
                        "\n".join(
                            ["エラーが発生しました", f"```{traceback.format_exc()}```"]),
                        channel)
                    break

                slack.chat_post_message(f":{name}: を作成しました", channel)
                break
    elif event.get("type") == "message":
        pass
    return


@app.post('/genemoji/')
async def genemoji(req: Request):
    try:
        body = await req.body()
        data = {
            row.split("=")[0]: row.split("=")[1]
            for row in body.decode().split("&")
        }
        # print(json.dumps(data, indent=2))

        user_id = data["user_id"]
        inputs = data["text"].split("+")
        name = inputs[0]
        char = unquote(inputs[1])
        if len(inputs) > 2:
            color = inputs[2]
        else:
            color = None
        print(user_id, name, char, color)

        slack.gen_d_upload_emoji(name, char, color)
    except Exception:
        return {
            "text":
            "\n".join(["エラーが発生しました", f"```{traceback.format_exc()}```"])
        }

    return {"text": f":{name}: を作成しました"}
