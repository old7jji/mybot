import discord
from discord.ext import commands
import datetime
import re
import os
# تحديد الصلاحيات (Intents)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# البريفكس المفضل (-)
bot = commands.Bot(command_prefix="-", intents=intents)

# قاموس لتخزين تحذيرات المستخدمين
user_warnings = {}

# -------------------------------------------------------------
# دالة مساعدة لإنشاء بطاقة Embed التوجيهية
# -------------------------------------------------------------
def create_help_embed(cmd_name, description, aliases, usage, examples):
    aliases_str = f"[{', '.join(aliases)}]" if aliases else "None"
    examples_text = "\n".join([f"-{ex}" for ex in examples])

    desc = (
        f"**Command: {cmd_name}**\n\n"
        f"{description}\n\n"
        f"**Aliases:**\n"
        f"{aliases_str}\n\n"
        f"**Usage:**\n"
        f"-{usage}\n\n"
        f"**Examples:**\n"
        f"{examples_text}"
    )
    return discord.Embed(description=desc, color=discord.Color.dark_gray())

# تحويل صيغ الوقت (1m, 1h, 1d, 1w, 1mo, 1y)
def parse_time(time_str: str):
    unit = time_str[-1].lower()
    if time_str.endswith("mo"):
        unit = "mo"
        num = int(time_str[:-2])
    else:
        num = int(time_str[:-1])

    if unit == "m":
        return datetime.timedelta(minutes=num)
    elif unit == "h":
        return datetime.timedelta(hours=num)
    elif unit == "d":
        return datetime.timedelta(days=num)
    elif unit == "w":
        return datetime.timedelta(weeks=num)
    elif unit == "mo":
        return datetime.timedelta(days=num * 30)
    elif unit == "y":
        return datetime.timedelta(days=num * 365)
    return None

