def update():
    from core.services.database.models import Guild

    for i in Guild.objects.all():
        i.warns_settings.update({
            "state": i.warns_settings["punishment"] is not None,
            "role": {"type": "add", "role_id": None, "time": None}
        })
        i.auto_mod.update({
            "anti_mentions": {
                "state": False,
                "max_mentions": 4,
                "target_roles": [],
                "target_channels": [],
                "ignore_roles": [],
                "ignore_channels": [],
            },
            "anti_link": {
                "state": False,
                "domains": [],
                "target_roles": [],
                "target_channels": [],
                "ignore_roles": [],
                "ignore_channels": [],
            },
            "auto_nick_corrector": {
                "state": False,
                "target_roles": [],
                "ignore_roles": [],
                "replace_with": "New nick",
                "percent": 60
            },
        })
        if "anti_caps" in i.auto_mod.keys():
            i.auto_mod["anti_caps"].update({"min_chars": 10})
            for j in ("target_roles", "target_channels", "ignore_roles", "ignore_channels"):
                if j not in i.auto_mod["anti_caps"].keys():
                    i.auto_mod["anti_caps"][j] = []
        else:
            i.auto_mod["anti_caps"] = {
                "state": False,
                "percent": 40,
                "min_chars": 10,
                "target_roles": [],
                "target_channels": [],
                "ignore_roles": [],
                "ignore_channels": [],
            }

        if "anti_flud" in i.auto_mod.keys():
            for j in ("target_roles", "target_channels", "ignore_roles", "ignore_channels"):
                if j not in i.auto_mod["anti_flud"].keys():
                    i.auto_mod["anti_flud"][j] = []
        else:
            i.auto_mod["anti_flud"] = {
                "state": False,
                "target_roles": [],
                "target_channels": [],
                "ignore_roles": [],
                "ignore_channels": [],
            }

        if "anti_invite" in i.auto_mod.keys():
            for j in ("target_roles", "target_channels", "ignore_roles", "ignore_channels"):
                if j not in i.auto_mod["anti_invite"].keys():
                    i.auto_mod["anti_invite"][j] = []
        else:
            i.auto_mod["anti_invite"] = {
                "state": False,
                "target_roles": [],
                "target_channels": [],
                "ignore_roles": [],
                "ignore_channels": [],
            }

        ec = i.audit["economy"] if "economy" in i.audit.keys() else None
        mc = i.audit["moderate"] if "moderate" in i.audit.keys() else None
        cc = i.audit["clans"] if "clans" in i.audit.keys() else None
        ms = "moderate" in i.audit.keys()
        es = "economy" in i.audit.keys()
        cs = "clan" in i.audit.keys()
        me = 'message_edit'
        md = 'message_delete'
        i.audit = {
            'message_edit': {'state': me in i.audit.keys(), "channel_id": i.audit[me] if me in i.audit.keys() else None},
            'message_delete': {'state': md in i.audit.keys(), "channel_id": i.audit[md] if md in i.audit.keys() else None},
            'member_mute': {'state': ms, "channel_id": mc},
            'member_unmute': {'state': ms, "channel_id": mc},
            'member_vmute': {'state': ms, "channel_id": mc},
            'member_unvmute': {'state': ms, "channel_id": mc},
            'member_ban': {'state': ms, "channel_id": mc},
            'member_unban': {'state': ms, "channel_id": mc},
            'member_nick_update': {"state": False, "channel_id": None},
            'member_roles_update': {"state": False, "channel_id": None},
            'clan_delete': {'state': cs, "channel_id": cc},
            'clan_create': {'state': cs, "channel_id": cc},
            'money_remove': {'state': es, "channel_id": ec},
            'money_add': {'state': es, "channel_id": ec},
            'member_voice_move': {'state': False, "channel_id": None},
            'member_voice_connect': {'state': False, "channel_id": None},
            'member_voice_disconnect': {'state': False, "channel_id": None},
            'member_join': {'state': False, "channel_id": None},
            'member_leave': {'state': False, "channel_id": None},
            'bot_join': {'state': False, "channel_id": None},
            'bot_leave': {'state': False, "channel_id": None},
            'member_kick': {'state': ms, "channel_id": mc},
            'new_warn': {'state': ms, "channel_id": mc},
            'warns_reset': {'state': ms, "channel_id": mc}
        }
        i.rank_message.update(type="channel", channel_id=None, not_sending_channels=[])
        Guild.objects.filter(guild_id=i.guild_id).update(
            warns_settings=i.warns_settings,
            audit=i.audit,
            auto_mod=i.auto_mod,
            rank_message=i.rank_message,
            auto_reactions={}
        )
