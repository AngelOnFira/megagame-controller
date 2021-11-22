from asyncore import write


watch_the_stars_data = {
    "currencies": {
        "rare": [
            # Earth Item Cards
            ("Useful Human Technology", "💻"),
            ("Human Cultural Item", "🎭"),
            ("Rare Earth Metals", "🔧"),
            ("DNA Samples", "🔬"),
            ("Abducted Human", "👨‍💻"),
            # Technology Cards
            ("Dead Alien", "👽"),
            ("Saucer Wreck", "🚀"),
            ("Exotic Materials", "💠"),
            ("Unidentified Alien Items", "🔮"),
            ("Live Alien", "👽"),
            ("Alien Entertainment System", "🎬"),
            ("Alien Personal Weapons", "🔫"),
            ("Alien Power Generator", "💡"),
            ("Alien Energy Crystals", "🔮"),
            ("Alien Foods", "🍔"),
            ("Alien Communications System", "📡"),
            ("Alien Computer", "💻"),
        ],
        "common": [("Megabucks", "💵")],
        "admin": [
            ("Public Order", "📰"),
            ("Public Relations", "📈"),
            ("Income bonus", "💸"),
            # income currency, bonus income
        ],
        "logistics": [
            # Military cards
            ("Army", "👮‍♂️"),
            ("Navy", "🛳"),
            ("Interceptors", "🛩"),
            ("Special Agents", "🕵️‍♂️"),
            ("Nuclear Missile", "💣"),
        ],
    },
    "teams": {
        "United Kingdom": {
            "abreviation": "UK",
            "income_track": [-1, 2, 4, 6, 8, 10, 12, 14, 16],
            "flag": "🇬🇧",
            "initial_currencies": [
                ("Army", 1),
                ("Navy", 1),
                ("Nuclear Missile", 1),
                ("Interceptors", 3),
                ("Special Agents", 2),
                ("Public Relations", 5),
            ],
            "capitol": "London",
        },
        "United States": {
            "abreviation": "US",
            "income_track": [-1, 2, 4, 6, 8, 11, 14, 17, 20],
            "flag": "🇺🇸",
            "initial_currencies": [
                ("Army", 5),
                ("Navy", 5),
                ("Nuclear Missile", 5),
                ("Interceptors", 7),
                ("Special Agents", 4),
                ("Public Relations", 5),
            ],
            "capitol": "Washington",
        },
        "Brazil": {
            "abreviation": "BR",
            "income_track": [-1, 2, 3, 4, 6, 8, 10, 12, 14],
            "flag": "🇧🇷",
            "initial_currencies": [
                ("Army", 3),
                ("Navy", 1),
                ("Interceptors", 3),
                ("Special Agents", 2),
                ("Public Relations", 5),
            ],
            "capitol": "Brasilia",
        },
        "France": {
            "abreviation": "FR",
            "income_track": [-1, 2, 4, 6, 8, 10, 12, 14, 16],
            "flag": "🇫🇷",
            "initial_currencies": [
                ("Army", 1),
                ("Navy", 1),
                ("Nuclear Missile", 1),
                ("Interceptors", 3),
                ("Special Agents", 2),
                ("Public Relations", 5),
            ],
            "capitol": "Paris",
        },
        "India": {
            "abreviation": "IN",
            "income_track": [-1, 2, 3, 5, 7, 9, 11, 13, 15],
            "flag": "🇮🇳",
            "initial_currencies": [
                ("Army", 2),
                ("Navy", 1),
                ("Nuclear Missile", 1),
                ("Interceptors", 3),
                ("Special Agents", 2),
                ("Public Relations", 5),
            ],
            "capitol": "New Delhi",
        },
        "Russia": {
            "abreviation": "RU",
            "income_track": [-1, 2, 3, 4, 6, 8, 10, 12, 14],
            "flag": "🇷🇺",
            "initial_currencies": [
                ("Army", 4),
                ("Navy", 2),
                ("Nuclear Missile", 3),
                ("Interceptors", 5),
                ("Special Agents", 2),
                ("Public Relations", 5),
            ],
            "capitol": "Moscow",
        },
        "China": {
            "abreviation": "CN",
            "income_track": [-1, 2, 4, 6, 8, 10, 12, 15, 18],
            "flag": "🇨🇳",
            "initial_currencies": [
                ("Army", 4),
                ("Navy", 1),
                ("Nuclear Missile", 1),
                ("Interceptors", 4),
                ("Special Agents", 2),
                ("Public Relations", 5),
            ],
            "capitol": "Beijing",
        },
        "Japan": {
            "abreviation": "JP",
            "income_track": [-1, 2, 4, 6, 8, 10, 12, 14, 16],
            "flag": "🇯🇵",
            "initial_currencies": [
                ("Army", 2),
                ("Navy", 2),
                ("Interceptors", 4),
                ("Special Agents", 2),
                ("Public Relations", 5),
            ],
            "capitol": "Tokyo",
        },
    },
    "roles": {
        "Head of State",
        "Foreign Minister",
        "Chief of Defense",
        "Security Council",
    },
    "channels": {
        "world-news": {"description": "Announcements for world events"},
        "media-release": {
            "write": ["Head of State", "Foreign Minister"],
            "read": ["Chief of Defense"],
            "description": "News reports from Control and press releases from nations",
        },
        "world-summit": {
            "write": ["Head of State"],
            "description": "Meeting space for Heads of State, mainly for emergencies",
        },
        "united-nations": {
            "write": ["Foreign Minister"],
            "description": "UN council for Foreign Ministers",
        },
        "security-council": {
            "write": ["Security Council"],
            "description": "UN Security Council members",
        },
        "science-conference": {
            "write": ["Head of State"],
            "description": "Scientific developments",
        },
        "red-phone": {
            "countries": ["Russia", "United States"],
            # "write": ["Head of State", "Foreign Minister"],
        },
        "nato": {
            "countries": ["France", "United Kingdom", "United States"],
            # "write": ["Head of State", "Foreign Minister"],
        },
        "war-room": {
            "write": ["Chief of Defense"],
            "read": ["Head of State", "Foreign Minister"],
            "description": "War room for Chief of Defense to deploy interceptors and make military maneuvers",
        },
        "operations-room": {
            "write": ["Head of State"],
            "read": ["Chief of Defense", "Foreign Minister"],
            "description": "Operations room for Heads of State. Agent actions carried out here.",
        },
        "treaties": {
            "write": ["Head of State", "Foreign Minister"],
            "read": ["Chief of Defense"],
            "description": "Treaties posted here. Only Head of State can react (sign)",
        },
        "tech-support": {"description": "Technical related Q/A"},
        "wts-qa": {"description": "Rules related Q/A"},
    },
}


