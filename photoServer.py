# Author: Vikram Melapudi aka makechaos (makechaos [at] gmail [dot] com)
# Updated: 07 Jan 2014
# Started: 25 Dec 2013
# Summary: Backend of python server to process the user input and link with the MongoDB database

import photoServer
import web
import StringIO
import string
from PIL import Image
from pymongo import MongoClient

hostid='http://192.168.1.4:1451'
client = MongoClient('localhost',1951)
dbName = 'PhotoDB-6'
db = client[dbName]
coll = db['Photos']
gopt = ''
showSizeText = False
dfmt = '%d-%b-%Y'
albumList = None
imPerPage = 50

## ******************************************************************************************** 
##    ALL HTML PAGE CODES
## ******************************************************************************************** 

def initHTML():
  txt = '<html><head><meta name="viewport" content="width=device-width, user-scalable=no">\n'
  txt+= '<style type="text/css">\n'
  txt+= '* {font-family: arial; border:0px; font-size:12px;}\n'
  txt+= 'txt {font-weight: bold;}\n'
  txt+= 'button {background-color:#774477; color:white; margin:5px;}\n'
  txt+= '.bodybtn {background-color:lightgray; color:black; }\n'
  txt+= '.greenbtn {cursor: pointer; float:left; display:block; margin:5px; padding:5px; border-radius: 5px; background-color:lightgreen;}\n'
  txt+= '.graybtn {cursor: pointer; float:left; display:block; margin:5px; padding:5px; border-radius: 5px; background-color:lightgray;}\n'
  txt+= '.bluebtn {cursor: pointer; float:left; display:block; margin:5px; padding:5px; border-radius: 5px; background-color:lightblue;}\n'
  txt+= '.sel {margin:5px; float:left; width:160px; background-color:lightblue; position:relative;}\n'
  txt+= '.nosel {margin:5px; float:left; width:160px; background-color:white; position:relative;}\n'
  txt+= '</style></head>\n'
  return txt

def homeBanner(src):
  txt = '<div align="center">'
  txt += '<table style="width:100%; background-color:#663366;"><tr>\n'
  #txt +='<td><button onclick=bylist("Albums")>By Albums</button></td>'
  #txt +='<td><button onclick=bylist("Tags")>By Tags</button></td>'
  #txt +='<td><button onclick=bylist("Date")>By Date</button></td>'
  #txt +='<td><button onclick=bylist("Model")>By Model</button></td>'
  txt += '<td><div style="margin:10px;"><a href="'+hostid+'/home" style="font-size:20px; color:white;">PhotoAccess v2.0</a></td>\n'
  txt += '<td><div style="font-size:14px; color:white;">Show <select id="opt" style="font-size:14px; border:0px; background-color:#663366; color:white;"> <option value="public">Public</option> <option value="all">All</option> <option value="private">Private</option> <option value="NoAlbum">No Albums</option> <option value="notag">No Tags</option> </select></div></a>\n'
  txt +='</tr>\n'
  txt +='</table></div><hr>\n' 
  return txt

def albumsDropdown():
  global albumList
  txt ='<select id="albums" style="background-color:#996699; color:#050505; border:0px;">\n'
  txt +='<option value="create-new" style="font-weight:bold;">New Album</option>\n'
  if albumList==None:
    albumList = getEntries('Albums')
  for m in albumList:
    dval = m[0]
    if len(dval)>15:
      dval = dval[:13]+'..'
    txt += '<option value="%s" style="color:blue;" >%s (%d)</option>\n'%(m[0],dval,m[1])
  txt +='</select>\n'
  return txt

def imageBanner():
  txt = '<div align="center">\n'
  txt +='<table style="width:100%; background-color:#663366;"><tr>\n'
  txt += '<td><div style="margin:10px;"><a href="'+hostid+'/home" style="font-size:20px; color:white;">PhotoAccess v2.0</a></div></td>\n'
  txt += '<td><button onclick="selall()">Toggle Sel.</button>\n'
  txt +=albumsDropdown()
  txt +='<button margin=10px onclick="addAlbum()" id="album">To Album</button>\n'
  txt +='<button margin=10px onclick="addTags()" id="tags">Tag-em</button>\n'
  txt +='<button margin=10px onclick="setPrivate()">As Private</button></td>\n'
  txt +='</tr>'
  txt +='</table></div><hr>'  
  return txt

