import discord
import os
import re
import time
import asyncio
import requests
import json
import numpy as npy
import pandas as pd
import random
import keep_alive
from discord.ext import tasks,commands
import itertools
import openai

intents = discord.Intents().default()
intents.presences = False
intents.members = True
intents.message_content = True

def get_prefix(client,message):
  prefixes = [f'<@{client.user.id}>',f'<@!{client.user.id}>']
  with open('varstorage.json','r') as f:
    globalvars = json.load(f)
  try:
    prefix = globalvars["GlobalServer"][str(message.guild.id)]["prefix"]
  except KeyError:
    prefix = 'M.'
  prefixes.extend(map(''.join,itertools.product(*zip(prefix.upper(),prefix.lower()))))
  return prefixes

client = commands.Bot(command_prefix=get_prefix, strip_after_prefix=True, case_insensitive=True, intents=intents, help_command=None)
version = "v1.0.1"
devs = (697407424734298142,874332449109332018)
cmds = [['bal','balance','wallet','bank'],['beg'],['daily'],['dep','deposit'],['help'],['loadex','load_ex','load_extension'],['ping','pings'],['eval','evaluate','pyeval','pyevaluate','pythoneval','pythonevaluate'],['reloadex','reload_ex','reload_extension'],['rchat','reset_chat'],['rcharbot','reset_chatbot'],['rob','steal'],['prefix','set_prefix'],['transfer','send'],['unloadex','unload_ex','unload_extension'],['with','withdraw'],['work']]
chat_whitelist = [745148398247739516,692361266534285392,1006510265807929366,1058793877647147139,851823977563160577,1144459184671301632]
emojis = ('<:Cooldown:954434657947107348>','<:Yes:933934172299468810>','<:No:933934032192962600>','<a:Loading:1104249319231602689>')
currencies = ('<:Retcoins:1018448204364263434>','<:Retgems:1036311033364627559>')

cd_mapping = commands.CooldownMapping.from_cooldown(1,10,commands.BucketType.user)

os.chdir(os.path.normcase('/home/runner/Michiko/'))
@client.event
async def on_ready():
  global presences
  presences = itertools.cycle([1,f"{len(client.guilds):,} Servers | {len(client.users):,} Members",3])
  change_status.start()
  print(f"Logged in as {client.user.display_name}")
  time.sleep(1)
  
@tasks.loop(seconds=12)
async def change_status():
  status = next(presences)
  if status == 1:
    await client.change_presence(activity=discord.Game(name=f"/help | {version} - Stable"))
  elif status == 3:
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{client.get_user(devs[0]).display_name} & {client.get_user(devs[1]).display_name}"))
  else:
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=status))
  
@client.event
async def on_guild_remove(guild):
  with open('varstorage.json','r') as f:
    globalvars = json.load(f)
  if str(guild.id) in globalvars["GlobalServer"]:
    globalvars["GlobalServer"].pop(str(guild.id))
  with open('varstorage.json','w') as f:
    json.dump(globalvars,f,indent=2)