# -------------------------------------------------------------
# الأحداث الرئيسية والردود التلقائية
# -------------------------------------------------------------
@bot.event
async def on_ready():
    print(f"تم تشغيل البوت بنجاح باسم: {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    msg = message.content.strip()

    # 1. رد السلام التلقائي
    if msg in ["السلام عليكم", "سلام عليكم", "السلام عليكم ورحمة الله", "سلام عليكم ورحمة الله وبركاته"]:
        await message.channel.send(f"# وعليكم السلام منور/ة <a:9544:1551310004726796389>")

    # 2. رد برب
    elif msg.lower() in ["برب", "brb"]:
        await message.channel.send(f"# تيت، لا تطول  <:906:1551308924786053171>")

    # 3. رد التقييط (نقطة)
    elif msg == ".":
        await message.channel.send(f"# أحلى من ينقط <:67:1551304126179319989>")

    # 4. أمر إخفاء وإظهار الروم بالرمز +
    elif msg == "+hide":
        if message.author.guild_permissions.manage_channels:
            await message.channel.set_permissions(message.guild.default_role, read_messages=False)
            await message.channel.send("**تم إخفاء القناة بنجاح.**")
        else:
            await message.channel.send("لا تملك صلاحية لإخفاء هذه القناة.")

    elif msg == "+show":
        if message.author.guild_permissions.manage_channels:
            await message.channel.set_permissions(message.guild.default_role, read_messages=True)
            await message.channel.send("**تم إظهار القناة بنجاح.**")
        else:
            await message.channel.send("لا تملك صلاحية لإظهار هذه القناة.")

    await bot.process_commands(message) 
    # -------------------------------------------------------------
# 1. أمر التايم / اسكات (Mute / Timeout)
# -------------------------------------------------------------
@bot.command(name="تايم", aliases=["مزعج", "اسكت", "نجب", "mute"])
@commands.has_permissions(moderate_members=True)
async def timeout_command(ctx, member: discord.Member = None, duration: str = None, *, reason: str = "لم يتم تحديد سبب"):
    if member is None or duration is None:
        embed = create_help_embed(
            cmd_name="mute",
            description="Mute a member from text/voice channels so they cannot type.",
            aliases=["تايم", "مزعج", "اسكت", "نجب"],
            usage="mute [user] [time] (reason)",
            examples=[
                f"mute {ctx.author.mention} 1m Spamming",
                f"mute {ctx.author.mention} 1h",
                f"mute {ctx.author.mention} 1d",
                f"mute {ctx.author.mention} 1w",
                f"mute {ctx.author.mention} 1mo",
                f"mute {ctx.author.mention} 1y"
            ]
        )
        await ctx.send(embed=embed)
        return

    try:
        delta = parse_time(duration)
        if delta:
            await member.timeout(delta, reason=reason)
            await ctx.send(f"**تم إعطاء تايم للعضو {member.mention} لمدة {duration}!**\nالسبب: {reason}")
        else:
            await ctx.send("الصيغة الزمنية غير صحيحة. استخدم: (1m, 1h, 1d, 1w, 1mo, 1y)")
    except Exception as e:
        await ctx.send(f"تعذر تطبيق التايم: {e}")

# -------------------------------------------------------------
# 2. أمر إزالة التايم (Untimeout)
# -------------------------------------------------------------
@bot.command(name="شيل", aliases=["انبح", "تكلم", "اهرج", "untimeout"])
@commands.has_permissions(moderate_members=True)
async def untimeout_command(ctx, member: discord.Member = None):
    if member is None:
        embed = create_help_embed(
            cmd_name="untimeout",
            description="Remove timeout from a user",
            aliases=["شيل", "انبح", "تكلم", "اهرج"],
            usage="untimeout [user]",
            examples=[
                f"untimeout {ctx.author.mention}",
                "untimeout 956374841206931476"
            ]
        )
        await ctx.send(embed=embed)
        return

    try:
        await member.timeout(None)
        await ctx.send(f"**تم فك التايم عن العضو {member.mention} بنجاح!**")
    except Exception as e:
        await ctx.send(f"حدث خطأ: {e}")

# -------------------------------------------------------------
# 3. أمر الباند (Ban)
# -------------------------------------------------------------
@bot.command(name="تف", aliases=["لف", "برا", "بانكاي", "بان", "ban"])
@commands.has_permissions(ban_members=True)
async def ban_command(ctx, member: discord.Member = None, *, reason: str = "لم يتم تحديد سبب"):
    if member is None:
        embed = create_help_embed(
            cmd_name="ban",
            description="Bans a member.",
            aliases=["تف", "لف", "برا", "بانكاي", "بان"],
            usage="ban [user] (reason)",
            examples=[
                f"ban {ctx.author.mention}",
                f"ban {ctx.author.mention} spamming",
                f"ban {ctx.author.mention} 1h spamming",
                f"ban {ctx.author.mention} 1d spamming",
                f"ban {ctx.author.mention} 1w"
            ]
        )
        await ctx.send(embed=embed)
        return

    try:
        await member.ban(reason=reason)
        await ctx.send(f"**تم حظر العضو {member.mention} بنجاح!**\nالسبب: {reason}")
    except Exception as e:
        await ctx.send(f"حدث خطأ أثناء التبنيد: {e}")
        # -------------------------------------------------------------
# 4. أمر إزالة الباند (Unban)
# -------------------------------------------------------------
@bot.command(name="فك", aliases=["رفع", "شيل_باند", "unban"])
@commands.has_permissions(ban_members=True)
async def unban_command(ctx, user_id: str = None):
    if user_id is None:
        embed = create_help_embed(
            cmd_name="unban",
            description="Unbans a member.",
            aliases=["فك", "رفع", "شيل_باند"],
            usage="unban [user_id / mention]",
            examples=[
                f"unban {ctx.author.id}",
                "unban 956374841206931476"
            ]
        )
        await ctx.send(embed=embed)
        return

    try:
        clean_id = int(re.sub(r"\D", "", user_id))
        user = await bot.fetch_user(clean_id)
        await ctx.guild.unban(user)
        await ctx.send(f"**تم فك الحظر عن العضو {user.mention} بنجاح!**")
    except Exception as e:
        await ctx.send(f"تعذر فك الحظر، تأكد من صحة الآيدي: {e}")

# -------------------------------------------------------------
# 5. أمر الطرد (Kick)
# -------------------------------------------------------------
@bot.command(name="طرد", aliases=["برا-الحجي", "kick"])
@commands.has_permissions(kick_members=True)
async def kick_command(ctx, member: discord.Member = None, *, reason: str = "لم يتم تحديد سبب"):
    if member is None:
        embed = create_help_embed(
            cmd_name="kick",
            description="Kicks a member.",
            aliases=["طرد", "برا-الحجي"],
            usage="kick [user] (reason)",
            examples=[
                f"kick {ctx.author.mention}",
                f"kick {ctx.author.mention} spam",
                "kick 956374841206931476"
            ]
        )
        await ctx.send(embed=embed)
        return

    try:
        await member.kick(reason=reason)
        await ctx.send(f"**تم طرد العضو {member.mention} بنجاح!**\nالسبب: {reason}")
    except Exception as e:
        await ctx.send(f"حدث خطأ أثناء الطرد: {e}")
        # -------------------------------------------------------------
# 6. نظام التحذيرات (Warn / مسامح)
# -------------------------------------------------------------
@bot.command(name="تحذير", aliases=["ت", "warn"])
@commands.has_permissions(manage_messages=True)
async def warn_command(ctx, member: discord.Member = None, *, reason: str = "لم يتم تحديد سبب"):
    if member is None:
        embed = create_help_embed(
            cmd_name="warn",
            description="Warn a member for rules violation.",
            aliases=["ت", "تحذير"],
            usage="warn [user] (reason)",
            examples=[
                f"warn {ctx.author.mention}",
                f"warn {ctx.author.mention} سب الشات"
            ]
        )
        await ctx.send(embed=embed)
        return

    guild_id = ctx.guild.id
    user_id = member.id

    if guild_id not in user_warnings:
        user_warnings[guild_id] = {}
    if user_id not in user_warnings[guild_id]:
        user_warnings[guild_id][user_id] = []

    user_warnings[guild_id][user_id].append(reason)
    count = len(user_warnings[guild_id][user_id])

    await ctx.send(f"**تم إعطاء تحذير للمستخدم {member.mention}!**\nعدد التحذيرات الحالية: **{count}**\nالسبب: {reason}")

@bot.command(name="مسامح", aliases=["unwarn"])
@commands.has_permissions(manage_messages=True)
async def unwarn_command(ctx, member: discord.Member = None):
    if member is None:
        embed = create_help_embed(
            cmd_name="unwarn",
            description="Remove warnings from a user.",
            aliases=["مسامح"],
            usage="مسامح [user]",
            examples=[
                f"مسامح {ctx.author.mention}"
            ]
        )
        await ctx.send(embed=embed)
        return

    guild_id = ctx.guild.id
    user_id = member.id

    if guild_id in user_warnings and user_id in user_warnings[guild_id] and len(user_warnings[guild_id][user_id]) > 0:
        user_warnings[guild_id][user_id].pop()
        count = len(user_warnings[guild_id][user_id])
        await ctx.send(f"**تم إزالة تحذير عن {member.mention}.** المتبقي لديه: **{count}** تحذيرات.")
    else:
        await ctx.send(f"المستخدم {member.mention} ليس لديه أي تحذيرات حالياً.")
        # -------------------------------------------------------------
# 7. نظام التكت الاحترافي - الأزرار والقوائم (Ticket System)
# -------------------------------------------------------------
class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="إغلاق التكت 🔒", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("سيتم إغلاق التكت خلال 5 ثوانٍ...", ephemeral=True)
        await discord.utils.sleep_until(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=5))
        await interaction.channel.delete()

class TicketSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="اختر قسم التكت المناسب...",
        custom_id="ticket_dropdown",
        options=[
            discord.SelectOption(label="الدعم الفني والخدمات", value="tech", description="فتح تكت للمساعدة الفنية والحلول", emoji="🛠️"),
            discord.SelectOption(label="شكاوى واقتراحات", value="complaint", description="رفع شكوى على عضو أو اقتراح جديد", emoji="📝"),
            discord.SelectOption(label="استفسار عام", value="general", description="أي سؤال أو استفسار يدور في بالك", emoji="❓"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        category_name = select.values[0]
        guild = interaction.guild
        author = interaction.user

        # إنشاء الكاتجوري إن لم يكن موجوداً
        category = discord.utils.get(guild.categories, name="Tickets")
        if not category:
            category = await guild.create_category("Tickets")

        # تعيين صلاحيات الروم
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        channel_name = f"ticket-{category_name}-{author.name}"
        ticket_channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)

        embed = discord.Embed(
            title=f"أهلاً بك في قسم {select.values[0].capitalize()}!",
            description=f"مرحباً {author.mention}، يرجى كتابة مشكلتك/تفاصيل طلبك هنا وستتم إجابتك من قبل إدارة السيرفر في أقرب وقت.",
            color=discord.Color.dark_red()
        )
        await ticket_channel.send(content=f"{author.mention}", embed=embed, view=TicketControlView())
        await interaction.response.send_message(f"تم فتح التكت بنجاح: {ticket_channel.mention}", ephemeral=True)
        # -------------------------------------------------------------
# أمر إرسال بانل التكت وتشغيل البوت
# -------------------------------------------------------------
@bot.command(name="setup_ticket")
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx, title: str = "لوحة الدعم الفني وتذاكر السيرفر"):
    embed = discord.Embed(
        title=title,
        description="يرجى اختيار القسم المناسب من القائمة السفلى لفتح تكت وتواصلك مع الدعم الفني مباشرة.",
        color=discord.Color.dark_gray()
    )
    await ctx.send(embed=embed, view=TicketSelectView())

