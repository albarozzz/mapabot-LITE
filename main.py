#!/usr/bin/env python3.8
import random
import discord
from discord.ext import commands
import os
import settings
import tweepy
from io import BytesIO
import aiohttp
from PIL import Image, ImageOps, ImageEnhance, ImageDraw, ImageFont
import moviepy.editor as mpe
from moviepy.editor import afx
import numpy as np
from loguru import logger
import locale
from yt_dlp import YoutubeDL

locale.setlocale(locale.LC_TIME, "en_US.UTF-8")
ydl_opts = {'format': 'bestaudio/best', 'ext': 'mp3', 'outtmpl': 'music/%(id)s.%(ext)s', 'quiet': True, 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}], 'forceprint': {}, 'print_to_file': {}}

logger.add("main.log", format="{time} | {name} | {level}: {message}", level=settings.level, enqueue=True)

async def download_image(image_url, mimetype="image"):
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as resp:
            if resp.content_type.startswith(mimetype):
                image = await resp.read()
            else:
                return False
    return image


async def get_image(ctx, image_url=None, mimetype="image", limit=11):
    image = None
    msg = await ctx.send(content=f"Cargando... {random.choice(ctx.guild.emojis or [''])} ")
    try:
        if ctx.message.attachments and ctx.message.attachments[0].content_type.startswith(mimetype):
            image = await ctx.message.attachments[0].read()
            return msg, image
    except:
        pass
    if image_url is not None and image is None:
        if not image_url.startswith("http"):
            await msg.edit(content="¿la url no es una url?")
            return msg, False
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.content_type.startswith(mimetype):
                    image = await resp.read()
                else:
                    await msg.edit(content="la url no es una imagen!")
                    return msg, False
    else:
        if image_url is None:
            for _msg in await ctx.channel.history(limit=limit).flatten():
                if _msg.attachments and _msg.attachments[0].content_type.startswith(mimetype):
                    image = await _msg.attachments[0].read()
                    break
    if image is None:
        await msg.edit(content="Error al recolectar la imagen, ¿ninguna imagen encontrada?")
        return msg, False
    return msg, image


intents = discord.Intents.all()
activity = discord.Activity(type=discord.ActivityType.playing, name="the cake is a lie")
bot = commands.Bot(command_prefix="vic!", intents=intents, activity=activity, slash_commands=True, help_command=None, allowed_mentions=discord.AllowedMentions.all())


@bot.event
async def on_ready():
    logger.info("Ready!")
    logger.info(bot.user.name)
    logger.info(bot.user.id)
    logger.info("------")


@bot.event
async def on_command_error(ctx, err):
    if isinstance(err, commands.BotMissingPermissions):
        await ctx.send(f"`{type(err)}`, me faltan los siguientes permisos: **{', '.join(err.missing_permissions)}**")
    elif isinstance(err, commands.MissingPermissions):
        await ctx.send(f"`{type(err)}`, te faltan los siguientes permisos: **{', '.join(err.missing_permissions)}**")
    elif isinstance(err, commands.CommandOnCooldown):
        await ctx.send(f"Comando en cooldown, intente de nuevo en -> `{int(err.retry_after)}` segundos.")
    elif isinstance(err, commands.CommandNotFound):
        await ctx.send(f"El comando no existe, lo siento mucho!")
    else:
        await ctx.send(f"`{err}`")
        logger.exception(err)

