import discord
import re
import time
import asyncio
import requests
import json
import numpy as npy
import pandas as pd
import random
from discord.ext import commands
import itertools

emojis = ('<:Cooldown:954434657947107348>','<:Yes:933934172299468810>','<:No:933934032192962600>','<a:Loading:1104249319231602689>')
currencies = ('<:Retcoins:1018448204364263434>','<:Retgems:1036311033364627559>')

async def get_bank_data():
  with open('mainbank.json','r') as f:
    users = json.load(f)
  return users
  
async def open_account(user):
  users = await get_bank_data()
  if str(user.id) in users:
    return False
  else:
    users[str(user.id)] = {}
    users[str(user.id)]["Retcoins"] = 0
    users[str(user.id)]["Retcoins_B"] = 0
    users[str(user.id)]["Retgems"] = 0
  with open('mainbank.json','w') as f:
    json.dump(users,f,indent=2)
  return True

async def update_bank(user,change=0,mode="Retcoins"):
  users = await get_bank_data()
  users[str(user.id)][mode] += change
  with open('mainbank.json','w') as f:
    json.dump(users,f,indent=2)
  balance = [users[str(user.id)]["Retcoins"], users[str(user.id)]["Retcoins_B"], users[str(user.id)]["Retgems"]]
  return balance
  
def toFloat(s):
  return float(pd.eval(str(s).replace(',','').replace('k','*1e3').replace('K','*1e3').replace('m','*1e6').replace('M','*1e6').replace('b','*1e9').replace('B','*1e9')))
  
shop = {
  "Alcohol" : [1000, "Desc"],
  "Padlock" : [10000, "Desc"],
  "Cell Phone" : [10000, "Desc"]
}