# watch_the_stars_data = {
#     "currencies": {
#         "rare": [
#             # Earth Item Cards
#             ("Pikachu", "🟡"),
#             ("Charmander", "🟠"),
#             ("Bulbasaur", "🟢"),
#             ("Squirtle", "🔵"),
#             ("Pidgey", "🔴"),
#             ("Eevee", "🔶"),
#             ("Jigglypuff", "🔷"),
#             ("Psyduck", "🔸"),
#             ("Mankey", "🔹"),
#             ("Growlithe", "🔺"),
#             ("Vulpix", "🔻"),
#             ("Rattata", "🔜"),
#             ("Meowth", "🔝"),
#             ("Koffing", "🔞"),
#             ("Gastly", "🔟"),
#             ("Gengar", "🔠"),
#             ("Cubone", "🔡"),
#         ],
#         "common": [("Megabucks", "💵")],
#         "admin": [
#             ("Public Order", "📰"),
#             ("Public Relations", "📈"),
#             ("Income bonus", "💸"),
#             # income currency, bonus income
#         ],
#         "logistics": [
#             ("Apple", "🍎"),
#             ("Banana", "🍌"),
#             ("Egg Nog", "🍩"),
#         ],
#     },
#     "teams": {
#         "United Kingdom": {
#             "abreviation": "UK",
#             "income_track": [-1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
#             "flag": "🇬🇧",
#             "initial_currencies": [
#                 ("Megabucks", 100),
#                 ("Public Relations", 5),
#             ],
#             "capitol": "London",
#         },
#         "United States": {
#             "abreviation": "US",
#             "income_track": [-1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
#             "flag": "🇺🇸",
#             "initial_currencies": [
#                 ("Megabucks", 100),
#                 ("Public Relations", 5),
#             ],
#             "capitol": "Washington",
#         },
#         "Brazil": {
#             "abreviation": "BR",
#             "income_track": [-1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
#             "flag": "🇧🇷",
#             "initial_currencies": [
#                 ("Megabucks", 100),
#                 ("Public Relations", 5),
#             ],
#             "capitol": "Brasilia",
#         },
#         "France": {
#             "abreviation": "FR",
#             "income_track": [-1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
#             "flag": "🇫🇷",
#             "initial_currencies": [
#                 ("Megabucks", 100),
#                 ("Public Relations", 5),
#             ],
#             "capitol": "Paris",
#         },
#         "India": {
#             "abreviation": "IN",
#             "income_track": [-1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
#             "flag": "🇮🇳",
#             "initial_currencies": [
#                 ("Megabucks", 100),
#                 ("Public Relations", 5),
#             ],
#             "capitol": "New Delhi",
#         },
#         "Russia": {
#             "abreviation": "RU",
#             "income_track": [-1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
#             "flag": "🇷🇺",
#             "initial_currencies": [
#                 ("Megabucks", 100),
#                 ("Public Relations", 5),
#             ],
#             "capitol": "Moscow",
#         },
#         "China": {
#             "abreviation": "CN",
#             "income_track": [-1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
#             "flag": "🇨🇳",
#             "initial_currencies": [
#                 ("Megabucks", 100),
#                 ("Public Relations", 5),
#             ],
#             "capitol": "Beijing",
#         },
#         "Japan": {
#             "abreviation": "JP",
#             "income_track": [-1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
#             "flag": "🇯🇵",
#             "initial_currencies": [
#                 ("Megabucks", 100),
#                 ("Public Relations", 5),
#             ],
#             "capitol": "Tokyo",
#         },
#     },
#     "roles": {
#         "Head of State",
#         "Foreign Minister",
#         "Chief of Defense",
#         "Security Council",
#     },
#     "channels": {
#         "world-news": {"description": "Announcements for world events"},
#         "media-release": {
#             "write": ["Head of State", "Foreign Minister"],
#             "read": ["Chief of Defense"],
#             "description": "News reports from Control and press releases from nations",
#         },
#         "world-summit": {
#             "write": ["Head of State"],
#             "description": "Meeting space for Heads of State, mainly for emergencies",
#         },
#         "united-nations": {
#             "write": ["Foreign Minister"],
#             "description": "UN council for Foreign Ministers",
#         },
#         "security-council": {
#             "write": ["Security Council"],
#             "description": "UN Security Council members",
#         },
#         "science-conference": {
#             "write": ["Head of State"],
#             "description": "Scientific developments",
#         },
#         "red-phone": {
#             "countries": ["Russia", "United States"],
#             # "write": ["Head of State", "Foreign Minister"],
#         },
#         "nato": {
#             "countries": ["France", "United Kingdom", "United States"],
#             # "write": ["Head of State", "Foreign Minister"],
#         },
#         "war-room": {
#             "write": ["Chief of Defense"],
#             "read": ["Head of State", "Foreign Minister"],
#             "description": "War room for Chief of Defense to deploy interceptors and make military maneuvers",
#         },
#         "operations-room": {
#             "write": ["Head of State"],
#             "read": ["Chief of Defense", "Foreign Minister"],
#             "description": "Operations room for Heads of State. Agent actions carried out here.",
#         },
#         "treaties": {
#             "write": ["Head of State", "Foreign Minister"],
#             "read": ["Chief of Defense"],
#             "description": "Treaties posted here. Only Head of State can react (sign)",
#         },
#         "tech-support": {"description": "Technical related Q/A"},
#         "wts-qa": {"description": "Rules related Q/A"},
#     },
# }