def imageBannerAlbums():
  txt = '<div align="center">\n'
  txt +='<table style="width:100%; background-color:#663366;"><tr>\n'
  txt += '<td><div style="margin:10px;"><a href="'+hostid+'/home" style="font-size:20px; color:white;">PhotoAccess v2.0</a></div></td>\n'
  txt += '<td><button onclick="selall()">Toggle Sel.</button>\n'
  txt +=albumsDropdown()
  txt +='<button margin=10px onclick="addAlbum()" id="album">To Album</button>\n'
  txt +='<button margin=10px onclick="rmAlbum()" id="album">Remove-em</button>\n'
  txt +='<button margin=10px onclick="addTags()" id="rmAlbum">Tag-em</button>\n'
  txt +='<button margin=10px onclick="setPrivate()">As Private</button></td>\n'
  txt +='</tr>\n'
  txt +='</table></div><hr>\n'  
  return txt

def imageBannerTags():
  txt = '<div align="center">\n'
  txt +='<table style="width:100%; background-color:#663366;"><tr>\n'
  txt += '<td><div style="margin:10px;"><a href="'+hostid+'/home" style="font-size:20px; color:white;">PhotoAccess v2.0</a></div></td>\n'
  txt += '<td><button onclick="selall()">Toggle Sel.</button>\n'
  txt +=albumsDropdown()
  txt +='<button margin=10px onclick="addAlbum()" id="album">To Album</button>\n'
  txt +='<button margin=10px onclick="rmTag()" id="rmTag">Remove-em</button>\n'
  txt +='<button margin=10px onclick="addTags()" id="tags">Tag-em</button>\n'
  txt +='<button margin=10px onclick="setPrivate()">As Private</button></td>\n'
  txt +='</tr>\n'
  txt +='</table></div><hr>\n'  
  return txt