class Economy(commands.Cog):
  def __init__(self,client):
    self.client = client
    
  @commands.Cog.listener()
  async def on_ready(self):
    print("» Loaded : economy.py")
  
  @commands.command(aliases=['bal','wallet','bank'])
  @commands.cooldown(1,3,commands.BucketType.user)
  async def balance(self,ctx,*,user=None):
    if user == None:
      user = ctx.author
    else:
      user = await commands.MemberConverter().convert(ctx, user)
    if user.bot == True:
      bal = [0,0]
    else:
      await open_account(user)
      bal = await update_bank(user)
    embed = discord.Embed(title=f"{user.display_name}'s Balance", description=f">>> **Wallet**\n{currencies[0]}{bal[0]:,}\n\n**Bank**\n{currencies[0]}{bal[1]:,}\n\n**Gems**\n{currencies[1]}{bal[2]:,}\n\n**Net Worth**\n{currencies[0]}{(bal[0]+bal[1]):,} {currencies[1]}{bal[2]:,}", color=discord.Color.blue())
    embed.set_thumbnail(url=user.avatar)
    await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
  
  @balance.error
  async def balance_error(self,ctx,error):
    if isinstance(error,commands.BadArgument):
      embed = discord.Embed(description=f"{emojis[2]} Please Mention a Valid User", color=discord.Color.blue())
      await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
  
  @commands.command(aliases=['with'])
  @commands.cooldown(1,3,commands.BucketType.user)
  async def withdraw(self,ctx,amount):
    await open_account(ctx.author)
    bal = await update_bank(ctx.author)
    if amount.lower() == "all" or amount.lower() == "maximum" or amount.lower() == "max":
      amount = bal[1]
    amount = int(toFloat(amount))
    if amount > bal[1]:
      embed = discord.Embed(description=f"{emojis[2]} You don't have that much money in your Bank", color=discord.Color.blue())
      await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
      return
    if amount < 0:
      embed = discord.Embed(description=f"{emojis[2]} Amount must be Positive", color=discord.Color.blue())
      await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
      return
    await update_bank(ctx.author,amount)
    await update_bank(ctx.author,-1*amount,"Retcoins_B")
    bal = await update_bank(ctx.author)
    if bal[1] == 0:
      embed = discord.Embed(description=f"You withdrew{currencies[0]}**{amount:,}** from your Bank... Now, you have{currencies[0]}**{bal[0]:,}** in your Wallet", color=discord.Color.blue())
    else:
      embed = discord.Embed(description=f"You withdrew{currencies[0]}**{amount:,}** from your Bank... Now, you have{currencies[0]}**{bal[0]:,}** in your Wallet &{currencies[0]}**{bal[1]:,}** in your Bank", color=discord.Color.blue())
    await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
  
  @withdraw.error
  async def withdraw_error(self,ctx,error):
    if isinstance(error,commands.MissingRequiredArgument) or isinstance(error,commands.BadArgument):
      embed = discord.Embed(description=f"{emojis[2]} Please Provide a Valid Amount to Withdraw", color=discord.Color.blue())
      await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
  
  @commands.command(aliases=['dep'])
  @commands.cooldown(1,3,commands.BucketType.user)
  async def deposit(self,ctx,amount):
    await open_account(ctx.author)
    bal = await update_bank(ctx.author)
    if amount.lower() == "all" or amount.lower() == "maximum" or amount.lower() == "max":
      amount = bal[0]
    amount = int(toFloat(amount))
    if amount > bal[0]:
      embed = discord.Embed(description=f"{emojis[2]} You don't have that much money in your Wallet", color=discord.Color.blue())
      await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
      return
    if amount < 0:
      embed = discord.Embed(description=f"{emojis[2]} Amount must be Positive", color=discord.Color.blue())
      await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
      return
    await update_bank(ctx.author,-1*amount)
    await update_bank(ctx.author,amount,"Retcoins_B")
    bal = await update_bank(ctx.author)
    if bal[0] == 0:
      embed = discord.Embed(description=f"You deposited{currencies[0]}**{amount:,}** in your Bank... Now, you have{currencies[0]}**{bal[1]:,}** in your Bank", color=discord.Color.blue())
    else:
      embed = discord.Embed(description=f"You deposited{currencies[0]}**{amount:,}** in your Bank... Now, you have{currencies[0]}**{bal[0]:,}** in your Wallet &{currencies[0]}**{bal[1]:,}** in your Bank", color=discord.Color.blue())
    await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
  
  @deposit.error
  async def deposit_error(self,ctx,error):
    if isinstance(error,commands.MissingRequiredArgument) or isinstance(error,commands.BadArgument):
      embed = discord.Embed(description=f"{emojis[2]} Please Provide a Valid Amount to Deposit", color=discord.Color.blue())
      await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
    
  @commands.command()
  @commands.cooldown(1,86400,commands.BucketType.user)
  async def daily(self,ctx):
    await open_account(ctx.author)
    await update_bank(ctx.author,5000)
    bal = await update_bank(ctx.author)
    embed = discord.Embed(description=f"{ctx.author.display_name} claimed his daily & got{currencies[0]}**{5000:,}** ... Now, they have{currencies[0]}**{bal[0]:,}** in their Wallet", color=discord.Color.blue())
    await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
  
  @commands.command()
  @commands.cooldown(1,600,commands.BucketType.user)
  async def work(self,ctx):
    await open_account(ctx.author)
    earnings = random.randint(500,1000)
    await update_bank(ctx.author,earnings)
    bal = await update_bank(ctx.author)
    embed = discord.Embed(description=f"{ctx.author.display_name} worked for {random.randint(10,16)} hours and got{currencies[0]}**{earnings:,}** ... Now, they have{currencies[0]}**{bal[0]:,}** in their Wallet", color=discord.Color.blue())
    await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
  
  @commands.command()
  @commands.cooldown(1,300,commands.BucketType.user)
  async def beg(self,ctx):
    await open_account(ctx.author)
    success = random.choice(["True","False"])
    if success == "True":
      earnings = random.randint(100,500)
      await update_bank(ctx.author,earnings)
    else:
      earnings = 0
    person = random.choice(["Elon Musk","Barack Obama","Donald Trump","Jeff Bezos","Bill Gates","Dwayne Johnson","Will Smith","Cristiano Ronaldo","Lionel Messi","Emma Watson","J.K. Rowling","Justin Bieber","Alan Walker","Sia","J. Balvin","Shawn Mendes","Taylor Swift","Selena Gomez"])
    if earnings > 0:
      reply = random.choice([f"gave you{currencies[0]}**{earnings:,}**",f'said,"Oh Poor Thing!" and gave you{currencies[0]}**{earnings:,}**',f"felt pity on you and gave you{currencies[0]}**{earnings:,}**"])
    else:
      reply = random.choice(["gave you Nothing","ignored you... Get Rekt!",f"gave you{currencies[0]}**{random.randint(100,2000):,}** but took it back... Lol","got angry as you wasted their precious time... So, they gave you Nothing"])
    embed = discord.Embed(description=f"**{person}** {reply}", color=discord.Color.blue())
    await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
    
  @commands.command(aliases=['steal'])
  @commands.cooldown(1,1800,commands.BucketType.user)
  async def rob(self,ctx,member:discord.Member):
    if member.bot == True:
      embed = discord.Embed(description=f"{emojis[2]} Did you just try to Rob a Bot?!", color=discord.Color.blue())
      await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
      return
    if member == ctx.author:
      embed = discord.Embed(description=f"{emojis[2]} Did you just try to rob yourself?!", color=discord.Color.blue())
      await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
      return
    await open_account(ctx.author)
    await open_account(member)
    bal1 = await update_bank(ctx.author)
    bal2 = await update_bank(member)
    if bal1[0] <= 100:
      embed = discord.Embed(description=f"{emojis[2]} You must have at least{currencies[0]}100 to Rob somone", color=discord.Color.blue())
      await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
      return
    if bal2[0] == 0:
      embed = discord.Embed(description=f"{emojis[2]} {member.display_name} doesn't have any money in their Wallet", color=discord.Color.blue())
      await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
      return
    user = random.choice(["Author","Member"])
    if user == "Author":
      rob = random.randint(1,bal1[0])
      await update_bank(ctx.author,-1*rob)
      await update_bank(member,rob)
    else:
      rob = random.randint(1,bal2[0])
      await update_bank(ctx.author,rob)
      await update_bank(member,-1*rob)
    bal1 = await update_bank(ctx.author)
    bal2 = await update_bank(member)
    reply = random.choice(["you got Robbed in return. You lost","you were beaten up by them. You were fined","you were caught by the Police. You were fined"])
    if user == "Author":
      embed = discord.Embed(description=f"You tried to Rob {member.display_name} but {reply}{currencies[0]}**{rob:,}** ... Now, you have{currencies[0]}**{bal1[0]:,}** in your Wallet & they have{currencies[0]}**{bal2[0]:,}**", color=discord.Color.blue())
    else:
      embed = discord.Embed(description=f"You Robbed {member.display_name} and stole{currencies[0]}**{rob:,}** from them... Now, you have{currencies[0]}**{bal1[0]:,}** in your Wallet & they have{currencies[0]}**{bal2[0]:,}**", color=discord.Color.blue())
    await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
  
  @rob.error
  async def rob_error(self,ctx,error):
    if isinstance(error,commands.MissingRequiredArgument) or isinstance(error,commands.BadArgument):
      embed = discord.Embed(description=f"{emojis[2]} Please Mention a Valid User to Steal from", color=discord.Color.blue())
      await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
  
  @commands.command(aliases=['send'])
  @commands.cooldown(1,5,commands.BucketType.user)
  async def transfer(self,ctx,member:discord.Member,amount=None):
    if member.bot == True:
      embed = discord.Embed(description=f"{emojis[2]} Did you just try to send money to a Bot?!", color=discord.Color.blue())
      await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
      return
    if member == ctx.author:
      embed = discord.Embed(description=f"{emojis[2]} Did you just try to give yourself money?!", color=discord.Color.blue())
      await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
      return
    if amount == None:
      embed = discord.Embed(description=f"{emojis[2]} Please Provide a Valid Amount", color=discord.Color.blue())
      await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
      return
    await open_account(ctx.author)
    await open_account(member)
    bal1 = await update_bank(ctx.author)
    bal2 = await update_bank(member)
    if amount.lower() == "all" or amount.lower() == "maximum" or amount.lower() == "max":
      amount = bal1[0]
    amount = int(toFloat(amount))
    if amount > bal1[0]:
      embed = discord.Embed(description=f"{emojis[2]} You don't have that much money in your Wallet", color=discord.Color.blue())
      await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
      return
    if amount < 0:
      embed = discord.Embed(description=f"{emojis[2]} Amount must be Positive", color=discord.Color.blue())
      await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
      return
    await update_bank(ctx.author,-1*amount)
    await update_bank(member,amount)
    bal1 = await update_bank(ctx.author)
    bal2 = await update_bank(member)
    embed = discord.Embed(description=f"You gave {member.display_name}{currencies[0]}**{amount:,}** ... Now, you have{currencies[0]}**{bal1[0]:,}** in your Wallet & they have{currencies[0]}**{bal2[0]:,}**", color=discord.Color.blue())
    await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
  
  @transfer.error
  async def transfer_error(self,ctx,error):
    if isinstance(error,commands.MissingRequiredArgument) or isinstance(error,commands.BadArgument):
      embed = discord.Embed(description=f"{emojis[2]} Please Mention a Valid User", color=discord.Color.blue())
      await ctx.send(embed=embed,reference=ctx.message,mention_author=False)
    
async def setup(client):
  await client.add_cog(Economy(client))