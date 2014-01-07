# Author: Vikram Melapudi aka makechaos (makechaos [at] gmail [dot] com)
# Updated: 07 Jan 2014
# Started: 25 Dec 2013


import web
from photoServer import photoServe

urls = (
  '/(.*)', 'hello'
)

app = web.application(urls, globals())

class hello:
  def GET(self, name):
    return photoServe(name)

if __name__ == "__main__":
  app.run()

app = web.application(urls, globals())

class hello:
  def GET(self, name):
    return photoServe(name)

if __name__ == "__main__":
  app.run()
