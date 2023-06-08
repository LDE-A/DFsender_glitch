import os
import time
import shutil
import discord
from pytube import YouTube
from pytube import Playlist
from discord.ext import commands
from pixivpy3 import AppPixivAPI

TOKEN = os.getenv("TOKEN") #自分のDISCORD TOKEN(str)
nitro = "None" #None,Classic,Normalのどれか
refTOKEN = os.getenv("refTOKEN")
myid = int(os.getenv("myid"))
logFile = "/app/artists.txt"
log_channel_id = int(os.getenv("logID"))
general_id = int(os.getenv("genID"))


lib_ver = int(discord.__version__.replace(".",""))
if lib_ver > 174:
    print(lib_ver)
    print("このプログラムはdiscord.pyのバージョンが2.0.0より下である必要があります\npip install discord.py==1.7.3で1.7.3(推奨)のバージョンをインストールしてください")
    input()


client = commands.Bot(command_prefix="",self_bot=True)
path = "/app"
maxFilesize = 26214400 if nitro == "None" else 52428800 if nitro == "Classic" else 524288000
#25mb * 1024 * 1024 discordの計測方法が1000か1024かは調べてない

def api_auth():
    api = AppPixivAPI()
    try:
        api.auth(refresh_token=refTOKEN)
        return api
    except Exception as e:
        return None

@client.event
async def on_ready():
    print("準備完了")
    await client.get_channel(general_id).send("準備完了")
    await client.get_channel(log_channel_id).send("backup",file=discord.File(logFile))

async def on_disconnect():
    print("bot disconnected")

