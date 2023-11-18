# @Author: https://github.com/Itz-fork
# @Project: https://github.com/Itz-fork/Mega.nz-Bot
# @Version: nightly-0.1
# @Description: Responsible for download function


from os import path, stat, makedirs

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from config import Config
from bot import GLOB_TMP
from bot.lib.megatools import MegaTools
from bot.helpers.files import send_as_guessed, splitit, listfiles, cleanup


@Client.on_message(filters.regex("https?:\/\/mega\.nz\/(file|folder|#)?.+"))
async def dl_from(_: Client, msg: Message):
    # Push info to temp db
    GLOB_TMP[msg.id] = [msg.text, f"{Config.DOWNLOAD_LOCATION}/{msg.id}"]
    await msg.reply(
        "Should' I download it?",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Download ", callback_data=f"dwn_mg-{msg.id}")],
                [InlineKeyboardButton("Info ", callback_data=f"dwn_mg-{msg.id}")],
                [InlineKeyboardButton("Close ❌", callback_data="closeqcb")],
            ]
        ),
    )


@Client.on_callback_query(filters.regex("dwn_mg?.+"))
async def dl_from_cb(client: Client, query: CallbackQuery):
    # Access saved info
    dtmp = GLOB_TMP.pop(int(query.data.split("-")[1]))
    url = dtmp[0]
    dlid = dtmp[1]
    qcid = query.message.chat.id
    # Create unique download folder
    if not path.isdir(dlid):
        makedirs(dlid)
    # Download the file/folder
    resp = await query.edit_message_text(
        """
    ──────▄▀▄─────▄▀▄
    ─────▄█░░▀▀▀▀▀░░█▄ Hey!
    ─▄▄──█░░░░░░░░░░░█──▄▄
    █▄▄█─█░░▀░░┬░░▀░░█─█▄▄█
    ════════════════════════

    ║`Your download is starting...`║""",
        reply_markup=None,
    )
    cli = MegaTools(client)
    f_list = await cli.download(url, qcid, resp.id, path=dlid)
    try:
        await query.edit_message_text(
            """
            Done
            """
        )
    except Exception as e:
        await query.edit_message_text(
            f"""
            {e}
            """
        )
    # Send file(s) to the user
    await resp.edit(
        """
        Uploading
        """
    )
    for file in f_list:
        # Split files larger than 2GB
        if stat(file).st_size > 2040108421:
            await client.edit_message_text(
                qcid,
                resp.id,
                """
            The file you're trying to upload exceeds telegram limits.
            Trying to split the files...
                """,
            )
            splout = f"{dlid}/splitted"
            await splitit(file, splout)
            for file in listfiles(splout):
                await send_as_guessed(client, file, qcid)
            cleanup(splout)
        else:
            await send_as_guessed(client, file, qcid)
    await resp.edit(
        """
        Ight!
        """
    )
    cleanup(dlid)
