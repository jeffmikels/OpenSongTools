#!/usr/bin/env python3
import os
from xml.etree import ElementTree as ET
from datetime import datetime


class Set():
  name = ''
  path = ''
  songs = []

  def __repr__(self):
    return '{}, {}, {}'.format(self.name, self.path, self.songs)

  def __init__(self, setpath):
    # print('opening set:', setpath)
    if not os.path.exists(setpath):
      return
    xml = ET.parse(setpath)
    root = xml.getroot()
    self.path = setpath
    self.name = root.attrib['name']
    self.songs = []
    slide_groups = xml.find('slide_groups')
    for slide_group in slide_groups:
      songpath = ''
      if slide_group.attrib['type'] == 'song':
        name = slide_group.attrib['name']
        try:
          subdir = slide_group.attrib['path']
        except:
          subdir = ''
        if subdir != '':
          songpath = os.path.join(songsdir, subdir, name)
        else:
          songpath = os.path.join(songsdir, name)
        if songpath != '':
          # print(songpath)
          song = Song(songpath)
          # print(song.name)
          if (song.name != ''):
            self.songs.append(song)
    # print(self.name)
    # print(self.songs)


class Song():
  path = ''
  lyrics = ''
  name = ''
  ccli = ''
  data = {}

  def __init__(self, songpath):
    # print('opening song:', songpath)
    if not os.path.exists(songpath):
      return
    xml = ET.parse(songpath)
    song = xml.getroot()
    self.path = songpath

    self.data = {}
    for element in song:
      # print(element.tag)
      # print(element.text)
      # print(element.attrib)
      self.data[element.tag] = element.text
    self.name = self.data['title']
    self.lyrics = self.data['lyrics']
    self.ccli = self.data['ccli']


class SongFolder():
  path = ''
  songs = []
  subfolders = []
  name = ''

  def __init__(self, folderpath):
    self.path = folderpath
    self.name = os.path.basename(folderpath)
    if not os.path.exists(folderpath):
      return

    for item in os.listdir(self.path):
      if '.' == item[0]:
        continue
      fp = os.path.join(self.path, item)
      if os.path.isdir(fp):
        self.subfolders.append(SongFolder(fp))
      else:
        self.songs.append(Song(fp))


class Library():
  sets = {}
  songfolder = None
  songstats = {}

  def __init__(self, new_librarypath):
    global setsdir
    global songsdir
    self.librarypath = new_librarypath

    setsdir = os.path.join(self.librarypath, 'Sets')
    songsdir = os.path.join(self.librarypath, 'Songs')
    self.songfolder = SongFolder(songsdir)

    # create sets listing
    for root, dirs, files in os.walk(setsdir):
      for basename in files:
        pathname = os.path.join(root, basename)
        try:
          songset = Set(pathname)
        except:
          # print("could not parse", basename)
          continue
        name = songset.name

        try:
          datestamp = datetime.strptime(name, "%Y-%m-%d")
        except:
          continue
        if datestamp < datetime.strptime("2012-01-01", "%Y-%m-%d"):
          continue

        self.sets[datestamp] = songset

        for song in songset.songs:
          if song.path == '':
            continue
          self.songs.append(song)
          songpath = song.path

          name = os.path.basename(songpath)
          if name not in self.songstats:
            self.songstats[name] = {
                "uses": 1, 'author': song.data['author'], 'copyright': song.data['copyright']}
          else:
            self.songstats[name]['uses'] += 1