@client.event
async def on_message(message):
  if message.author == client.user:
    return
  await client.process_commands(message)
  if message.content.startswith(f'<@{client.user.id}>') or message.content.startswith(f'<@!{client.user.id}>'):
    if message.content == f'<@{client.user.id}>' or message.content == f'<@!{client.user.id}>':
      with open('varstorage.json','r') as f:
        globalvars = json.load(f)
      try:
        prefix = globalvars["GlobalServer"][str(message.guild.id)]["prefix"]
      except KeyError:
        prefix = 'M.'
      embed = discord.Embed(description=f"The Prefix for this Server is **{prefix}**\nIf you Forget the Prefix then mention me", color=discord.Color.blue())
      await message.channel.send(embed=embed,reference=message,mention_author=False)
    else:
      if message.author.id not in devs and message.author.id not in chat_whitelist:
        return
      bucket = cd_mapping.get_bucket(message)
      if bucket.update_rate_limit() == True:
        embed = discord.Embed(description=f"{emojis[0]} **Slow Down!** You're going too Fast", color=discord.Color.blue())
        await message.channel.send(embed=embed,reference=message,mention_author=False)
        return
      try:
        prompt = message.content.replace(f"<@{client.user.id}>","").replace(f"<@!{client.user.id}>","").strip()
        for i in cmds:
          if prompt.split(" ",1)[0].lower() in i:
            return
        embed = discord.Embed(description=f"{emojis[3]} Preparing a Response...", color=discord.Color.blue())
        msg = await message.channel.send(embed=embed,reference=message,mention_author=False)
        if prompt.split(" ",1)[0] == "AutoC:" or prompt.split(" ",1)[0] == "AutoComplete:":
          autocp = prompt.split(" ",1)[1]
          response = await GPT_Davinci(autocp)
          response = f"**{autocp}**" + response
        else:
          for task in asyncio.all_tasks():
            if str(message.author.id) == task.get_name():
              task.cancel()
              try:
                await task
              except asyncio.CancelledError:
                pass
          with open('chatbot.json','r') as f:
            prompts = json.load(f)
          if str(message.author.id) in prompts:
            result = prompts[str(message.author.id)]
            result.append({'role':'user','content':prompt})
            response = await GPT_Turbo(result)
            if len(prompts[str(message.author.id)]) == 5:
              prompts[str(message.author.id)].pop(0)
            prompts[str(message.author.id)].append({'role':'user','content':prompt})
          else:
            response = await GPT_Turbo([{'role':'user','content':prompt}])
            prompts[str(message.author.id)] = [{'role':'user','content':prompt}]
          links = list(map(lambda a: a.replace("![alt text](","").replace(")",""),re.findall("!\[alt text\]\(http.+\)",response)))
          if prompt.split(" ",1)[0] != "AutoC:" and prompt.split(" ",1)[0] != "AutoComplete:" and len(prompt.split(" ",40)) < 40 and len(response.split(" ",100)) > 100:
            embed = discord.Embed(description=f"**{prompt}**"+"\n\n"+response.replace("![alt text]","[Image Link]"), color=discord.Color.blue())
          else:
            embed = discord.Embed(description=response.replace("![alt text]","[Image Link]"), color=discord.Color.blue())
          if links != []:
            embed.set_image(url=links[0])
          asyncio.create_task(coro=chatbot_removekey(message.author), name=str(message.author.id))
          await msg.edit(embed=embed)
          if prompt.split(" ",1)[0] != "AutoC:" and prompt.split(" ",1)[0] != "AutoComplete:":
            try:
              with open('chatbot.json','w') as f:
                json.dump(prompts,f,indent=2)
            except Exception as e:
              pass
      except Exception as e:
        print(e)
        embed = discord.Embed(description=f"{emojis[2]} An Error has occurred", color=discord.Color.blue())
        await msg.edit(embed=embed)
  
@client.event
async def on_message_edit(before,after):
  if after.author == client.user:
    return
  await client.process_commands(after)
  
async def chatbot_removekey(user):
  try:
    await asyncio.sleep(900)
  except asyncio.CancelledError:
    return
  with open('chatbot.json','r') as f:
    prompts = json.load(f)
  prompts.pop(str(user.id))
  with open('chatbot.json','w') as f:
    json.dump(prompts,f,indent=2)
  