# آيديات الرولات
PIC_ROLE_ID = 1548230198674198528   # رول -pic
NICK_ROLE_ID = 1548230199923974194  # رول -nick

@bot.event
async def on_message(message):
    # تجاهل الرسائل الصادرة من البوت نفسه أو من الخاص (DM)
    if message.author == bot.user or not message.guild:
        return

    msg = message.content.strip().lower()

    # 1. أمر رول الصور (-pic)
    if msg == "-pic":
        role = message.guild.get_role(PIC_ROLE_ID)
        if not role:
            await message.channel.send("❌ لم يتم العثور على الرول!")
        else:
            if role in message.author.roles:
                await message.author.remove_roles(role)
                await message.channel.send("تم إزالة الرول منك بنجاح!")
            else:
                await message.author.add_roles(role)
                await message.channel.send("# تم الحصول على الرول بنجاح!")

    # 2. أمر رول تغيير الاسم (-nick)
    elif msg == "-nick":
        role = message.guild.get_role(NICK_ROLE_ID)
        if not role:
            await message.channel.send("❌ لم يتم العثور على الرول!")
        else:
            if role in message.author.roles:
                await message.author.remove_roles(role)
                await message.channel.send("تم إزالة الرول منك بنجاح!")
            else:
                await message.author.add_roles(role)
                await message.channel.send("# تم الحصول على الرول بنجاح!")

    # معالجة بقية أوامر البوت إن وجدت
    await bot.process_commands(message)

# 3. أمر قفل القناة (ق / -قفل)
    if msg in ["ق", "-قفل"]:
        if not message.author.guild_permissions.manage_channels:
            await message.channel.send("# ليس لديك صلاحية لإغلاق القناة!")
        else:
            await message.channel.set_permissions(message.guild.default_role, send_messages=False)
            await message.channel.send("# تم قفل الروم")

    # 4. أمر فتح القناة (ف / -فتح)
    if msg in ["ف", "-فتح"]:
        if not message.author.guild_permissions.manage_channels:
            await message.channel.send("# ليس لديك صلاحية لفتح القناة!")
        else:
            await message.channel.set_permissions(message.guild.default_role, send_messages=True)
            await message.channel.send("# تم فتح الروم")

# 5. أمر مسح الشات (م / مسح)
    if msg == "م" or msg.startswith("م ") or msg == "مسح" or msg.startswith("مسح "):
        if not message.author.guild_permissions.manage_messages:
            await message.channel.send("# ليس لديك صلاحية لمسح الرسائل!")
        else:
            # استخراج العدد المحدد من الرسائل
            parts = message.content.split()
            amount = 100  # العدد الافتراضي إذا لم يحدد المستخدم عدداً
            if len(parts) > 1 and parts[1].isdigit():
                amount = int(parts[1])

            # عملية المسح (تضمين الرسالة الحالية ضمن العدد)
            deleted = await message.channel.purge(limit=amount + 1)
            
            # إرسال رسالة تأكيد وحذفها بعد 3 ثوانٍ
            confirm_msg = await message.channel.send(f"# تم مسح {len(deleted) - 1}  بنجاح <a:99:1551318187096932504>")
            await confirm_msg.delete(delay=3)

# أمر الرد على كلمة أحبك Sys مع المنشن
    if msg.lower() in ["احبك sys", "أحبك sys"]:
        await message.channel.send(f"# أنا أكثر يقلبي {message.author.mention} <a:9544:1551310004726796389>")

# أمر الرد على السلام مع المنشن والإيموجي
    if msg in ["السلام عليكم", "سلام عليكم", "السلام عليكم ورحمة الله"]:
        await message.channel.send(f"# وعليكم السلام ورحمة الله وبركاته {message.author.mention} <:45:1551323026719506534>")

# أمر الرد على كلمة برب
    if msg.lower() in ["برب", "brb"]:
        await message.channel.send(f"# تيت لا تطول الغيبه {message.author.mention} <:906:1551308924786053171>")

# ضع التوكين الخاص بك هنا
bot.run(os.environ.get("MTU1MTI2MTIxOTEzNzEzMDYxOA.GxsfOW.I4jwBrS9X9x3P7Q575zb54WMMgUFTrV8EbhEMU")
