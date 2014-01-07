# Author: Vikram Melapudi aka makechaos (makechaos [at] gmail [dot] com)
# Updated: 07 Jan 2014
# Started: 25 Dec 2013

import flickr_api

logFile = 'pyflickr.log'
resize = (1,1)
fd = open('flickr.key','r')
kdat = fd.readlines()
fd.close()
flickr_api.set_keys(api_key=kdat[0].strip(), api_secret=kdat[1].strip())

def log(msg,typ='a'):
  global logFile

  fd = open(logFile,typ)
  fd.write(msg+'\n')
  fd.close()

def setLog(fil='pyflickr.log'):
  import datetime
  global logFile 

  logFile = fil
  log('Created on '+datetime.datetime.now().strftime('%x %X'),'w')

def firstTimeUser(user):
  log('Create first-time login-auth for user='+user)
  a = flickr_api.auth.AuthHandler()
  url = a.get_authorization_url('write')
  print 'Copy-paste this url : '+url
  tok = raw_input('Copy-paste the resulting oauth-token here: ')
  a.set_verifier(tok)
  fil = '.'+user+'_flickr'
  a.save(fil)
  return fil
  
def getUserLogin(user):
  import os
  fil = '.'+user+'_flickr'
  log('Trying to access user-auth-token file %s'%(fil))
  if os.access(fil,os.F_OK):
    return fil
  else:
    return firstTimeUser(user)

def uploadPhoto(fil,titl):
  import datetime
  from PIL import Image
  global resize
  
  msg = 'ResizeOption[%d, %d] '%resize
  dt1 = datetime.datetime.now()
  if not ((resize[0]==1) and (resize[1]==1)):
    rsz = resize
    im = Image.open(fil)
    if resize[0]==0:
      rsz = (100000, resize[1])
    elif resize[1]==0:
      rsz = (resize[0], 100000)
    else:
      rat = resize[0]
      rsz = (round(im.size[0]*rat), round(im.size[1]*rat))
    msg += '... Orginal[%d,%d] -->'%im.size
    im.thumbnail(rsz,Image.ANTIALIAS)
    msg += 'Final[%d, %d]'%im.size
    im.save('tmp.jpg')
    fil = 'tmp.jpg'
    
  ph = flickr_api.upload(photo_file=fil, title=titl)
  dt2 = datetime.datetime.now()
  dd = dt2 - dt1
  msg += '... Uploaded photo %s, title %s, in %d s'%(fil, titl, dd.seconds)
  log(msg)
  return ph

def syncAlbumPhotos(user, album, photos):
  import datetime
  
  t1 = datetime.datetime.now()

  summ = 'Created by PhotoAccess on %s'%(datetime.datetime.now().strftime('%x %X'))
  log(summ)

  if len(photos)<1:
    log('No photos to be added to %s for user=%s'%(album,user))
    return
  else:
    log('%d photos to sync for album %s in user %s'%(len(photos),album,user))

  flickr_api.set_auth_handler( getUserLogin(user) )
  fusr = flickr_api.test.login()
  log('Using user login :'+str(fusr.username))

  # check if album exists
  psets = fusr.getPhotosets()
  log('Found %d photosets'%len(psets))
  galbum = None
  for m in psets:
    if str(m.title) == album:
      galbum = m
      break

  # Sync PHOTOS
  nupload = 0
  nrm = 0
  uphs = []
  ephs = []
  # upload photos not in album
  gphotos = fusr.getPhotos()
  log('Found %d photos for user %s'%(len(gphotos),user))
  gph = dict()
  for m in gphotos:
    gph[m.title] = m
  for m in photos.keys():
    if m not in gph.keys():
      nupload = nupload + 1
      ph = uploadPhoto(photos[m], m)
      uphs += [ph]
    else:
      ephs += [gph[m]]
      
  # Add uploaded photos to album/photoset
  if (galbum == None):
    # create album if not already present
    log('Creating new album %s'%album)
    uphs += ephs
    galbum = flickr_api.Photoset.create(title=album, primary_photo=uphs[0] )
    for m in range(1,len(uphs)):
      galbum.addPhoto(photo=uphs[m])
  else:
    gphotos = galbum.getPhotos()
    gph = dict()
    for m in gphotos:
      gph[m.title] = m
    log('Found %d photos in album %s'%(len(gphotos), album))
    # add existing (already uploaded for another album) photos
    for m in ephs:
      if m.title not in gph.keys():
        galbum.addPhoto(photo=m)
    # add newly uploaded photos
    for m in range(0,len(uphs)):
      galbum.addPhoto(photo=phs[m])

    # Remove photos from photoset/album (photos are not deleted
    #       though, cab be found in photostream!)
    for m in gph.keys():
      if m not in photos.keys():
        galbum.removePhoto(photo=gph[m])
        nrm = nrm + 1

  t2 = datetime.datetime.now()
  dt = (t2-t1).seconds
  msg = '%d uploaded, %d removed of %d photos in album %s to user A/C %s in %ds'%(nupload, nrm, len(photos.keys()), album, user,dt)
  log(msg)
  print(msg)