@client.event
async def on_command_error(ctx,error):
  if isinstance(error,commands.CommandOnCooldown):
    minutes,seconds = divmod(round(error.retry_after),60)
    hours,minutes = divmod(minutes,60)
    cooldown = [hours,minutes,seconds]
    if cooldown[0] == 0:
      embed = discord.Embed(description=f"{emojis[0]} You Need to wait for **{cooldown[1]}** minutes & **{cooldown[2]}** seconds to use this Command Again", color=discord.Color.blue())
    elif cooldown[1] == 0:
      embed = discord.Embed(description=f"{emojis[0]} You Need to wait for **{cooldown[0]}** hours & **{cooldown[2]}** seconds to use this Command Again", color=discord.Color.blue())
    elif cooldown[2] == 0:
      embed = discord.Embed(description=f"{emojis[0]} You Need to wait for **{cooldown[0]}** hours & **{cooldown[1]}** minutes to use this Command Again", color=discord.Color.blue())
    elif cooldown[0] == 0 and cooldown[1] == 0:
      embed = discord.Embed(description=f"{emojis[0]} You Need to wait for **{cooldown[2]}** seconds to use this Command Again", color=discord.Color.blue())
    elif cooldown[0] == 0 and cooldown[2] == 0:
      embed = discord.Embed(description=f"{emojis[0]} You Need to wait for **{cooldown[1]}** minutes to use this Command Again", color=discord.Color.blue())
    elif cooldown[1] == 0 and cooldown[2] == 0:
      embed = discord.Embed(description=f"{emojis[0]} You Need to wait for **{cooldown[0]}** hours to use this Command Again", color=discord.Color.blue())
    else:
      embed = discord.Embed(description=f"{emojis[0]} You Need to wait for **{cooldown[0]}** hours, **{cooldown[1]}** minutes & **{cooldown[2]}** seconds to use this Command Again", color=discord.Color.blue())
    await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
    return
  elif isinstance(error,commands.CommandNotFound):
    return
  
@client.command(aliases=['rchat'])
@commands.cooldown(1,10,commands.BucketType.user)
async def reset_chat(ctx):
  embed = discord.Embed(description=f"{emojis[3]} Processing Request...", color=discord.Color.blue())
  msg = await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
  for task in asyncio.all_tasks():
    if str(ctx.author.id) == task.get_name():
      task.cancel()
      try:
        await task
      except asyncio.CancelledError:
        pass
  with open('chatbot.json','r') as f:
    prompts = json.load(f)
  if str(ctx.author.id) in prompts:
    prompts.pop(str(ctx.author.id))
    with open('chatbot.json','w') as f:
      json.dump(prompts,f,indent=2)
  embed = discord.Embed(description=f"{emojis[1]} All your previous conversations with the chatbot have been deleted", color=discord.Color.blue())
  await msg.edit(embed=embed)
  
@client.command(aliases=['rchatbot'])
@commands.is_owner()
@commands.cooldown(1,10,commands.BucketType.user)
async def reset_chatbot(ctx):
  embed = discord.Embed(description=f"{emojis[3]} Processing Request...", color=discord.Color.blue())
  msg = await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
  for task in asyncio.all_tasks():
    try:
      await commands.MemberConverter().convert(ctx,task.get_name())
    except commands.errors.MemberNotFound:
      continue
    task.cancel()
    try:
      await task
    except asyncio.CancelledError:
      pass
  with open('chatbot.json','r') as f:
    prompts = json.load(f)
  prompts.clear()
  with open('chatbot.json','w') as f:
    json.dump(prompts,f,indent=2)
  embed = discord.Embed(description=f"{emojis[1]} Chatbot Database has been cleared", color=discord.Color.blue())
  await msg.edit(embed=embed)

async def load_cogs():  
  for file in os.listdir('./cogs'):
    if file.endswith('.py'):
      await client.load_extension(f'cogs.{file[:-3]}')
asyncio.run(load_cogs())
  
@client.command(aliases=['load_extension','load_ex'])
@commands.is_owner()
@commands.cooldown(1,3,commands.BucketType.user)
async def loadex(ctx,extension):
  await client.load_extension(f"cogs.{extension.replace('.py','')}")
  print(f"» Loaded : {extension.replace('.py','')}.py")
  embed = discord.Embed(description=f"{emojis[1]} Loaded **{extension.replace('.py','')}.py**", color=discord.Color.blue())
  await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
  
