import discord
from discord.ext import commands
from discord.ui import View
import sqlite3
import random
import asyncio
import time
from getpass import getpass

# =========================================
# TOKEN
# =========================================
print("🔥 OW0 REAL PUBLIC BOT")

TOKEN = getpass("YOUR_BOT_TOKEN")

OWNER_ID = 1141054252433821876

# =========================================
# BOT
# =========================================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="p!",
    intents=intents,
    help_command=None
)

# =========================================
# DATABASE
# =========================================
conn = sqlite3.connect("owo_public.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    cash INTEGER,
    xp INTEGER,
    level INTEGER,
    pet TEXT,
    last_daily REAL,
    last_hunt REAL
)
""")

conn.commit()

# =========================================
# PETS
# =========================================
pets = {
    "none": 1,
    "fox": 1.2,
    "wolf": 1.5,
    "dragon": 2.5
}

# =========================================
# UTILS
# =========================================
def embed(title, desc, color=0x2f3136):
    return discord.Embed(
        title=title,
        description=desc,
        color=color
    )

def get_user(uid):

    c.execute(
        "SELECT * FROM users WHERE id=?",
        (str(uid),)
    )

    user = c.fetchone()

    if user is None:

        c.execute("""
        INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uid),
            1000,
            0,
            1,
            "none",
            0,
            0
        ))

        conn.commit()

        return get_user(uid)

    return user

def save(uid, cash, xp, level, pet, daily, hunt):

    c.execute("""
    UPDATE users
    SET cash=?,
        xp=?,
        level=?,
        pet=?,
        last_daily=?,
        last_hunt=?
    WHERE id=?
    """, (
        cash,
        xp,
        level,
        pet,
        daily,
        hunt,
        str(uid)
    ))

    conn.commit()

def cooldown(last, seconds):

    now = time.time()

    if now - last < seconds:
        return False, int(seconds - (now - last))

    return True, now

def add_xp(xp, level):

    xp += 10

    if xp >= level * 100:
        return 0, level + 1, True

    return xp, level, False

def draw():
    return random.randint(2, 11)

