import logging
import uuid

import discord

logger = logging.getLogger("bot")


async def create_button_view(client, button_rows) -> discord.ui.View:
    from .Button import Button

    view = discord.ui.View(timeout=None)

    for row in button_rows:
        for button in row:
            options_dict = {
                "style": button["style"][1],
                "label": button["label"],
                "row": button["y"],
            }

            if "emoji" in button:
                options_dict["emoji"] = button["emoji"]

            if "disabled" in button:
                options_dict["disabled"] = button["disabled"]

            # if "custom_id" in button:
            #     options_dict["custom_id"] = button["custom_id"]
            options_dict["custom_id"] = str(uuid.uuid1())

            if button["do_next"] == "":
                logger.error(f"Button {button['label']} has no do_next")

            button = Button(
                client=client,
                x=button["x"],
                y=button["y"],
                options=options_dict,
                do_next=button["do_next"],
                callback_payload=button["callback_payload"],
            )

            view.add_item(button)

    return view
