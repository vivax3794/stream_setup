import os
import random
import time
import uuid
import json
import subprocess
import asyncio
import threading

from twitchio.ext import commands
from loguru import logger
import httpx
import websockets
from websockets.server import serve

TESTING = True
if TESTING:
    cooldown = lambda *args, **kwargs: lambda f: f
else:
    cooldown = commands.cooldown


TOKEN = os.environ['TOKEN']
CHANNEL = os.environ['CHANNEL']
CLIENT_SECRET = os.environ['CLIENT_SECRET']
CLIENT_ID = os.environ['CLIENT_ID']
OAUTH = os.environ['OAUTH']

# list of words that are not allowed to be used in the prompt
BLACKLIST = [
        "nsfw",
        "pussy",
        "dick",
        "boobs",
        "tits",
        "nude",
        "naked",
        ]

class MultiConsumerChannel:
    def __init__(self):
        self.queues = []

    async def put(self, item):
        await asyncio.gather(*(queue.put(item) for queue in self.queues))

    def get_queue(self):
        queue = asyncio.Queue()
        self.queues.append(queue)
        return queue 

WS_EVENTS = MultiConsumerChannel()

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(token=TOKEN, prefix='?', initial_channels=[CHANNEL])

        self.generating_wallpaper = False

    async def event_ready(self):
        channel = self.get_channel(CHANNEL)
        await channel.send('Hello chat!')
        logger.info(f'Bot is ready')

    async def event_command_error(self, ctx, err):
        logger.error(err);
        await ctx.send(str(err))

    async def event_message(self, msg):
        if msg.author is None: return

        user = await msg.author.user();
        logger.debug(user.profile_image)

        await WS_EVENTS.put({"type": "add_name", "data": {"name": user.name, "display": user.display_name, "profile_image": user.profile_image}})
        await self.handle_commands(msg)

    @commands.command(name='test')
    async def test(self, ctx):
        await ctx.send(f'yes I am fine, {ctx.author.name}!')

    @commands.command(name="help")
    async def help(self, ctx):
        await ctx.send("?wallpaper [prompt] - change my wallpaper to a new ai generated one")
        await ctx.send("?avatar [prompt] - change your avatar to a new ai generated one")
        await ctx.send("?discord - join the discord server")

    @commands.command(name='discord')
    async def discord(self, ctx):
        await ctx.send("Join the discord server: https://discord.gg/9f7p3GQtX2")

    @cooldown(rate=1, per=60, bucket=commands.Bucket.channel)
    @commands.command(name='wallpaper')
    @logger.catch(reraise=True)
    async def wallpaper(self, ctx, *args):
        prompt = " ".join(args)
        if any(word in prompt for word in BLACKLIST):
            await ctx.send("What do you think you are doing?")
            return

        with open("comfyui_workflows/wallpaper.json", "r") as f:
            data = json.load(f)

        data["79"]["inputs"]["stringA"] = prompt
        data["20"]["inputs"]["seed"] = random.randint(0, 1000000)
        data["86"]["inputs"]["seed"] = random.randint(0, 1000000)

        await ctx.send("Generating wallpaper...")
        filename = await execute_workflow(data, "84")
        await ctx.send("Wallpaper generated!") 

        subprocess.run(["swww", "img", f"/images/{filename}", "-t", "any"])
    
        user = await ctx.author.user()
        await WS_EVENTS.put({"type": "wallpaper", "data": ctx.author.display_name})

    @cooldown(rate=1, per=60, bucket=commands.Bucket.user)
    @commands.command(name='avatar')
    @logger.catch(reraise=True)
    async def avatar(self, ctx, *args):
        prompt = " ".join(args)
        if any(word in prompt for word in BLACKLIST):
            await ctx.send("What do you think you are doing?")
            return

        with open("comfyui_workflows/avatar.json", "r") as f:
            data = json.load(f)

        data["9"]["inputs"]["stringA"] = prompt
        data["1"]["inputs"]["seed"] = random.randint(0, 1000000)

        await ctx.send("Generating avatar...")
        filename = await execute_workflow(data, "8")
        await ctx.send("Avatar generated!") 

        url = f"http://localhost:8080/{filename}"
        await WS_EVENTS.put({"type": "update_pfp", "data": {"name": ctx.author.name, "profile_image": url}})

    @commands.command(name='rw')
    async def rw(self, ctx):
        subprocess.run(["swww", "img", "/images/wallpaper/ComfyUI_0001.png", "-t", "any"])
        await ctx.send("Wallpaper reset")

    @commands.command(name='ra')
    async def ra(self, ctx, person):
        user = await self.fetch_users([person])
        user = user[0]
        await WS_EVENTS.put({"type": "update_pfp", "data": {"name": user.name, "profile_image": user.profile_image}})
        await ctx.send("Avatar reset")

    @commands.command(name='test_raid')
    async def test_raid(self, ctx):
        user = await self.fetch_users([ctx.author.name])
        user = user[0]
        await WS_EVENTS.put({"type": "raid", "data": {
            "name": user.name,
            "profile_picture": user.profile_image,
            "viewers": 10
        }})