def addJS(src='',sel=''):
  txt = '<head><script>'
  txt += 'var nsel=0; var gsel="'+sel+'"; var hostid="'+hostid+'"; var gopt="/opt-'+gopt+'"; var query="'+src.replace('/',':')+'";\n'
  txt += 'function imselect0(id){el=document.getElementById(id); if(el.getAttribute("sel")=="0") { nsel++; gsel+=","+id; var stxt=el.style.cssText; stxt=stxt.substring(0, stxt.indexOf("background-color")); el.style.cssText =stxt+"background-color:lightblue;";  el.setAttribute("sel","1");} else { nsel--; el.setAttribute("sel","0"); var stxt=el.style.cssText; stxt=stxt.substring(0, stxt.indexOf("background-color")); el.style.cssText = stxt +"background-color:white;"; var sel=gsel+","; sel=sel.replace(","+id+",",","); gsel=sel.substring(0,sel.length-1);} }\n'
  txt += 'function imselect(id){el=document.getElementById("d"+id); if (el==null) { rmSel(id); return; } if(el.getAttribute("sel")=="0") { nsel++; gsel+=","+id; el.setAttribute("class","sel"); el.setAttribute("sel","1");} else { nsel--; el.setAttribute("sel","0"); el.setAttribute("class","nosel"); rmSel(id); }}\n'
  txt += 'function rmSel(id) { var sel=gsel+","; sel=sel.replace(","+id+",",","); gsel=sel.substring(0,sel.length-1); }\n'
  #txt += 'function resize(){location.assign("'+location.host+'/size=256");}';
  #txt += 'function nameChange() {txt=document.getElementById("name").value+"/"+gsel; document.getElementById("album").setAttribute("href",hostid+"/album/"+txt); document.getElementById("tags").setAttribute("href",hostid+"/tags/"+txt); alert(hostid+"/album/"+txt);}'
  txt += 'function validName() { if(document.getElementById("name").value.length<1) { alert("No name provided!"); return flase;} else return true; }\n'
  txt += 'function option() { var el=document.getElementById("opt"); return "/opt-"+el.options[el.selectedIndex].text; }\n'
  txt += 'function bylist(val) { window.location.href=hostid+option()+"/list/"+val; }\n'
  txt += 'function selNext(val) { window.location.href=hostid+"/"+val+"/sel="+gsel; }\n'
  txt += 'function selPrev(val) { window.location.href=hostid+"/"+val+"/sel="+gsel; }\n'
  txt += 'function showSelect() { window.location.href=hostid+"/select/"+query+gsel; }\n'
  txt += 'function addAlbum() {var el=document.getElementById("albums"); var nm=el.options[el.selectedIndex].value; if(nm.indexOf("create-new")==0) nm=prompt("Enter new album name:"); postPage(hostid+gopt+"/album/"+nm+"/"+query+gsel, false); }\n'
  txt += 'function postPage(url, reload) { /*window.location.href = url; */ var txt=httpGET(url); if(reload) location.reload(); showInfo( txt ); var ss=gsel.split(","); for(var m=1;m<ss.length;m++) { imselect(ss[m]); } gsel=""; }\n'
  txt += 'function impage() {var el=document.getElementById("impage"); var pg=el.options[el.selectedIndex].value; window.location.href=hostid+gopt+"/"+pg+"/sel="+gsel}\n'
  txt += 'function setPrivate() { postPage(hostid+gopt+"/private/"+query+gsel, false); }\n'
  txt += 'function httpGET(url) { var xmlHttp=null; xmlHttp=new XMLHttpRequest(); xmlHttp.open("GET", url, false); xmlHttp.send(null); return xmlHttp.responseText; }\n'
  txt += 'function rmAlbum() { var ss=gsel.split(","); for(var m=1;m<ss.length;m++) {el=document.getElementById(ss[m]); el.style.cssText+="visibility:hidden;"; } postPage(hostid+gopt+"/rmAlbum/"+query+gsel, true); }\n'
  txt += 'function rmTag() { var ss=gsel.split(","); for(var m=1;m<ss.length;m++) {el=document.getElementById(ss[m]); el.style.cssText+="visibility:hidden;"; } postPage(hostid+gopt+"/rmTag/"+query+gsel, true); }\n'
  txt += 'function addTags() { var tg=prompt("Enter the tags (separated by comma):"); postPage(hostid+gopt+"/tags/"+tg+"/"+query+gsel, false); }\n'
  txt += 'function iminfo(e,msg) { return; var el=document.getElementById("info"); el.innerHTML=msg; el.style.cssText="font-size:14px; background-color:#FFFF99; width:100%; color:#404040; visibility:visible; position:absolute; left:0px; top:0px;"; }\n'
  txt += 'function showInfo(msg) { var el=document.getElementById("info"); el.innerHTML=msg; el.style.cssText="font-size:11px; background-color:#FFFF99; width:100%; color:#404040; visibility:visible; position:absolute; left:0px; top:0px;"; }\n'
  txt += 'function selall() { var els=document.getElementsByTagName("img"); for (var el=0; el<els.length; el++){ imselect(els[el].getAttribute("id")); } }\n'
  txt += 'function hideinfo() {  var el=document.getElementById("info"); el.innerHTML=""; el.style.cssText="visibility:hidden;"; }\n'
  txt += '</script></head>'
  return txt

def errorPage(err):
  txt = initHTML()+addJS()+'<body>'
  txt += homeBanner("");
  txt += '<div align="center" style="font-size:20px;">'+err+'</div'
  txt += '</body></html>'
  fd = open('err.html','w')
  fd.write(txt)
  fd.close()
  return txt

def homeMessage(msg):
  return msg;
  txt = initHTML()+addJS()+'<body>'+homeBanner("")
  txt += '<div align="center" style="font-size:20px">'+msg+'</div>'
  txt += '</body></html>'
  return txt

## ********************************************************************************************

## ******************************************************************************************** 
##    PYMONGO (database inquiry routines)
## ******************************************************************************************** 

