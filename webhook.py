from flask import request
from flask.wrappers import Response
from CTFd.utils.dates import ctftime
from CTFd.models import Challenges
from discord_webhook import DiscordWebhook, DiscordEmbed
from functools import wraps

import re

ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])
sanreg = re.compile(r'(~|!|@|#|\$|%|\^|&|\*|\(|\)|\_|\+|\`|-|=|\[|\]|;|\'|,|\.|\/|\{|\}|\||:|"|<|>|\?)')
sanitize = lambda m: sanreg.sub(r'\1',m)

def load(app):
    def patch_submission_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not ctftime():
                return f(*args, **kwargs)

            # Make sure request type is "PATCH" https://docs.ctfd.io/docs/api/redoc/#tag/submissions/operation/patch_submissione
            if request.method != "PATCH":
                return f(*args, **kwargs)
            
            result = f(*args, **kwargs)
            if isinstance(result, Response):
                data = result.json
                if not data.get("success") or data['data']['challenge']['category'] != 'IPPON' or data['data']['type'] != 'correct':
                    return result
                username = sanitize(data['data']['user']['name'])
                answer = sanitize(data['data']['provided'])
                challenge = Challenges.query.filter_by(id=data['data']['challenge_id']).first_or_404()
                challenge_name = sanitize(challenge.name)
                challenge_description = sanitize(challenge.description.split('`')[0].strip().replace("<br>", ""))
                
                webhook = DiscordWebhook(url=app.config['DISCORD_WEBHOOK_URL'])
                embed = DiscordEmbed(title="🎉 IPPON! 🎉", description=f"「{username}」が「{challenge_name}」でIPPONを取りました！", color=0xffff00)
                embed.add_embed_field("お題", challenge_description, inline=False)
                embed.add_embed_field("回答", answer, inline=False)
                webhook.add_embed(embed)
                webhook.execute()
            return result
        return wrapper

    app.view_functions['api.submissions_submission'] = patch_submission_decorator(app.view_functions['api.submissions_submission'])
 