@bot.command(aliases=["gl"], brief="Hace un globo de texto a partir de la imagen")
async def globo(ctx, url=commands.Option(None, description='La url de la imagen para hacerle el globo de texto')):
    msg, image = await get_image(ctx, url)
    if not image:
        return

    image = Image.open(BytesIO(image))  # imagen de la captura o de lo que quieras
    image = ImageOps.exif_transpose(image)
    iw, ih = image.size
    _bg = Image.open("assets/globo.jpeg")  # imagen de la plantilla del globo de texto

    h = int((ih / 4) * (iw / ih))
    offset = (0, h)

    new_h = ih + h
    _bg = _bg.resize((iw, h))
    bg = Image.new("RGBA", (iw, new_h), (255, 255, 255, 255))
    bg.paste(_bg, (0, 0))

    image = image.resize((iw, ih))
    bg.paste(image, offset)
    resul = BytesIO()
    await bot.loop.run_in_executor(None, lambda: bg.save(resul, format="png", optimize=True, quality=85))
    resul.seek(0)
    try:
        await msg.edit(content="OK", file=discord.File(resul, filename="unknown.png"), allowed_mentions=discord.AllowedMentions.none())
    except TypeError:
        await ctx.send(content="OK", file=discord.File(resul, filename="unknown.png"))
    bg.close()
    _bg.close()
    image.close()
    resul.close()

@bot.command(aliases=["esp"], brief="Hace un efecto espejo a la imagen")
async def espejin(ctx, url=commands.Option(None, description='La url de la imagen')):
    msg, image = await get_image(ctx, url)
    if not image:
        return

    image1 = Image.open(BytesIO(image))  # imagen de la captura o de lo que quieras
    image1 = ImageOps.exif_transpose(image1)
    iw, ih = image1.size

    image1 = image1.crop((0, 0, int(iw/2), ih))
    bg = Image.new("RGBA", (int(iw/2)*2, int(ih/2)*2), (255, 255, 255, 255))
    bg.paste(image1, (0, 0))
    image2 = image1.transpose(Image.FLIP_LEFT_RIGHT)
    bg.paste(image2, (image1.size[0], 0))

    resul = BytesIO()
    await bot.loop.run_in_executor(None, lambda: bg.save(resul, format="png", optimize=True, quality=85))
    resul.seek(0)
    try:
        await msg.edit(content="OK", file=discord.File(resul, filename="unknown.png"))
    except TypeError:
        await ctx.send(content="OK", file=discord.File(resul, filename="unknown.png"))
    bg.close()
    image1.close()
    image2.close()
    resul.close()

@bot.command(aliases=["ss"], brief="Sobresatura la imagen")
async def sobresaturar(ctx, url=commands.Option(None, description='La url de la imagen')):
    msg, image = await get_image(ctx, url)
    if not image:
        return

    image = Image.open(BytesIO(image))  # imagen de la captura o de lo que quieras
    image = ImageOps.exif_transpose(image)

    image = ImageEnhance.Sharpness(image).enhance(10)
    image = ImageEnhance.Color(image).enhance(5)
    image = ImageEnhance.Brightness(image).enhance(0.11)
    image = ImageEnhance.Contrast(image).enhance(10)

    resul = BytesIO()
    await bot.loop.run_in_executor(None, lambda: image.save(resul, format="png", optimize=True, quality=85))
    resul.seek(0)
    try:
        await msg.edit(content="OK", file=discord.File(resul, filename="unknown.png"))
    except TypeError:
        await ctx.send(content="OK", file=discord.File(resul, filename="unknown.png"))
    image.close()
    resul.close()