def fullQuery(qry):
  import string
  # add the option query to mongodb query
  
  if gopt=='No Albums':
    qry['Albums'] = []
  elif gopt=='No Tags':
    qry['Tags'] = []
  elif gopt=='Public':
    qry['Class'] = 'Public'
  elif gopt=='Private':
    qry['Class'] = 'Private'
  return qry

def getSelectedImages(inp,listby='Albums'):
  imgs = inp.split(',')
  typ = imgs[0].split(':')
  sim = []
  if len(typ)==0:
    return sim
  dbqry = getQuery(typ[0], typ[1])
  allim = coll.find(dbqry).sort('Date')
  for m in range(1,len(imgs)):
    nn = int(imgs[m][4:len(imgs[m])])
    fil = allim[nn]["File"]
    alb = allim[nn][listby]
    sim = sim + [[fil, alb]]
  return sim

def setClass(cls,inp):
  sim = getSelectedImages(inp)
  for m in sim:
    coll.update({"File":m[0]}, {"$set" : {"Class":cls}})
  return homeMessage("Set Private class for %d images."%len(sim))

def rmAlbum(inp):
  import datetime
  sim = getSelectedImages(inp)
  ss = inp.split(',')[0].split(':')
  n = 0
  qalb = ''
  for m in ss:
    if m=='Albums':
      qalb = ss[n+1]
      break
    n = n + 1
  for m in sim:
    alb = []
    for n in m[1]:
      if not(n==qalb):
        alb += [n];
    coll.update( {'File':m[0]}, { '$set' : {'Albums':alb}} )

  ctime = datetime.datetime.now()
  coll.update({'AlbumEdit':qalb},{'$set': {'EditLog':'remove %d images'%(len(sim)), 'EditTime':ctime } })

  return homeMessage('Removed %d images from album %s'%(len(sim),qalb))

def rmTag(inp):
  import datetime
  sim = getSelectedImages(inp,'Tags')
  ss = inp.split(',')[0].split(':')
  n = 0
  qtag = ''
  for m in ss:
    if m=='Tags':
      qtag = ss[n+1]
      break
    n = n + 1
  for m in sim:
    tag = []
    for n in m[1]:
      if not(n==qtag):
        tag += [n];
    coll.update( {'File':m[0]}, { '$set' : {'Tags':tag}} )

  return homeMessage('Untagged %d images from tag %s'%(len(sim),qtag))
    
def addAlbum(name,inp):
  import datetime
  
  sim = getSelectedImages(inp)

  ctime = datetime.datetime.now()
  aa = coll.find({'AlbumEdit':name})
  msg = '%d images'%(len(sim))
  if aa.count()==0:
    keyval = dict()
    keyval['AlbumEdit'] = name
    keyval['EditTime'] = ctime
    keyval['EditLog'] = 'New album with '+msg
    coll.insert( keyval )
  else:
    coll.update({'AlbumEdit': name}, {'$set': {'EditTime':ctime, 'EditLog':'added '+msg }})
    
  fd = open('Albums/'+name+'.abm','a')
  for m in sim:
    doupdate = False
    alb = []
    if type(m[1]) is list:
      if name not in m[1]:
        alb = m[1] + [name]
        doupdate = True
    elif len(m[1])>0:
      # if no album was ever set or set as string
      alb = [m[1]]
      doupdate = True 
    if doupdate:
      coll.update({"File" : m[0]}, {"$set" : { "Albums" : alb } })
    fd.write(m[0]+'\n')
  fd.close()
  return homeMessage('Added %d images to album %s</div>'%(len(sim),name))

def addTags(tags,inp):
  sim = getSelectedImages(inp)
  taglst = tags.split(',')
  for m in sim:
    tgs = coll.find({'File':m[0]})[0]['Tags']
    if type(tgs) is list:
      for n in taglst:
        if n.strip() not in tgs:
          tgs += [n.strip()]
    coll.update({'File':m[0]}, {'$set':{'Tags':tgs}})

  return homeMessage('Added tag(s) (%s) to %d images</div>'%(tags,len(sim)))