class EventSub:
    def __init__(self, bot):
        self.bot = bot
    
    async def subscribe(self, id, type_, version):
        logger.info(f"Subscribing to {type_}")
        channel_id = str((await self.bot.fetch_users([CHANNEL]))[0].id)

        async with httpx.AsyncClient() as client:
            response = await client.post('https://api.twitch.tv/helix/eventsub/subscriptions', json={
                "type": type_,
                "version": str(version),
                "condition": {
                    "broadcaster_user_id": channel_id,
                    "moderator_user_id": channel_id,
                    "to_broadcaster_user_id": channel_id
                },
                "transport": {
                    "method": "websocket",
                    "session_id": id,
                }
            }, headers={
                "Client-ID": CLIENT_ID,
                "Authorization": f"Bearer {OAUTH}"
            })
            logger.info(response.json())

    async def connect(self):
        logger.info("Connecting to EventSub")
        async with websockets.connect("wss://eventsub.wss.twitch.tv/ws", extra_headers={
                "Client-ID": CLIENT_ID,
                "Authorization": f"Bearer {OAUTH}"
            }) as ws:
            welcome = json.loads(await ws.recv())
            id = welcome["payload"]["session"]["id"]

            await self.subscribe(id, "channel.follow", 2)
            await self.subscribe(id, "channel.raid", 1)

            while True:
                data = json.loads(await ws.recv())
                logger.info(data)
                if data["metadata"]["message_type"] != "notification": continue
                
                payload = data["payload"]
                if payload["subscription"]["type"] == "channel.follow":
                    channel = self.bot.get_channel(CHANNEL)
                    await channel.send(f"Thank you {payload['event']['user_name']} for following!")

                    user = await self.bot.fetch_users(ids=[payload['event']['user_id']])
                    user = user[0]
                    await WS_EVENTS.put({"type": "follow", "data": {
                        "name": user.name,
                        "display": user.display_name,
                        "profile_image": user.profile_image
                    }})
                elif payload["subscription"]["type"] == "channel.raid":
                    channel = self.bot.get_channel(CHANNEL)
                    await channel.send(f"Thank you {payload['event']['from_broadcaster_user_name']} for the raid!")

                    user = await self.bot.fetch_users(ids=[payload['event']['from_broadcaster_user_id']])
                    user = user[0]
                    await WS_EVENTS.put({"type": "raid", "data": {
                        "name": user.name,
                        "profile_picture": user.profile_image,
                        "viewers": payload['event']['viewers']
                    }})

async def execute_workflow(data, output_node):
    COMFYUI_CLIENT_ID = str(uuid.uuid4())

    async with httpx.AsyncClient() as client:
        response = await client.post('http://comfyui:8188/prompt', json={"prompt": data, "client_id": COMFYUI_CLIENT_ID})
        data = response.json()
        prompt_id = data["prompt_id"]
        logger.info(prompt_id)

        async with websockets.connect(f"ws://comfyui:8188/ws?clientId={COMFYUI_CLIENT_ID}") as ws:
            while True:
                response = await ws.recv()
                if isinstance(response, str):
                    response = json.loads(response)
                    if response["type"] == "executing":
                        data = response["data"]
                        if data["node"] is None and data["prompt_id"] == prompt_id:
                            break

        logger.info("Prompt finished")
        response = await client.get(f'http://comfyui:8188/history/{prompt_id}')
        data = response.json()[prompt_id]["outputs"][output_node]["images"][0]
        logger.info(data)

        filename = data["filename"]
        folder = data["subfolder"] 

        return f"{folder}/{filename}"

def keep_swww_alive():
    subprocess.run(["swww", "kill"])
    while True:
        server = subprocess.Popen(["swww", "init", "--no-cache", "--no-daemon"])
        server.wait()
        logger.warning("swww server died, restarting")

def start_swww():
    threading.Thread(target=keep_swww_alive, daemon=True).start()
    oldest = ""
    oldest_num = 0
    for root, dirs, files in os.walk("/images/wallpaper"):
        for file in files:
            if file.endswith(".png"):
                num = int(file.split(".")[0].split("_")[1])
                if num > oldest_num:
                    oldest = file
                    oldest_num = num
    time.sleep(1)
    subprocess.Popen(["swww", "img", f"/images/wallpaper/{oldest}", "-t", "any"])



async def handle_request(ws):
    logger.info("New connection")
    queue = WS_EVENTS.get_queue()
    while True:
        data = await queue.get()
        await ws.send(json.dumps(data))

async def main():
    logger.info('Starting swww')
    start_swww()

    logger.info('Starting bot')
    bot = Bot()
    eventsub = EventSub(bot)

    async with serve(handle_request, "0.0.0.0", 8000):
        await asyncio.gather(
            bot.start(),
            eventsub.connect()
        )

if __name__ == "__main__":
    asyncio.run(main())
