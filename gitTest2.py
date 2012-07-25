import pycurl, json,sys

resource = 'https://api.github.com/repos/%s/issues' % sys.argv[2]
token = "a061fe5e8fafc96c561093f44620e864d290b805"
data = sys.argv[1]
c = pycurl.Curl()
c.setopt(pycurl.URL, resource)
c.setopt(pycurl.HTTPHEADER, ['Authorization: token %s' % token])
c.setopt(pycurl.POST, 1)
c.setopt(pycurl.POSTFIELDS, data)
print c.perform()
c.close()