def getDistinctLists(key):
  from bson.code import Code

  mapper = Code(" function() { if('"+key+"' in this) { this."+key+".forEach( function(z){emit(z,1);} ) } } " )
  reducer= Code(" function(key,val) { var tot=0; for(var i=0;i<val.length;i++)tot+=val[i]; return tot;} ")
  res = coll.map_reduce(mapper, reducer, "album")
  return res.find()

def getDistinctEntries(key):
  from bson.code import Code

  mapper = Code(" function() { if('"+key+"' in this) { emit(this."+key+",1); } } ")
  reducer= Code(" function(key,val) { var tot=0; for(var i=0;i<val.length;i++)tot+=val[i]; return tot;} ")
  res = coll.map_reduce(mapper, reducer, "album")
  return res.find()

def getDistinctMonths():
  from bson.code import Code

  mapper = Code(" function() { if('Date' in this) { emit(this.Date.toUTCString().substring(8,16),1); } } " )
  reducer= Code(' function(key,val) { var tot=0; for(var i=0;i<val.length;i++)tot+=val[i]; return tot;} ')
  res = coll.map_reduce(mapper, reducer, "album")
  return res.find()

def fmt(st):
  import datetime
  if type(st) is datetime.datetime:
    return st.strftime(dfmt)
  if type(st) is str:
    return st
  return st

def getEntries(key):
  if key=="Albums" or key=="Tags":
    res = getDistinctLists(key)
  elif key=="Date":
    res = getDistinctMonths()
  elif key=="Date" or key=="Model" or key=="Folder":
    res = getDistinctEntries(key)
  else:
    return None

  lst = []
  for m in res:
    lst += [ [fmt(m['_id']), int(m['value']) ]]
  return lst


def serveImage(name,sz=128):
  try:
    img = Image.open(name)
    img.thumbnail((sz,sz),Image.ANTIALIAS)
  except:
    return name.replace("/","-")
  web.header('Content-type', 'image/PNG');
  buf = StringIO.StringIO()
  img.save(buf,'PNG')
  return buf.getvalue()

def getQuery(key, val):
  import datetime
  import calendar

  dbqry = dict()  
  if key=='Date':
    dt1 = datetime.datetime.strptime(val,'%b %Y')
    dt2 = datetime.datetime(dt1.year, dt1.month, calendar.monthrange(dt1.year, dt1.month)[1])
    dt2 = datetime.datetime(dt2.year, dt2.month, dt2.day, 23, 59, 59)
    dbqry["Date"] = { "$gte": dt1, "$lte": dt2 }
  else:
    dbqry[key] = val
  dbqry = fullQuery(dbqry)
  return dbqry


## ******************************************************************************************** 

## ******************************************************************************************** 
##    Server pages
## ******************************************************************************************** 

def showSelection(inp):
  fd = open('tt.txt','w')
  fd.write(inp)
  fd.close()
  txt = initHTML()+addJS("")
  txt+= '<body><div align="center">'  
  txt+= imageBanner('');
  sim = getSelectedImages(inp)
  txt+= 'Selected %d images<br>'%len(sim)
  for m in sim:
    txt += '<img src="'+hostid+'/image=256'+m[0]+'"><br><br>\n'
  txt+= '</div></body></html>'  
  return txt

def homePage():
  global albumList
  keys = ['Model','Albums','Folder','Date','Tags']
  gorb = True
  txt = initHTML()+addJS()+'<body>'
  txt += homeBanner('')
  txt += '\n<table>'
  for key in keys:
    ents = getEntries(key)
    if key=="Albums":
      albumList = ents
    txt += '<tr width="100%"><td> <txt style="valign:bottom; font-size:16px; padding-top:10px;">'+key+'</txt></td></tr>\n'
    txt += '<tr width="100%"><td>\n'
    cls = 'bluebtn'
    if gorb:
      cls = 'greenbtn'
    gorb = not(gorb)
    if ents==None or len(ents)==0:
      txt +='<div class="graybtn"> No entries found !</div>'
    else:
      for m in ents:
        txt += '<div class="'+cls+'" onclick="bylist('+"'"+key+"/"+m[0]+"'"+')">'
        txt += '<div align="center"><txt>'+ m[0] + '</txt>('+ str(m[1]) +')</div></div>'
    txt += '<br></td></tr>\n'
  txt += '</table>\n</body></html>'
  return txt

