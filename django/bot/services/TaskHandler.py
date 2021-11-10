from distutils.log import info, debug
import json
import logging
from code import interact
from typing import Tuple

import discord
import emojis
from asgiref.sync import sync_to_async

from bot.discord_models.models import Category, Channel, Guild, Role
from bot.users.models import Member
from currencies.models import Currency, Trade
from currencies.services import (CreateBankEmbed, CreatePaymentEmbed,
                                 CreateTradeEmbed)
from players.models import Player
from responses.models import Response
from teams.models import Team

# from .Dropdown import Dropdown
# from .Button import Button


TEAM_ROLE_COLOUR = discord.Colour.red()

logger = logging.getLogger("bot")


class TaskHandler:
    def __init__(self, view: discord.ui.View, client: discord.Client):
        self.view = view

        if client is None:
            logger.error("Client is None")

        self.client = client

    async def create_dropdown_response(
        self,
        interaction: discord.Interaction,
        options: list[discord.SelectOption],
        do_next: str,
        callback_payload: dict,
    ):
        from .Dropdown import Dropdown

        debug("Options", options)
        debug("Callbackpayload", callback_payload)

        self.view.add_item(
            Dropdown(
                self.client,
                {
                    "placeholder": callback_payload["placeholder"],
                    "min_values": 1,
                    "max_values": 1,
                    "options": options,
                },
                do_next,
                callback_payload,
            )
        )

        await interaction.response.send_message(
            content="_🔽_", view=self.view, ephemeral=True
        )

    async def create_dropdown(self, payload: dict, interaction: discord.Interaction):
        from .Dropdown import Dropdown

        guild_id = payload["guild_id"]
        channel_id = payload["channel_id"]
        dropdown = payload["dropdown"]
        do_next = payload["do_next"]
        callback = payload["callback"]

        options = []

        for option in dropdown["options"]:
            options.append(discord.SelectOption(**option))

        self.view.add_item(
            Dropdown(
                self.client,
                {
                    "placeholder": "Which country do you want to trade with?",
                    "min_values": 1,
                    "max_values": 1,
                    "options": options,
                },
                callback,
                do_next=do_next,
            )
        )
        channel = self.client.get_guild(guild_id).get_channel(channel_id)

        embedVar = discord.Embed(title=" ads", description=" d", color=0x00FF00)

        await channel.send(embed=embedVar, view=self.view)

    async def create_category(self, payload: dict):
        guild_id = payload["guild_id"]

        guild: discord.Guild = self.client.get_guild(guild_id)
        if guild is None:
            logger.error(f"Guild {guild_id} not found")

        everyone_role = guild.default_role

        overwrites = {
            everyone_role: discord.PermissionOverwrite(view_channel=True),
        }

        # Category can either be created for a team or everyone
        if "team_id" in payload:
            team_id = payload["team_id"]

            @sync_to_async
            def get_team(team_id) -> Tuple[Team, Guild, Role]:
                team = Team.objects.get(id=team_id)
                team_guild = team.guild
                team_role = team.role

                return (team, team_guild, team_role)

            team, team_guild, team_role = await get_team(team_id)

            team_role_id = team_role.discord_id
            team_role = guild.get_role(team_role_id)

            overwrites[everyone_role] = discord.PermissionOverwrite(view_channel=False)

            overwrites[team_role] = discord.PermissionOverwrite(view_channel=True)

            category_name = team.name

        else:
            category_name = payload["category_name"]

        category_channel = await guild.create_category(
            category_name,
            overwrites=overwrites,
        )

        if "team_id" in payload:
            team.category, _ = await sync_to_async(Category.objects.get_or_create)(
                discord_id=category_channel.id, guild=team_guild
            )

            await sync_to_async(team.save)()

    async def create_button(
        self, payload: dict, interaction: discord.Interaction = None
    ):
        from .Button import Button

        button_rows = payload["button_rows"]

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

                if "custom_id" in button:
                    options_dict["custom_id"] = button["custom_id"]

                if button["do_next"] == "":
                    logger.error(f"Button {button['label']} has no do_next")

                button = Button(
                    client=self.client,
                    x=button["x"],
                    y=button["y"],
                    options=options_dict,
                    do_next=button["do_next"],
                    callback_payload=button["callback_payload"],
                )

                view.add_item(button)

        params = {}

        if "trade_id" in payload:
            trade_id = payload["trade_id"]
            params["embed"] = await sync_to_async(CreateTradeEmbed.execute)(
                {"trade_id": trade_id}
            )
        elif "payment_id" in payload:
            payment_id = payload["payment_id"]
            params["embed"] = await sync_to_async(CreatePaymentEmbed.execute)(
                {"payment_id": payment_id}
            )
        elif "embed" in payload:
            params["embed"] = discord.Embed(**payload["embed"])
        elif "content" in payload:
            params["content"] = payload["content"]

        if interaction is None:
            guild_id = payload["guild_id"]
            if "channel_id" in payload:
                channel_id = payload["channel_id"]
            elif "team_id" in payload:
                team_id = payload["team_id"]

                @sync_to_async
                def get_channel_id(team_id):
                    return Team.objects.get(id=team_id).menu_channel.discord_id

                channel_id = await get_channel_id(team_id)
            else:
                logger.error("No channel_id or team_id")

            channel = self.client.get_guild(guild_id).get_channel_or_thread(channel_id)

            button_message = await channel.send(**params, view=view)
            return button_message

        else:
            await interaction.response.send_message(**params, view=view, ephemeral=True)

    async def create_channel(self, payload: dict):
        team_id = payload["team_id"]
        channel_bind_model_id = payload["channel_bind_model_id"]

        @sync_to_async
        def get_team(team_id):
            team = Team.objects.get(id=team_id)

            channel = Channel.objects.get(id=channel_bind_model_id)

            return team.category, team.guild, channel

        team_category, team_guild, channel = await get_team(team_id)

        guild = self.client.get_guild(team_guild.discord_id)

        # TODO: Remove fetch needed for cache busting
        category = await guild.fetch_channel(team_category.discord_id)

        text_channel = await guild.create_text_channel(
            channel.name,
            category=category,
        )

        channel.discord_id = text_channel.id

        await sync_to_async(channel.save)()

    async def create_role(self, payload: dict):
        team_id = payload["team_id"]

        @sync_to_async
        def get_team(team_id):
            team = Team.objects.get(id=team_id)
            team_guild = team.guild

            return team, team_guild

        team, team_guild = await get_team(team_id)

        # TODO: Problem with resetting db and running this

        roles = self.client.get_guild(team_guild.discord_id).roles
        role_dict = {}
        for role in roles:
            role_dict[role.name] = role

        role_names = [role.name for role in roles]

        # Check if the team is already in the guild
        if team.name in role_names:
            await role_dict[team.name].delete()

        # Create a role for the team
        role_object = await self.client.get_guild(team_guild.discord_id).create_role(
            name=team.name, hoist=True, mentionable=True, colour=TEAM_ROLE_COLOUR
        )

        new_role, _ = await sync_to_async(Role.objects.get_or_create)(
            discord_id=role_object.id, name=team.name, guild=team_guild
        )

        team.role = new_role
        await sync_to_async(team.save)()

    async def send_message(self, payload: dict):
        player_id = payload["player_id"]
        message = payload["message"]

        player = await sync_to_async(Player.objects.get)(id=player_id)

        discord_user: discord.User = await self.client.fetch_user(
            player.discord_member.discord_id
        )
        discord_message: discord.Message = await discord_user.send(message)

        @sync_to_async
        def update_player(discord_message):
            response = Response.objects.create(question_id=discord_message.id)
            player.responses.add(response)
            player.save()

        await update_player(discord_message)

    async def change_team(self, payload: dict):
        player_id = payload["player_id"]
        new_team_id = payload["new_team_id"]

        @sync_to_async
        def get_models(player_id, new_team_id):
            player = Player.objects.get(id=player_id)
            new_team = Team.objects.get(id=new_team_id)
            teams = [team for team in Team.objects.all()]

            player_guild = player.guild
            discord_member = player.discord_member
            team_role = new_team.role

            return (
                player,
                new_team,
                teams,
                player_guild,
                discord_member,
                team_role,
            )

        (
            player,
            new_team,
            teams,
            player_guild,
            discord_member,
            team_role,
        ) = await get_models(player_id, new_team_id)

        guild: Guild = self.client.get_guild(player_guild.discord_id)

        # TODO: Try to change this to get_member
        discord_member = await guild.fetch_member(discord_member.discord_id)

        # Will remove all roles from the player
        await discord_member.remove_roles(
            *[guild.get_role(team_role.discord_id) for team in teams]
        )

        # Add the new team role
        await discord_member.add_roles(guild.get_role(team_role.discord_id))

        player.team = new_team
        await sync_to_async(player.save)()

    async def create_message(self, payload: dict):
        channel_id = payload["channel_id"]
        message = payload["message"]

        channel = await sync_to_async(Channel.objects.get)(id=channel_id)
        discord_channel = self.client.get_channel(channel.discord_id)

        send_params = {}
        if message == "team_bank_embed":
            embed = send_params["embed"] = await sync_to_async(CreateBankEmbed.execute)(
                {
                    "team_id": payload["team_id"],
                }
            )

            discord_message = await discord_channel.send(embed=embed)

            team = await sync_to_async(Team.objects.get)(id=payload["team_id"])

            team.bank_embed_id = discord_message.id
            await sync_to_async(team.save)()

        # if message == "team_bank_embed":
        #     await sync_to_async(messag)()

    async def create_thread(self, payload: dict):
        from discord.enums import ChannelType

        channel_id = payload["channel_id"]
        message = payload["message"]
        name = payload["name"]

        channel: Channel = await sync_to_async(Channel.objects.get)(id=channel_id)
        discord_channel: discord.TextChannel = self.client.get_channel(
            channel.discord_id
        )

        new_thread = await discord_channel.create_thread(
            name=name,
            type=ChannelType.public_thread,
            # message=discord_message,
            auto_archive_duration=1440,
        )

        # Send the initial message
        await new_thread.send(message)

        return new_thread