def syncAll(user='vikrammelapudi'):
  import datetime
  from pymongo import MongoClient

  ctime = datetime.datetime.now()
  cl = MongoClient('localhost',1951)
  db = cl['PhotoDB-6']['Photos']
  aa = db.find({'AlbumAcc':'flickr'})
  if aa.count()==0:
    ltime = datetime.datetime(1970,1,1)
    db.insert( {'AlbumAcc':'flickr', 'AlbumSync':ltime } )
  else:
    ltime = aa[0]['AlbumSync']
  ent = db.find({'EditTime':{'$gte' : ltime}})
  print('Found %d albums to sync with flicr (%s)'%(ent.count(),user))
  for m in ent:
    alb = m['AlbumEdit']
    print('\t... syncing album %s'%(alb))
    syncAlbum(alb, user)
  db.update( {'AlbumAcc':'flickr'}, {'$set': {'AlbumSync':ctime}})

def resetSync():
  from pymongo import MongoClient
  import datetime

  cl = MongoClient('localhost',1951)
  db = cl['PhotoDB-6']['Photos']
  aa = db.find({'AlbumAcc':'flickr'})
  ltime = datetime.datetime(1970,1,1)
  if aa.count()==0:
    db.insert( {'AlbumAcc':'flickr', 'AlbumSync':ltime } )
  else:
    db.update( {'AlbumAcc':'flickr'}, {'$set' : {'AlbumSync':ltime}} )

def syncAlbum(album, user='vikrammelapudi'):
  from pymongo import MongoClient
  cl = MongoClient('localhost',1951)
  db = cl['PhotoDB-6']['Photos']
  ph = dict()
  for m in db.find({'Albums':album}):
    fil = str(m['File'])
    fn = fil.split('/')
    fn = fn[len(fn)-1]
    ph[str(m['Model'])+'_'+fn] = fil
  syncAlbumPhotos(user,album,ph)

def usage():
  print('Options:')
  print('\t<user> -syncall [<-fullsize> <-scale scale-ratio> <-scaleh height> <-scalew width>]: to sync all albums')
  print('\t<user> -reset  [<-scale scale-ratio>]: to reset last-sync time')
  print('\t<user> -sync1 <album>  [<-scale scale-ratio>]: sync only one album')
  print('\t<user> -adduser : add & authenticase user ')
  print('')


def setResize(opt=None):
  import string
  global resize
  
  if opt==None:
    log('setResize no options! - set default (height=480)')
    resize = (0,480)
    return

  log('setResize : [%s]'%(string.join(opt,' ')))
  if opt[0]=='-fullsize':
    log('use full (original) size of image during upload')
    resize = (1,1)
    return

  try:
    if opt[0]=='-scale':
      rat = float(opt[1])
      if rat>3:
        rat = 3
      if rat>0:
        resize = (rat,rat)
    elif opt[0]=='-scaleh':
      newh = int(opt[1])
      resize = (0, newh)
    elif opt[0]=='-scalew':
      neww = int(opt[1])
      resize = (neww, 0)
  except:
    log('Invalid scale/width/height value [%s], default to 1.0'%(sys.argv[m+1]))
    print('Invalid scale/width/height value [%s], default to 1.0'%sys.argv[m+1])

if __name__=="__main__":
  import sys
  import string

  try:
    usr = sys.argv[1]
    opt = sys.argv[2]

    for m in range(1,len(sys.argv)):
      if sys.argv[m].find('-scale')==0:
        setResize(opt[m:m+1])

    if opt == '-syncall':
      syncAll(usr)
    elif opt == '-reset':
      resetSync()
    elif opt == '-sync1':
      album = sys.argv[3]
      syncAlbum(album, usr)
    elif opt == '-adduser':
      firstTimeUser(user)
    else:
      usage()
  except:
    usage()


