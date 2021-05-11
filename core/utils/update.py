from core.services.database.models import Guild


def update():
    for i in Guild.objects.all():
        i.custom_commands = []
        i.auto_mod.update({
            "anti_mentions": {
                "state": False,
                "delete_message": False,
                "punishment": {
                    "state": False,
                    "type": "mute",
                    "time": None
                },
                "message": {
                    "state": False,
                    "type": "channel",
                    "content": {
                        "code": None,
                        "text": None
                    }
                },
                "max_mentions": 4,
                "target_roles": [],
                "target_channels": [],
                "ignore_roles": [],
                "ignore_channels": [],
            },
            "anti_link": {
                "state": False,
                "domains": [],
                "delete_message": False,
                "message": {
                    "state": False,
                    "type": "channel",
                    "content": {
                        "code": None,
                        "text": None
                    }
                },
                "punishment": {
                    "state": False,
                    "type": "mute",
                    "time": None
                },
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
            i.auto_mod["anti_caps"].update({
                "message": {
                    "state": False,
                    "type": "channel",
                    "content": {
                        "code": None,
                        "text": None
                    }
                }
            })
            for j in ("target_roles", "target_channels", "ignore_roles", "ignore_channels", "delete_message", "punishment"):
                if j not in i.auto_mod["anti_caps"].keys():
                    if j == "delete_message":
                        var = False
                    elif j == "punishment":
                        var = {
                            "state": False,
                            "type": "mute",
                            "time": None
                        }
                    else:
                        var = []

                    i.auto_mod["anti_caps"][j] = var
        else:
            i.auto_mod["anti_caps"] = {
                "state": False,
                "percent": 40,
                "min_chars": 10,
                "delete_message": False,
                "message": {
                    "state": False,
                    "type": "channel",
                    "content": {
                        "code": None,
                        "text": None
                    }
                },
                "punishment": {
                    "state": False,
                    "type": "mute",
                    "time": None
                },
                "target_roles": [],
                "target_channels": [],
                "ignore_roles": [],
                "ignore_channels": [],
            }

        if "anti_flud" in i.auto_mod.keys():
            i.auto_mod["anti_flud"].update({
                "message": {
                    "state": False,
                    "type": "channel",
                    "content": {
                        "code": None,
                        "text": None
                    }
                }
            })
            for j in ("target_roles", "target_channels", "ignore_roles", "ignore_channels", "delete_message", "punishment"):
                if j not in i.auto_mod["anti_flud"].keys():
                    if j == "delete_message":
                        var = False
                    elif j == "punishment":
                        var = {
                            "state": False,
                            "type": "mute",
                            "time": None
                        }
                    else:
                        var = []

                    i.auto_mod["anti_flud"][j] = var
        else:
            i.auto_mod["anti_flud"] = {
                "state": False,
                "delete_message": False,
                "message": {
                    "state": False,
                    "type": "channel",
                    "content": {
                        "code": None,
                        "text": None
                    }
                },
                "punishment": {
                    "state": False,
                    "type": "mute",
                    "time": None
                },
                "target_roles": [],
                "target_channels": [],
                "ignore_roles": [],
                "ignore_channels": [],
            }

        if "anti_invite" in i.auto_mod.keys():
            i.auto_mod["anti_invite"].update({
                "message": {
                    "state": False,
                    "type": "channel",
                    "content": {
                        "code": None,
                        "text": None
                    }
                }
            })
            for j in ("target_roles", "target_channels", "ignore_roles", "ignore_channels", "delete_message", "punishment"):
                if j not in i.auto_mod["anti_invite"].keys():
                    if j == "delete_message":
                        var = False
                    elif j == "punishment":
                        var = {
                            "state": False,
                            "type": "mute",
                            "time": None
                        }
                    else:
                        var = []
                    i.auto_mod["anti_invite"][j] = var
        else:
            i.auto_mod["anti_invite"] = {
                "state": False,
                "delete_message": False,
                "message": {
                    "state": False,
                    "type": "channel",
                    "content": {
                        "code": None,
                        "text": None
                    }
                },
                "punishment": {
                    "state": False,
                    "type": "mute",
                    "time": None
                },
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

        Guild.objects.filter(guild_id=i.guild_id).update(
            warns_settings={
                "max": 3,
                "punishment": {
                    "state": False,
                    "type": "mute",
                    "time": None
                },
                "role": {
                    "state": False,
                    "type": "add",
                    "role_id": None,
                    "time": None
                }
            },
            audit=i.audit,
            auto_mod=i.auto_mod,
            rank_message={
                "state": False,
                "type": "channel",
                "channel_id": None,
                "not_sending_channels": [],
                "message": {
                    "text": None,
                    "code": None
                }
            },
            auto_reactions={},
            shop_list=[],
            welcomer={
                "join": {
                    "state": False,
                    "type": "channel",
                    "channel_id": None,
                    "message": {
                        "text": None,
                        "code": None
                    }
                },
                "leave": {
                    "state": False,
                    "type": "channel",
                    "channel_id": None,
                    "message": {
                        "text": None,
                        "code": None
                    }
                }
            }
        )