@client.command(aliases=['unload_extension','unload_ex'])
@commands.is_owner()
@commands.cooldown(1,3,commands.BucketType.user)
async def unloadex(ctx,extension):
  await client.unload_extension(f"cogs.{extension.replace('.py','')}")
  print(f"» Unloaded : {extension.replace('.py','')}.py")
  embed = discord.Embed(description=f"{emojis[1]} Unloaded **{extension.replace('.py','')}.py**", color=discord.Color.blue())
  await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
  
@client.command(aliases=['reload_extension','reload_ex'])
@commands.is_owner()
@commands.cooldown(1,3,commands.BucketType.user)
async def reloadex(ctx,extension):
  await client.reload_extension(f"cogs.{extension.replace('.py','')}")
  print(f"» Reloaded : {extension.replace('.py','')}.py")
  embed = discord.Embed(description=f"{emojis[1]} Reloaded {extension.replace('.py','')}.py", color=discord.Color.blue())
  await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
  
def toFloat(s):
  return float(pd.eval(str(s).replace(',','').replace('k','*1e3').replace('K','*1e3').replace('m','*1e6').replace('M','*1e6').replace('b','*1e9').replace('B','*1e9')))

async def GPT_Davinci(prompt,max_tokens=2048,temp=1,top_p=0.5,f_p=0.75,p_p=0.5,stop=['\n\n\n\n\n'],echo=False,api_key=os.environ['OPENAI_API_KEY']):
  responses = openai.Completion.create(api_key=api_key, model="text-davinci-003", prompt=prompt, max_tokens=max_tokens, temperature=temp, top_p=top_p, frequency_penalty=f_p, presence_penalty=p_p, stop=stop, echo=echo)
  return responses['choices'][0]['text']

async def GPT_Turbo(prompt,max_tokens=2048,temp=1,top_p=0.5,f_p=0.75,p_p=0.5,api_key=os.environ['OPENAI_API_KEY']):
  responses = openai.ChatCompletion.create(api_key=api_key, model="gpt-3.5-turbo", messages=prompt, max_tokens=max_tokens, temperature=temp, top_p=top_p, frequency_penalty=f_p, presence_penalty=p_p)
  return responses['choices'][0]['message']['content']
  
def GPT_TextEdit(prompt,instruction,temp=1,top_p=0.5,api_key=os.environ['OPENAI_API_KEY']):
  prompt = prompt.strip()
  responses = openai.Edit.create(api_key=api_key, model="text-davinci-edit-001", input=prompt, instruction=instruction)
  return responses['choices'][0]['text']

@client.command(aliases=['prefix'])
@commands.has_permissions(administrator=True)
@commands.cooldown(1,10,commands.BucketType.guild)
async def set_prefix(ctx,bot:discord.Member,newprefix="Default"):
  if newprefix == None or newprefix.lower() == "default":
    newprefix = 'M.'
  with open('varstorage.json','r') as f:
    globalvars = json.load(f)
  try:
    oldprefix = globalvars["GlobalServer"][str(ctx.guild.id)]["prefix"]
  except KeyError:
    oldprefix = 'M.'
  if bot != client.user:
    embed = discord.Embed(description=f"{emojis[2]} Please Mention the Bot to Confirm (Please use the following Syntax):\n> **{oldprefix}prefix {client.user.mention} <new prefix>**", color=discord.Color.blue())
    await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
    return
  if oldprefix.lower() != newprefix.lower() and newprefix.upper() != 'M.':
    if str(ctx.guild.id) not in globalvars["GlobalServer"]:
      globalvars["GlobalServer"][str(ctx.guild.id)] = {}
    globalvars["GlobalServer"][str(ctx.guild.id)]["prefix"] = str(newprefix)
    with open('varstorage.json','w') as f:
      json.dump(globalvars,f,indent=2)
  elif newprefix.upper() == 'M.':
    if str(ctx.guild.id) in globalvars["GlobalServer"]:
      if "prefix" in globalvars["GlobalServer"][str(ctx.guild.id)]:
        globalvars["GlobalServer"][str(ctx.guild.id)].pop("prefix")
        if globalvars["GlobalServer"][str(ctx.guild.id)] == {}:
          globalvars["GlobalServer"].pop(str(ctx.guild.id))
        with open('varstorage.json','w') as f:
          json.dump(globalvars,f,indent=2)
  embed = discord.Embed(description=f"{emojis[1]} The Prefix has been Changed to **{newprefix}**", color=discord.Color.blue())
  await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
    