@bot.command(aliases=["con"], brief="Concadena 2 imagenes")
async def concadenar(ctx):

    msg = await ctx.send(f"Cargando... {random.choice(ctx.guild.emojis or [''])} ")
    check = None
    image1 = None
    image2 = None
    for _msg in await ctx.channel.history(limit=10).flatten():
        if _msg.attachments and _msg.attachments[0].content_type.startswith("image"):
            image1 = await _msg.attachments[0].read()
            check = _msg.id
            break
    for _msg in await ctx.channel.history(limit=20).flatten():
        if _msg.attachments and _msg.attachments[0].content_type.startswith("image") and check != _msg.id:
            image2 = await _msg.attachments[0].read()
            break

    if not image1 or not image2:
        return msg.edit(content="No se encontraron imagenes")

    image1 = Image.open(BytesIO(image1)).convert("RGB")
    image2 = Image.open(BytesIO(image2)).convert("RGB")

    image1 = ImageOps.exif_transpose(image1)
    image2 = ImageOps.exif_transpose(image2)

    iw, ih = image1.size  # la segunda
    w, h = image2.size  # la primera

    image1 = image1.resize((w, int(ih / (iw / w))))
    iw, ih = image1.size  # la segunda
    w, h = image2.size  # la primera

    bg = Image.new("RGB", (w, h+ih), (255, 255, 255))

    bg.paste(image2, (0, 0))
    bg.paste(image1, (0, h))

    resul = BytesIO()
    await bot.loop.run_in_executor(None, lambda: bg.save(resul, format="png", optimize=True, quality=85))
    resul.seek(0)
    try:
        await msg.edit(content="OK", file=discord.File(resul, filename="unknown.png"))
    except TypeError:
        await ctx.send(content="OK", file=discord.File(resul, filename="unknown.png"))
    bg.close()
    image1.close()
    image2.close()
    resul.close()

@bot.command(aliases=["z"], brief="Hace un videomeme a partir de la imagen")
@commands.cooldown(1, 30, commands.BucketType.member)
async def zzz(ctx, url=commands.Option(description='La url de la música para hacerle el meme'),
              image_url=commands.Option(None, description='La url de la imagen para hacerle el meme'),
              start=commands.Option(None,
                                    description='El tiempo inicial seleccionado de la música, por defecto en 00:00'),
              end=commands.Option(None,
                                  description='El tiempo final seleccionado de la música, por defecto en lo que dure'),
              loop=commands.Option(None,
                                   description='Selecciona si loopear la cancion hasta los 30 segundos o lo que dure')):
    msg, image = await get_image(ctx, image_url)

    if not image:
        return

    with YoutubeDL(ydl_opts) as yt:
        info = await bot.loop.run_in_executor(None, lambda: yt.extract_info(url, download=True))

    if info["duration"] > 600:
        return await msg.edit(content="Por favor, seleccione un vídeo con menos de 10 minutos de duración.")
    image = Image.open(BytesIO(image))
    fileid = random.randint(0, 10000)
    path = info["requested_downloads"][0]["filepath"]
    logo = (mpe.ImageClip(np.array(image)))
    audio_bg = mpe.AudioFileClip(path)
    final = mpe.CompositeVideoClip([logo.set_duration(audio_bg.duration)])
    length = None
    if start or end:
        audio_bg = audio_bg.subclip(start, end)
        length = audio_bg.duration if audio_bg.duration < 30 else 30
    length = length or audio_bg.duration if audio_bg.duration < 30 else 30
    if loop:
        length = 30
        final = final.set_audio(afx.audio_loop(audio_bg, duration=30))
    else:
        final = final.set_audio(audio_bg.set_duration(length))
    final = final.set_duration(length)
    await bot.loop.run_in_executor(None, lambda: final.write_videofile(f"videos/{ctx.channel.id}_{ctx.author.id}_{fileid}.webm", fps=1, verbose=False, logger=None,
                          codec="libvpx"))

    try:
        await msg.edit(content="OK",
                       file=discord.File(f"videos/{ctx.channel.id}_{ctx.author.id}_{fileid}.webm", filename="unknown.webm"))
    except TypeError:
        await ctx.send("OK", file=discord.File(f"videos/{ctx.channel.id}_{ctx.author.id}_{fileid}.webm", filename="unknown.webm"))
    os.remove(f"videos/{ctx.channel.id}_{ctx.author.id}_{fileid}.webm")
    os.remove(path)
    image.close()
    audio_bg.close()
    final.close()
    logo.close()

