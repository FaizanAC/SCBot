import discord
import youtube_dl
import os
import shutil
import urllib.parse, urllib.request, re
from discord.ext import commands
from discord.utils import get

# Discord Token goes here
token = ''

# Create prefix for Bot
bot = commands.Bot(command_prefix = 'sc-')

# Dictionary for Queues
queues = {}

# Events
@bot.event
async def on_ready():
    print('Bot is ready.')  

@bot.command(pass_context = True, aliases = ['j'], brief='Join a Voice Channel')
async def join(ctx):
    # Check if author has joined a Channel
    in_channel = ctx.message.author.voice
    voice = get(bot.voice_clients, guild = ctx.guild)

    if in_channel:
        channel = ctx.message.author.voice.channel
        # If connected and in voice channel, move bot to channel
        if voice and voice.is_connected():
            await voice.move_to(channel) # Move to Channel
        # If in voice channel and not connected, connect
        else:
            voice = await channel.connect() # Connect to Channel
        # Send message to Discord chat
        await ctx.send(f"Joined {channel}")
    else:
        await ctx.send("You are not connected to a voice channel")

@bot.command(pass_context = True, aliases = ['l'], brief='Leave a Voice Channel')
async def leave(ctx):
    # Check if author has joined a Channel
    in_channel = ctx.message.author.voice
    voice = get(bot.voice_clients, guild = ctx.guild)

    if in_channel:
        channel = ctx.message.author.voice.channel
        # If connected and in voice channel, disconnect bot
        if voice and voice.is_connected():
            await voice.disconnect() # Disconnect
            await ctx.send(f"Left {channel}")
        else:
            await ctx.send("I am not connected to a voice channel") 
    else:
        await ctx.send("You are not connected to a voice channel")        

# Commands
@bot.command(aliases = ['s'], brief='Search for track on SoundCloud')
async def search(ctx, *, track,):
    # Remove spaces to allow for proper search
    track = track.replace(' ', '-').lower()
    # Encode the requeted Track Title
    search_string = urllib.parse.quote(track)
    # Concatenate encoded Track Title to SoundCloud search link
    htm_content = urllib.request.urlopen(
        'https://soundcloud.com/search/sounds?q=' + search_string
    )
    # Search for any pattern that matches using regex, pattern must contain a referecne to Track Title
    search_result = re.findall(fr'href=\"/.*?/.*?{track}.*?\">(.*?)</a>', htm_content.read().decode())
    # Print Select Statement
    await ctx.send("Type sc-# to select an option")
    # Display options 1 through 5
    for x in range(4):
        await ctx.send('[' + str(x+1) + '] - ' + search_result[x])

    # Now that the options are up, retrive a selection
    # Code yet to be completed for selecting an option

@bot.command(pass_context = True, aliases = ['p'], brief='Play a track with a URL')
async def play(ctx, url: str):
    
    # Function to create new directory called "Queue" and add all Queued songs to it
    def check_queue():
        queues_folder = os.path.isdir("./Queue")
        # If Queue folder does exist
        if queues_folder is True:
            full_path = os.path.abspath(os.path.realpath("Queue"))
            length = len(os.listdir(full_path))
            # Take the first file out of the folder, if not available then queue is empty
            try:
                first_file = os.listdir(full_path)[0]
            except:
                queues.clear()
                return
            main_folder = os.path.dirname(os.path.realpath(__file__)) # Retrive Main project location
            audio_path = os.path.abspath(os.path.realpath("Queue") + "\\" + first_file) # Create path for first song added to queue
            # Ensure there are still Queued tracks
            if length != 0:
                audio_ready = os.path.isfile("audio.mp3")
                if audio_ready:
                    os.remove("audio.mp3")
                # Move song from Queues folder to Main location so it can be played
                shutil.move(audio_path, main_folder)
                for file in os.listdir("./"):
                    if file.endswith(".mp3"):
                        os.rename(file, 'audio.mp3')

                # Checks if song is done playing, if finished call function to Check Queue
                voice.play(discord.FFmpegPCMAudio("audio.mp3"), after = lambda e: check_queue())
                voice.source = discord.PCMVolumeTransformer(voice.source) # Setting limit to Audio volume
                voice.source.volume = 0.05
            else:
                queues.clear()
                return
        else:
            # Empty Queues Dictionary
            queues.clear()
    
    # Check to see if song available
    audio_file = os.path.isfile("audio.mp3")
    
    # Try to remove previous stored Audio File
    try:
        if audio_file:
            os.remove("audio.mp3")
            queues.clear()
    except PermissionError:
        # If Audio is being used, return message
        await ctx.send("Playing Music Currently, Please add to Queue")
        return

    # Remove Queues folder 
    queues_folder = os.path.isdir("./Queue")
    try:
        Queue_folder = "./Queue"
        if queues_folder is True:
            shutil.rmtree(Queue_folder)
    except:
        print("No Queue Folder")
    
    await ctx.send("Downloading Audio")
    
    # Get voice
    voice = get(bot.voice_clients, guild = ctx.guild)

    # Ensuring the Bot/Author are connected to voice channels
    if voice and voice.is_connected():
        # Yotube download Options for Audio using FFmpeg
        ydl_opts = {
            'quiet': True,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredquality': '192',
                'preferredcodec': 'mp3'
            }]
        }

        # Pass in options
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            print('Downloading Audio')
            ydl.download([url])

        # Check if file is in the directory, rename it accordingly
        for file in os.listdir("./"):
            if file.endswith(".mp3"):
                name = file
                print(f'Renamed File: {file}')
                os.rename(file, "audio.mp3")

        # Checks if audio is done playing, if finished call function to Check Queue
        voice.play(discord.FFmpegPCMAudio("audio.mp3"), after = lambda e: check_queue())
        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = 0.05

        # Split Youtube track title to display the current song playing
        newname = name.rsplit("-", 2)
        await ctx.send(f"Playing: {newname[0]}")
        print("Playing")
    else: 
        await ctx.send("One of us is not connected to a voice channel\nPlease join and add me with **sc-join**")