# =========================================
# READY
# =========================================
@bot.event
async def on_ready():

    print(f"✅ Logged in as {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"⚡ Synced {len(synced)} slash commands")

    except Exception as e:
        print(e)

# =========================================
# HELP
# =========================================
@bot.command()
async def help(ctx):

    em = discord.Embed(
        title="📖 P! HELP MENU",
        description="OW0 REAL PUBLIC BOT",
        color=0x00ffcc
    )

    em.add_field(
        name="💰 Economy",
        value="""
`p!daily`
`p!hunt`
`p!profile`
`p!leaderboard`
""",
        inline=False
    )

    em.add_field(
        name="🎮 Games",
        value="""
`p!coinflip <amount> <heads/tails>`
`p!spin <amount>`
`p!blackjack <amount>`
""",
        inline=False
    )

    em.add_field(
        name="👑 Owner",
        value="""
`p!addcash`
""",
        inline=False
    )

    await ctx.send(embed=em)

# =========================================
# PROFILE
# =========================================
@bot.command()
async def profile(ctx):

    u = get_user(ctx.author.id)

    em = discord.Embed(
        title=f"👤 {ctx.author.name}",
        color=0x00ffcc
    )

    em.add_field(name="💰 Cash", value=f"{u[1]}")
    em.add_field(name="⭐ XP", value=f"{u[2]}")
    em.add_field(name="🏆 Level", value=f"{u[3]}")
    em.add_field(name="🐾 Pet", value=f"{u[4]}")

    await ctx.send(embed=em)

# =========================================
# DAILY
# =========================================
@bot.command()
async def daily(ctx):

    u = get_user(ctx.author.id)

    ok, value = cooldown(u[5], 86400)

    if not ok:
        return await ctx.send(
            embed=embed(
                "⏳ Cooldown",
                f"Wait `{value}` seconds"
            )
        )

    reward = random.randint(1500, 4000)

    xp, lvl, up = add_xp(u[2], u[3])

    save(
        ctx.author.id,
        u[1] + reward,
        xp,
        lvl,
        u[4],
        value,
        u[6]
    )

    text = f"🎁 You received `{reward}` coins"

    if up:
        text += "\n⬆️ LEVEL UP"

    await ctx.send(
        embed=embed(
            "💰 Daily Reward",
            text,
            0x00ff99
        )
    )

# =========================================
# HUNT
# =========================================
@bot.command()
async def hunt(ctx):

    u = get_user(ctx.author.id)

    ok, value = cooldown(u[6], 10)

    if not ok:
        return await ctx.send(
            embed=embed(
                "⏳ Cooldown",
                f"Wait `{value}` seconds"
            )
        )

    animals = [
        "🐶 dog",
        "🐱 cat",
        "🦊 fox",
        "🐻 bear",
        "🐼 panda"
    ]

    animal = random.choice(animals)

    base = random.randint(100, 500)

    multiplier = pets.get(u[4], 1)

    reward = int(base * multiplier)

    xp, lvl, up = add_xp(u[2], u[3])

    save(
        ctx.author.id,
        u[1] + reward,
        xp,
        lvl,
        u[4],
        u[5],
        value
    )

    text = f"""
🏹 Hunted {animal}

💰 +{reward} coins
"""

    if up:
        text += "\n⬆️ LEVEL UP"

    await ctx.send(
        embed=embed(
            "🎯 Hunt",
            text,
            0xff9900
        )
    )

# =========================================
# COINFLIP
# =========================================
@bot.command()
async def coinflip(ctx, amount: int, side: str):

    u = get_user(ctx.author.id)

    if amount <= 0:
        return await ctx.send("❌ invalid amount")

    if amount > u[1]:
        return await ctx.send("❌ not enough money")

    if side.lower() not in ["heads", "tails"]:
        return await ctx.send("❌ choose heads/tails")

    msg = await ctx.send("🪙 Flipping coin...")

    animations = [
        "🪙 heads...",
        "🪙 tails...",
        "🪙 spinning..."
    ]

    for i in animations:
        await asyncio.sleep(0.7)
        await msg.edit(content=i)

    result = random.choice([
        "heads",
        "tails"
    ])

    cash = u[1]

    if result == side.lower():
        cash += amount
        text = f"✅ WON +{amount}"
    else:
        cash -= amount
        text = f"❌ LOST -{amount}"

    save(
        ctx.author.id,
        cash,
        u[2],
        u[3],
        u[4],
        u[5],
        u[6]
    )

    em = embed(
        "🪙 Coinflip",
        f"""
Result: `{result.upper()}`

{text}
""",
        0x00ffcc
    )

    await msg.edit(
        content="",
        embed=em
    )

# =========================================
# SLOT
# =========================================
@bot.command()
async def spin(ctx, amount: int):

    u = get_user(ctx.author.id)

    if amount <= 0:
        return await ctx.send("❌ invalid amount")

    if amount > u[1]:
        return await ctx.send("❌ not enough money")

    slots = [
        "🍒",
        "🍋",
        "🍇",
        "💎",
        "7️⃣"
    ]

    msg = await ctx.send("🎰 Spinning...")

    for _ in range(4):

        spin_result = [
            random.choice(slots),
            random.choice(slots),
            random.choice(slots)
        ]

        await asyncio.sleep(0.5)

        await msg.edit(
            content=f"🎰 {' | '.join(spin_result)}"
        )

    final = [
        random.choice(slots),
        random.choice(slots),
        random.choice(slots)
    ]

    final_text = " | ".join(final)

    cash = u[1]

    if len(set(final)) == 1:

        reward = amount * 3

        cash += reward

        result = f"🔥 JACKPOT +{reward}"

    else:

        cash -= amount

        result = f"❌ LOST -{amount}"

    save(
        ctx.author.id,
        cash,
        u[2],
        u[3],
        u[4],
        u[5],
        u[6]
    )

    em = embed(
        "🎰 Slot Machine",
        f"""
{final_text}

{result}
""",
        0xff00cc
    )

    await msg.edit(
        content="",
        embed=em
    )

# =========================================
# BLACKJACK
# =========================================
class Blackjack(View):

    def __init__(self, uid, amount):

        super().__init__(timeout=30)

        self.uid = uid
        self.amount = amount

        self.player = [draw(), draw()]
        self.dealer = [draw(), draw()]

    def total(self, cards):
        return sum(cards)

    async def finish(self, interaction, result):

        u = get_user(self.uid)

        cash = u[1]

        if result == "win":
            cash += self.amount

        elif result == "lose":
            cash -= self.amount

        save(
            self.uid,
            cash,
            u[2],
            u[3],
            u[4],
            u[5],
            u[6]
        )

        em = embed(
            "🃏 Blackjack Result",
            f"""
Your Total: `{self.total(self.player)}`
Dealer Total: `{self.total(self.dealer)}`

Result: **{result.upper()}**
""",
            0x00ffcc
        )

        await interaction.response.edit_message(
            embed=em,
            view=None
        )

    @discord.ui.button(
        label="HIT",
        style=discord.ButtonStyle.green
    )
    async def hit(self, interaction, button):

        if interaction.user.id != self.uid:
            return await interaction.response.send_message(
                "❌ not your game",
                ephemeral=True
            )

        self.player.append(draw())

        if self.total(self.player) > 21:
            return await self.finish(interaction, "lose")

        em = embed(
            "🃏 Blackjack",
            f"""
Your Total: `{self.total(self.player)}`
Dealer: `{self.dealer[0]} + ?`
"""
        )

        await interaction.response.edit_message(
            embed=em,
            view=self
        )

    @discord.ui.button(
        label="STAND",
        style=discord.ButtonStyle.red
    )
    async def stand(self, interaction, button):

        while self.total(self.dealer) < 17:
            self.dealer.append(draw())

        p = self.total(self.player)
        d = self.total(self.dealer)

        if p > d or d > 21:
            result = "win"

        elif p < d:
            result = "lose"

        else:
            result = "draw"

        await self.finish(interaction, result)

@bot.command()
async def blackjack(ctx, amount: int):

    u = get_user(ctx.author.id)

    if amount <= 0:
        return await ctx.send("❌ invalid amount")

    if amount > u[1]:
        return await ctx.send("❌ not enough money")

    em = embed(
        "🃏 Blackjack",
        """
🟩 HIT
🟥 STAND
""",
        0x00ffcc
    )

    await ctx.send(
        embed=em,
        view=Blackjack(
            ctx.author.id,
            amount
        )
    )

# =========================================
# SHOP
# =========================================
@bot.command()
async def shop(ctx):

    em = embed(
        "🛒 SHOP",
        """
🦊 fox — 1000
🐺 wolf — 3000
🐉 dragon — 10000
""",
        0xffcc00
    )

    await ctx.send(embed=em)

# =========================================
# LEADERBOARD
# =========================================
@bot.command()
async def leaderboard(ctx):

    c.execute("""
    SELECT id, cash
    FROM users
    ORDER BY cash DESC
    LIMIT 10
    """)

    rows = c.fetchall()

    text = ""

    for i, row in enumerate(rows):
        text += f"**{i+1}.** {row[0]} — `{row[1]}`💰\n"

    await ctx.send(
        embed=embed(
            "🏆 Leaderboard",
            text,
            0xffd700
        )
    )

# =========================================
# ADD CASH
# =========================================
@bot.command()
async def addcash(
    ctx,
    member: discord.Member,
    amount: int
):

    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ owner only")

    if amount <= 0:
        return await ctx.send("❌ invalid amount")

    u = get_user(member.id)

    new_cash = u[1] + amount

    save(
        member.id,
        new_cash,
        u[2],
        u[3],
        u[4],
        u[5],
        u[6]
    )

    await ctx.send(
        embed=embed(
            "💸 ADD CASH",
            f"""
✅ Added `{amount}` coins

👤 User: {member.mention}
💰 New Balance: `{new_cash}`
""",
            0x00ff99
        )
    )

# =========================================
# RUN
# =========================================
print("🔥 BOT STARTING...")

bot.run(TOKEN)