def listImages(npg,inp):
  import string
  import datetime
  import calendar
  from PIL import Image

  if len(inp)<1:
    return errorPage('No images to list!')

  sel = ''
  key = inp[0]
  val = inp[1]
  dbqry = getQuery(key, val)

  imgs = coll.find(dbqry).sort('Date')
  nimg = coll.find(dbqry).count()
  sz = "size=128"
  for m in range(2,len(inp)):
    if inp[m].find('size')>-1:
      sz =inp[m].split("=")[1]
    elif inp[m].find('sel')==0:
      sel = inp[m].split('=')[1]
  ssel = sel + ','
  if nimg>0:
    txt = initHTML()+addJS(key+':'+fmt(val),sel)+'<body>'
    if key=='Albums':
      txt += imageBannerAlbums()
    elif key=='Tags':
      txt += imageBannerTags()
    else:
      txt += imageBanner()
    txt += '<div align="center" style="width:100%;"><div id="info" width="100%" style="color:gray; visibility:hidden; position:absolute;"></div>'

    tpg = int(nimg/imPerPage)
    if tpg*imPerPage<nimg:
      tpg = tpg+1
    ns = npg*imPerPage
    ne = ns+imPerPage
    if ns<0:
      ns = 0
      ne = imPerPage
    if ns>nimg:
      ns = nimg
      ne = nimg
    if ne>nimg:
      ne = nimg
    opttxt = ''
    if len(gopt)>0:
      opttxt = 'opt-'+gopt+'/'
    keyval = '/'+key+'/'+fmt(val)
    if npg>0:
      txt += '<button class="bodybtn" id="prev" onclick="selPrev('+"'"+opttxt+'list-pg'+str(npg-1)+keyval+"'"+')">prev</button> ... '
    txt += 'showing '    
    if nimg<=imPerPage:
      txt+=str(ns+1)+'-'+str(ne)
    else:
      pg = 0
      nn = 1
      txt+='<select onchange="impage()" id="impage" style="border:0px; background-color:white;">'
      while(nn<=nimg):
        en = nn + imPerPage-1
        if(en>nimg):
          en = nimg
        sl = ''
        if pg==npg:
          sl = 'selected'
        txt += '<option value="list-pg'+str(pg)+keyval+'" '+sl+'>'+str(nn)+'-'+str(en)+'</option>\n'
        nn = nn + imPerPage
        pg = pg + 1
      txt+='</select>'
    txt+=' out of '+str(nimg)+' images in '+key+"="+fmt(val)+"."
    if ne<nimg:
      txt += ' ... <button class="bodybtn" id="next" onclick="selNext('+"'"+opttxt+'list-pg'+str(npg+1)+keyval+"'"+')">next</button>'
    txt += '</div><br><div align="center">'
    nim = 0
    for n in range(ns,ne):
      m  = imgs[n]
      fil = str(m["File"])
      imid = 'img-'+str(n)
      iminf= '' #'File: '+fil+', Model: '+m['Model']+', Date: '+fmt(m['Date'])+', Albums:'+string.join(m['Albums'],',')+', Tags:'+string.join(m['Tags'],',')
      
      sztxt = ''
      if showSizeText:
        imsz = Image.open(fil).size
        sztxt= str(imsz[0]) + ' x ' + str(imsz[1]) + ' px'
      
      imlnk= hostid+'/image'+fil
      titl = '' #str(nim) #date+", "+make
      stxt = 'class="nosel" sel="0"'
      if ssel.find(',img-%d,'%n)>-1:
        stxt = 'class="sel" sel="1"'
      txt += '<div align="center" onmouseout="hideinfo()" onmouseover="iminfo(event,'+"'"+iminf+"'"+')" onclick="imselect('+"'"+imid+"'"+')" id="d'+imid+'" '+stxt+'>'
      txt += '<img id="'+imid+'" src="'+imlnk+'" alt="'+fil+'">'
      txt += '<div style="position:absolute; bottom:0px; left:0px; opacity:0.7; background-color:lightgray;">'+sztxt+'</div>'
      txt += titl
      txt += '</div>\n'#<spacer width="20px"/>\n'
      nim += 1
    txt += '</div></body></html>'
    fd = open('img.html','w')
    fd.write(txt);
    fd.close()
    return txt
  else:
    txt = initHTML()+addJS()
    txt+= '<body>'+homeBanner('')
    txt+= '<div align="center" style="font-size:20px; font-weight:bold;"> No images found to show! </div></body>'
    return txt