@bot.command(brief="Hace un meme a partir de la url de una imagen")
async def meme(ctx, url=commands.Option(None, description='La url de la imagen'),
               top: str=commands.Option(description='El texto de arriba'),
               bottom: str=commands.Option(description='El texto de abajo')):
    image = None
    if url is None:
        for _msg in await ctx.channel.history(limit=11).flatten():
            if _msg.attachments and _msg.attachments[0].content_type.startswith("image"):
                image = _msg.attachments[0].url
                break
    else:
        image = url
    if image is None:
        return await ctx.send("Error al recolectar la imagen")
    top = top.replace(" ", "_")
    bottom = bottom.replace(" ", "_")
    link = "http://memegen.link/custom/{0}/{1}.jpg?alt={2}".format(top, bottom, image)
    bytes = BytesIO(await download_image(link))
    await ctx.send(file=discord.File(bytes, filename="unknown.jpg"))
    bytes.close()

@bot.command(brief="Hace el meme de I'M FINE a partir de una imagen y un texto")
async def imf(ctx, *, text: str=commands.Option(description='El texto de la imagen')):
    msg, image = await get_image(ctx)
    if not image:
        return
    image = Image.open(BytesIO(image))
    image = ImageOps.exif_transpose(image)
    image2 = Image.open("assets/fine.jpg")

    iw, ih = image2.size  # la segunda

    image = image.resize((iw, ih))
    image = image.crop((int(iw/2), 0, iw, ih))

    bg = Image.new("RGB", (iw, ih), (255, 255, 255))

    bg.paste(image2, (0, 0))
    bg.paste(image, (int(iw/2), 0))

    draw = ImageDraw.Draw(bg)

    font = ImageFont.truetype("tnr.ttf", 50)
    draw.text((245, 420), text, font=font, align="left", stroke_width=2, stroke_fill="black")


    resul = BytesIO()
    await bot.loop.run_in_executor(None, lambda: bg.save(resul, format="png", optimize=True, quality=85))
    resul.seek(0)
    try:
        await msg.edit(content="OK", file=discord.File(resul, filename="unknown.png"))
    except TypeError:
        await ctx.send(content="OK", file=discord.File(resul, filename="unknown.png"))
    bg.close()
    image.close()
    image2.close()
    resul.close()

@bot.command(brief="Hace el meme de I'M FINE pero sin el fine a partir de una imagen y un texto")
async def im(ctx, *, text: str=commands.Option(description='El texto de la imagen')):
    msg, image = await get_image(ctx)
    if not image:
        return
    image = Image.open(BytesIO(image))
    image = ImageOps.exif_transpose(image)
    image2 = Image.open("assets/IM.png").convert("RGB")

    iw, ih = image2.size  # la segunda

    image = image.resize((iw, ih))
    image = image.crop((int(iw/2), 0, iw, ih))

    bg = Image.new("RGB", (iw, ih), (255, 255, 255))

    bg.paste(image2, (0, 0))
    bg.paste(image, (int(iw/2), 0))

    draw = ImageDraw.Draw(bg)

    font = ImageFont.truetype("tnr.ttf", 50)
    #draw.rectangle(((197, 408), (243, 469)), fill="black")
    draw.text((192, 420), text, font=font, align="left", stroke_width=2, stroke_fill="black")

    resul = BytesIO()
    await bot.loop.run_in_executor(None, lambda: bg.save(resul, format="png", optimize=True, quality=85))
    resul.seek(0)
    try:
        await msg.edit(content="OK", file=discord.File(resul, filename="unknown.png"))
    except TypeError:
        await ctx.send(content="OK", file=discord.File(resul, filename="unknown.png"))
    bg.close()
    image.close()
    image2.close()
    resul.close()

@bot.command(aliases=["av"], brief="Devuelve el avatar del miembro")
async def avatar(ctx, member: discord.Member = commands.Option(None, description='El miembro para obtener su avatar')):
    try:
        if member is None:
            member = ctx.author
        image = await download_image(member.display_avatar.url)
        image = BytesIO(image)
        await ctx.send(file=discord.File(image, filename="unknown.png"))
        image.close()
    except Exception as e:
        logger.exception("avatar")

bot.run(settings.token)