@bot.command(pass_context = True, brief='Pause Audio')
async def pause(ctx):
    voice = get(bot.voice_clients, guild = ctx.guild)

    if voice and voice.is_playing():
        voice.pause() # Pause Audio
        await ctx.send("Music has been paused")
    else:
        await ctx.send("Music is not playing")

@bot.command(pass_context = True, aliases = ['r'], brief='Resume Audio')
async def resume(ctx):
    voice = get(bot.voice_clients, guild = ctx.guild)

    if voice and voice.is_paused():
        voice.resume() # Resume Audio
        await ctx.send("Resumed Music")
    else:
        await ctx.send("Music is not Playing")

@bot.command(pass_context = True, brief='Skip Audio')
async def skip(ctx):
    voice = get(bot.voice_clients, guild = ctx.guild)

    if voice and voice.is_playing():
        voice.stop() # Skip track
        await ctx.send("Skipping Current Song")
    else:
        await ctx.send("Music is not playing")
       
@bot.command(pass_context = True, aliases = ['c'], brief='Clear Queue')
async def clear(ctx):
    voice = get(bot.voice_clients, guild = ctx.guild)

    # Clear Queues Dictionary
    queues.clear()

    # Delete Queues folder to clear all tracks
    queues_folder = os.path.isdir("./Queue")
    if queues_folder:
        shutil.rmtree("./Queue")

    if voice and voice.is_playing():
        voice.stop() # Stop Audio for current track
        await ctx.send("Music has been cleared")
    else:
        await ctx.send("Music is not playing")

@bot.command(pass_context = True, aliases = ['q'], brief='Add track to Queue')
async def queue(ctx, url: str):
   
    await ctx.send("Downloading Audio")

    # Get voice
    voice = get(bot.voice_clients, guild = ctx.guild)

    # Ensuring the Bot/Author are connected to voice channels
    if voice and voice.is_connected() and voice.is_playing():
        queues_folder = os.path.isdir("./Queue")
        # Check to see if Directory is available, if not, create it to store Queued tracks
        if queues_folder is False:
            os.mkdir("Queue")
        full_path = os.path.abspath(os.path.realpath("Queue"))
        queue_num = len(os.listdir(full_path))
        queue_num += 1
        add_queue = True

        while add_queue:
            if queue_num in queues:
                queue_num += 1
            else:
                add_queue = False
                queues[queue_num] = queue_num
            
        # Create Path to download Audio into
        queue_path = os.path.abspath(os.path.realpath("Queue") + fr"\audio{queue_num}.%(ext)s")
        
        # Youtube download options when converting to mp3
        ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'outtmpl': queue_path, # Download Audio in specified path
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredquality': '192',
                    'preferredcodec': 'mp3'
                }]
            }

        # Pass in Download Options
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            print('Downloading Audio')
            ydl.download([url])
        await ctx.send("Added the Track to the queue")
    elif not voice.is_playing():
        await ctx.send("Audio is not being played, Use **sc-play** before Queuing")
    else:
        await ctx.send("One of us is not connected to a voice channel\nPlease join and add me with **sc-join**")

@bot.command(pass_context = True, brief='Play a Playlist wiht a URL')
async def playlist(ctx, url: str):
    await ctx.send("Playlist feature being updated")

# Discord token 
bot.run(token)