def log(msg,mode='a'):
  fd = open('serverLog.txt',mode)
  fd.write(msg+'\n')
  fd.close()

def savePage( pg ):
  fd = open('page.html','w')
  fd.write(pg);
  fd.close()


def photoServe(name):
  import string
  import datetime
  global gopt
  global showSizeText
  inp = name.split("/");

  log(datetime.datetime.now().strftime('%x %X')+' '+name)
  
  # get the options string out
  showSizeText = False
  iinp = []
  for m in inp:
    if m.find('opt') == -1:
      iinp += [m]
    else:
      gopt = m.split('-')[1]
      if m.find('-showsize')>=0:
        showSizeText = True

  inp = iinp

  if name=="" or inp[0].find('home')==0:
    page = homePage()
    savePage( page )
    return page

  if len(inp)<2:
    return errorPage('Unknown error '+name)

  elif inp[0].find("list")==0:
    tmp  = inp[0].split('-')
    npg  = 0
    if len(tmp)>1:
      if tmp[1].find('pg')==0:
        npg = int(tmp[1][2:len(tmp[1])])
    return listImages(npg, inp[1:len(inp)])

  elif inp[0].find('private')==0:
    return setClass('Private',inp[1])

  elif inp[0].find('rmAlbum')==0:
    return rmAlbum(inp[1])

  elif inp[0].find('rmTag')==0:
    return rmTag(inp[1])

  elif inp[0].find('syncdir')==0:
    import addDirImagesToDB
    import string

    if len(inp)>1:
      ddir = ''
      for m in range(1,len(inp)):
        ddir += '//'+inp[m] 
      jfil = addDirImagesToDB.scanDirForPhotos(ddir)
      addDirImagesToDB.addFilesToDB(jfil)
      txt = '<html><body>'+homeBanner('')+'<h1>Log from photo-scanner program:</h1><br>'
      fd = open('.lastupdate_'+dbName,'r')
      for m in fd.readlines():
        txt += m +'<br>\n'
      fd.close()
      txt+= '</body></html>'
      return txt

  elif inp[0].find('sync')==0:
    import pyflickr
    
    pyflickr.setLog()
    if len(inp)>2:
      pyflickr.setResize(inp[2].split(' '))
    else:
      pyflickr.setResize(None)
    pyflickr.syncAlbum(inp[1],'vikrammelapudi')

    fd = open('pyflickr.log','r')
    txt = '<html><body>'+homeBanner('')
    txt += '<h1>Log from flickr-sync program:</h1><br>'
    for m in fd.readlines():
      txt += m+'<br>\n'
    txt += '</body></html>'
    fd.close()
    return txt

  elif inp[0].find("image")==0:
    szin = inp[0].split("=")
    sz = 128
    if len(szin)>1:
      sz = int(szin[1])
    ff = ''
    for m in range(1,len(inp)):
      ff += '//'+inp[m] 
    return serveImage(ff,sz)

  elif inp[0].find("album")==0:
    return addAlbum(inp[1],inp[2])

  elif inp[0].find("tags")==0:
    return addTags(inp[1],inp[2])

  else:
    return errorPage('Unknown request '+string.join(inp)+', '+name)

  return errorPage('Unknown error '+name)
