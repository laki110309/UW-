import discord
from discord.ext import commands
import asyncio
import os

# 環境変数からボットのトークン、チャンネルID、メッセージ内容を取得
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# 環境変数からチャンネルIDをカンマ区切りで取得し、リストに変換
TARGET_CHANNEL_IDS_STR = os.getenv("TARGET_CHANNEL_IDS")
if TARGET_CHANNEL_IDS_STR:
    TARGET_CHANNEL_IDS = [int(id_str.strip()) for id_str in TARGET_CHANNEL_IDS_STR.split(",")]
else:
    TARGET_CHANNEL_IDS = []

FIXED_MESSAGE_CONTENT = os.getenv("FIXED_MESSAGE_CONTENT")

if not TOKEN or not TARGET_CHANNEL_IDS or not FIXED_MESSAGE_CONTENT:
    print("Error: One or more required environment variables (DISCORD_BOT_TOKEN, TARGET_CHANNEL_IDS, FIXED_MESSAGE_CONTENT) are not set.")
    exit(1)

# 必要なインテンツを設定
intents = discord.Intents.default()
intents.message_content = True  # メッセージの内容を読み取るために必要
intents.messages = True         # メッセージイベントをリッスンするために必要

# ボットのインスタンスを作成
bot = commands.Bot(command_prefix="!", intents=intents)

# 各チャンネルの最後に送信したメッセージを保存する辞書
last_bot_messages = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print("Bot is ready.")
    # ボットが起動したら、各チャンネルに初期メッセージを送信
    for channel_id in TARGET_CHANNEL_IDS:
        channel = bot.get_channel(channel_id)
        if channel:
            try:
                # 既存のボットメッセージを検索して削除
                async for message in channel.history(limit=200):
                    if message.author == bot.user and message.content == FIXED_MESSAGE_CONTENT:
                        await message.delete()
                        break
                
                sent_message = await channel.send(FIXED_MESSAGE_CONTENT)
                last_bot_messages[channel_id] = sent_message
                print(f"Initial message sent to channel {channel_id}")
            except discord.Forbidden:
                print(f"Permission denied to send message in channel {channel_id}.")
            except Exception as e:
                print(f"Error sending initial message to channel {channel_id}: {e}")
        else:
            print(f"Channel {channel_id} not found.")

@bot.event
async def on_message(message):
    # ボット自身のメッセージは無視
    if message.author == bot.user:
        return

    # 対象チャンネルからのメッセージか確認
    if message.channel.id in TARGET_CHANNEL_IDS:
        channel_id = message.channel.id
        channel = message.channel

        # 以前にボットが送信したメッセージがあれば削除
        if channel_id in last_bot_messages:
            try:
                await last_bot_messages[channel_id].delete()
                print(f"Previous message deleted in channel {channel_id}.")
            except discord.NotFound:
                print(f"Previous message not found in channel {channel_id}. It might have been deleted manually.")
            except discord.Forbidden:
                print(f"Permission denied to delete message in channel {channel_id}.")
            except Exception as e:
                print(f"Error deleting previous message in channel {channel_id}: {e}")
        
        # 新しいメッセージを送信し、参照を保存
        try:
            sent_message = await channel.send(FIXED_MESSAGE_CONTENT)
            last_bot_messages[channel_id] = sent_message
            print(f"New message sent to channel {channel_id}.")
        except discord.Forbidden:
            print(f"Permission denied to send message in channel {channel_id}.")
        except Exception as e:
            print(f"Error sending new message to channel {channel_id}: {e}")

    await bot.process_commands(message) # コマンド処理を継続するために必要

# ボットを実行
bot.run(TOKEN)