@client.event
async def on_message(message):
    mc = message.content
    ch = client.get_channel(message.channel.id)
    if message.author.id != client.user.id:
        return
    elif mc == "restart":
        await message.reply("bot再起動中")
        await client.close()
    elif mc == "help":
        await message.reply("restart\nhelp\nread\nedit\nedit-replace\npixiv-all")
    elif mc == "read":
        with open(logFile,"r") as f:
            content = f.read()
        if content == "":
            await message.reply("Content is an Empty")
        elif len(content) >= 1998:
            await message.channel.send(file=discord.File(logFile))
        else:
            await message.reply("`" + content + "`")
    elif mc == "edit":
        await message.reply("新しい内容を入力してください")
        newText = await client.wait_for("message")
        newText = newText.content
        await client.get_channel(log_channel_id).send("backup",file=discord.File(logFile))
        with open(logFile,"w") as f:
            f.write(newText)
    elif mc == "edit-replace":
        await message.reply("新しい内容を入力してください\n例:`1234,4321`")
        inputted = await client.wait_for("message")
        inputted = inputted.content
        with open(logFile,"r") as f:
            content = f.read()
        newText = content.replace(inputted.split(",")[0],inputted.split(",")[1])
        await client.get_channel(log_channel_id).send("backup",file=discord.File(logFile))
        with open(logFile,"w") as f:
            f.write(newText)
    elif mc == "pixiv-all":
        users_str = ""
        api = None
        while api is None:
            api = api_auth()
            time.sleep(3)
        #諸々の設定
        me = myid #自分のユーザーid
        temp_folder = "/app" #一時ファイルを保存しておくフォルダパス
        src = r'\\/:*?"<>|.,\'@^!#$%&+[]()=`'

        next_qs = {"user_id":me}
        while next_qs: #フォロー中ユーザー取得
            result_following = api.user_following(**next_qs)
            #async for msgs in client.get_channel(log_channel_id).history():
                #users_str = users_str + "\n" + msgs.content #既にバックアップしたユーザー取得
            #async for msg in client.get_channel(log_channel_id).history(limit=1):
                #Lastmsg_msg = msg
                #Lastmsg = msg.content
            with open(logFile,"r") as f: #既にバックアップしたユーザー取得
                users_str = f.read()
            user_list = users_str.split("\n")
            for user in result_following.user_previews: #ユーザー抽出
                if str(user.user.id) in user_list:
                    msg = f"{user.user.name}:保存済み"
                    print(msg)
                    if log_channel_id is not None:
                        await client.get_channel(log_channel_id).send(msg)
                    continue
                msg = f"{user.user.name}({user.user.id})の作品をバックアップ中..."
                print(msg)
                if log_channel_id is not None:
                    await client.get_channel(log_channel_id).send(msg)

                #if len(Lastmsg) >= 1900:
                    #Lastmsg = str(user.user.id) + "*" #未完了は*
                    #await client.get_channel(log_channel_id).send(Lastmsg)
                #else:
                    #Lastmsg = Lastmsg + "\n" + str(user.user.id) + "*" #未完了は*
                    #await Lastmsg_msg.edit(content=Lastmsg)
                users_str = users_str + "\n" + str(user.user.id) + "*"
                with open(logFile,"w") as f:
                    f.write(users_str)

                channel = await client.get_guild(message.guild.id).create_text_channel(user.user.name,topic=f"https://pixiv.net/users/{user.user.id}")

                next_qs2 = {"user_id":user.user.id}
                while next_qs2:#ユーザーのイラスト取得
                    result_illusts = api.user_illusts(**next_qs2)
                    if result_illusts is None or result_illusts.illusts is None:
                        msg = "result_illusts is None"
                        print(msg)
                        if log_channel_id is not None:
                            await client.get_channel(log_channel_id).send(msg)
                        num = 1
                        while result_illusts is None or result_illusts.illusts is None:
                            if num >= 6:
                                msg = "unknown error,server down?"
                                print(msg)
                                if log_channel_id is not None:
                                    await client.get_channel(log_channel_id).send(msg)
                                continue
                            time.sleep(5)
                            api = api_auth()
                            result_illusts = api.user_illusts(**next_qs2)
                            num += 1
                    for illust in result_illusts.illusts: #イラスト抽出
                        tag_str = ""
                        data = api.illust_detail(illust.id)
                        if data is None or data.illust is None:
                            msg = "data is None"
                            print(msg)
                            if log_channel_id is not None:
                                await client.get_channel(log_channel_id).send(msg)
                            num = 1
                            while data is None or data.illust is None:
                                if num >= 6:
                                    msg = "unknown error,server down?"
                                    print(msg)
                                    if log_channel_id is not None:
                                        await client.get_channel(log_channel_id).send(msg)
                                    continue
                                time.sleep(5)
                                api = api_auth()
                                data = api.illust_detail(illust.id)
                                num += 1
                        else: #1枚目
                            for tag in data.illust.tags: #スペース区切りでタグをstrに
                                tag_str = f"{tag_str} {tag.name}"
                            img_url = data.illust.image_urls.large
                            extention = img_url[img_url.find('master1200.'):]
                            fileName = f"{illust.id}_0{extention}" if data.illust.page_count >= 2 else f"{illust.id}{extention}"
                            api.download(img_url,path=temp_folder,name=fileName)
                            time.sleep(1)
                            text = f"{illust.title}:{illust.id}\n{tag_str}" if data.illust.page_count == 1 else f"{illust.title} 1/{data.illust.page_count}:{illust.id}\n{tag_str}"
                            await channel.send(text,file=discord.File(f"{temp_folder}/{fileName}"))
                            time.sleep(1)
                            print("[o] " + illust.title)
                            os.remove(f"{temp_folder}/{fileName}")
                        if data.illust.page_count >= 2: #2枚以上あれば2枚以降
                            for i in range(data.illust.page_count):
                                if i == 0: continue
                                else:
                                    url = data.illust.meta_pages[i].image_urls.large
                                    extention = url[url.find('master1200.'):]
                                    fileName = f"{illust.id}_{i}{extention}"
                                    api.download(url,path=temp_folder,name=fileName)
                                    time.sleep(1)
                                    await channel.send(f"{illust.title}:{illust.id}\n{i+1}/{data.illust.page_count}",file=discord.File(f"{temp_folder}/{fileName}"))
                                    time.sleep(1)
                                    print("[o] " + illust.title + " " + str(i))
                                    os.remove(f"{temp_folder}/{fileName}")
                    next_qs2 = api.parse_qs(result_illusts.next_url)
                    time.sleep(2)
                users_str = users_str.replace("*","")
                #await Lastmsg_msg.edit(content=Lastmsg)
                with open(logFile,"w") as f:
                    f.write(users_str)
            next_qs = api.parse_qs(result_following.next_url)

client.run(TOKEN,bot=False)
