# Author: Vikram Melapudi aka makechaos (makechaos [at] gmail [dot] com)
# Updated: 07 Jan 2014
# Started: 25 Dec 2013

import os
import sys
from pymongo import MongoClient
from datetime import datetime

dbname = 'PhotoDB-6'
updfil = '.lastupdate'+'_'+dbname

def getJpegHeader(fname):
  from PIL import Image
  from PIL.ExifTags import TAGS
  import datetime
  import os

  i = Image.open(fname)
  inf = i._getexif();
  dat = dict()
  sdir = os.path.abspath(fname).split('/')
  ddir = ''
  ldir = 'NA'
  for m in range(1,len(sdir)-1):
    ddir += '/'+sdir[m]
  if len(sdir)>1:
    ldir = sdir[len(sdir)-2]
  dat["Path"] = ddir
  dat["Folder"] = ldir
  dat["File"] = fname
  for tag, value in inf.items():
    ttag = TAGS.get(tag,tag)
    if ttag=="Model":
      mk = ''
      if 'Make' in dat:
        mk = dat['Make']
      cam = value + "_" + mk
      cam = cam.replace(' ','_')
      cam = cam.replace('-','_')
      dat["Model"] = cam
    elif ttag=="DateTimeOriginal":
      dt = value.split(" ")[0]
      dtv= dt.split(":")
      tm= value.split(" ")[1]
      tmv = tm.split(":")
      dat["Date"] = datetime.datetime(int(dtv[0]), int(dtv[1]), int(dtv[2]), int(tmv[0]), int(tmv[1]), int(tmv[2]))
  return dat

def getJpegHeaderAll(fname):
  from PIL import Image
  from PIL.ExifTags import TAGS
  import os

  i = Image.open(fname)
  inf = i._getexif();
  dat = dict()
  sdir = os.path.abspath(fname).split('/')
  ddir = ''
  ldir = 'NA'
  for m in range(1,len(sdir)-1):
    ddir += '/'+sdir[m]
  if len(sdir)>1:
    ldir = sdir[len(sdir)-2]
  dat["Path"] = ddir
  dat["Folder"] = ldir
  dat["File"] = fname
  for tag, value in inf.items():
    ttag = TAGS.get(tag,tag)
    dat[ttag] = value
  return dat
 
if __name__ == "__main__":
  if len(sys.argv)>1:
    for m in range(1,len(sys.argv)):
      fname = sys.argv[m]
      print(getJpegHeaderAll(fname))
 

def scanDirForPhotos(ddir,scanOnly=False):
  fils = os.walk(ddir)
  pupd = datetime(1900,1,1,1,1,1)
  if os.access(updfil,os.F_OK):
    fd = open(updfil,'r')
    txt = ''
    for m in fd.readlines():
      txt = m
      if m.find('Updated-on;')>=0:
        mm = m.strip('\n').split(';')
        pupd = datetime.strptime(mm[1].strip(),'%c')
    fd.close()

  print('Scanning %s for files after [%s]'%(ddir,pupd.strftime('%c')))
  fd = None
  if not scanOnly:
    fd = open(updfil,'w')
    fd.write('Last-update: '+pupd.strftime('%c')+'\n')
    fd.write('Scanning: '+ddir+'\n')
  jfil = []
  for rdir,cdirs,files in fils:

    st= os.stat(rdir)
    tm = datetime.fromtimestamp(st.st_mtime)
    if tm<pupd:
      print(rdir+'-- no updates, %s'%(tm.strftime('%c')))
      if not(fd==None):
        fd.write('NO UPDATE - '+rdir+'\n')
      continue
    else:
      if not(fd==None):
        fd.write('SCANNING  - '+rdir+'\n')
    nf = 0
    na = 0
    for fil in files:
      sfil = fil.split(".")
      st= os.stat(rdir)
      tm = datetime.fromtimestamp(st.st_mtime)
      if len(sfil)<2:
        continue
      tail = sfil[len(sfil)-1]
      if (tail=='JPEG') or (tail=='JPG') or (tail=='jpeg') or (tail=='jpg'):
        nf = nf + 1
        if tm<pupd:
          continue
        na = na + 1
        jfil += [rdir + '/' + fil]
    if scanOnly:
      print(rdir+'-- %d/%d to add'%(na,nf))
    else:
      fd.write('\t-- %d/%d added\n'%(na,nf))

  print('Found '+str(len(jfil))+' photo files')
  if not scanOnly:
    dt = datetime.now()
    fd.write('\nUpdated-on;'+dt.strftime('%c')+'\n')
    fd.close()
  return jfil

def addFilesToDB(jfil):
  client = MongoClient('localhost',1951)
  db = client[dbname]
  coll = db['Photos']
  t1 = datetime.now()
  for fil in jfil:
    dt = datetime.now().date()
    keyval = getJpegHeader(fil)
    keyval["Albums"] = []
    keyval["Tags"] = []
    keyval["Class"] = "Public"
    dt = datetime.now()
    keyval["dbDate"] = datetime(dt.year, dt.month, dt.day) #str(dt.year)+':'+str(dt.month)+':'+str(dt.day)
    coll.insert( keyval )
  t2 = datetime.now()
  dt = t2 - t1
  fd = open('.lastupdate_'+dbname,'a')
  fd.write('Added %d photos in DB in %d s'%(len(jfil), dt.seconds))
  fd.close()

def usage():
  print('Options:')
  print('\t -update <dir> : scan dir and update DB')
  print('\t -scan <dir> : only scan dir (no DB updates)')
  print('')

if __name__ == '__main__':
  try:
    if sys.argv[1] == '-update':
      jfil = scanDirForPhotos(sys.argv[2])
      addFilesToDB(jfil)
    elif sys.argv[1] == '-scan':
      jfil = scanDirForPhotos(sys.argv[2],True)
    else:
      usage()
  except:
    usage()