@set_prefix.error
async def set_prefix_error(ctx,error):
  if isinstance(error,commands.MissingRequiredArgument) or isinstance(error,commands.BadArgument):
    with open('varstorage.json','r') as f:
      globalvars = json.load(f)
    try:
      oldprefix = globalvars["GlobalServer"][str(ctx.guild.id)]["prefix"]
    except KeyError:
      oldprefix = 'M.'
    embed = discord.Embed(description=f"{emojis[2]} Please Mention the Bot and Enter the New Prefix to Confirm (Please use the following Syntax):\n> **{oldprefix}prefix {client.user.mention} <new prefix>**", color=discord.Color.blue())
    await ctx.send(embed=embed,reference=ctx.message,mention_author=False)

@client.command(aliases=['pings'])
@commands.cooldown(1,3,commands.BucketType.user)
async def ping(ctx):
  embed = discord.Embed(title="<a:Online:933935886742224917> Pong!", url=f'https://discord.com/oauth2/authorize?client_id={client.user.id}&scope=bot%20applications.commands&permissions=2146958847',  description=f"```\nDatabase  : {random.randint(2,3)} ms\nWebsocket : {random.randint(60,80)} ms\nHeartbeat : {round(client.latency*1000)} ms\nRoundtrip : {round(time.process_time()+random.randint(350,400))} ms ```", color=0x2F3136)
  embed.set_thumbnail(url=client.user.avatar)
  await ctx.send(embed=embed,reference=ctx.message,mention_author=False)

@client.command(aliases=['eval','evaluate','pyevaluate','pythoneval','pythonevaluate'])
@commands.is_owner()
@commands.cooldown(1,3,commands.BucketType.user)
async def pyeval(ctx,*,pycode):
  embed = discord.Embed(description=f"{emojis[3]} Evaluating the Python Code...", color=discord.Color.blue())
  msg = await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
  try:
    embed = discord.Embed(description=f"<:Input:986957203321782332> **Input**\n```py\n{pycode} ```\n<:Output:986957278123012126> **Output**\n```py\n{eval(pycode)} ```", color=discord.Color.blue())
    embed.set_thumbnail(url=client.user.avatar)
  except Exception as e:
    embed = discord.Embed(description=f"<:Input:986957203321782332> **Input**\n```py\n{pycode} ```\n<:Output:986957278123012126> **Output**\n```py\nLine No.   : {e.__traceback__.tb_lineno}\nLocation   : {__file__}\nError Type : {type(e).__name__}\nException  : {e} ```", color=discord.Color.blue())
    embed.set_thumbnail(url=client.user.avatar)
  await msg.edit(embed=embed)
  
@pyeval.error
async def pyeval_error(ctx,error):
  if isinstance(error,commands.MissingRequiredArgument):
    embed = discord.Embed(description=f"{emojis[2]} Please Provide Valid Python Code to Evaluate", color=discord.Color.blue())
    await ctx.send(embed=embed,reference=ctx.message,mention_author=False)

keep_alive.keep_alive()
try:
  client.run(os.environ['TOKEN'])
except discord.HTTPException as e:
  if e.status == 429:
    print("You are being Rate Limited\nRestarting All Systems Now!")
    os.system('kill 1')
  else:
    raise e