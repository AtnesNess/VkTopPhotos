import vk
import argparse
import webbrowser
import socket
import re
import datetime
import time

global from_date
global to_date
CURSOR_UP_ONE = '\x1b[1A'
ERASE_LINE = '\x1b[2K'

def authenticate(login, passw):
    print 'Authentication...'
    vkapi = vk.API('4927742', login, passw)
    vkapi.friends.get()
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('localhost', 8003))
    webbrowser.open_new("https://oauth.vk.com/authorize?"
                            "client_id=4927742&scope=photos&redirect_uri=localhost:8003&v=5.33&response_type=token ")
    sock.listen(10)
    conn, addr = sock.accept()
    try:



        message = """HTTP/1.1 200 OK
    Content-Type: text/html; charset=utf-8
    Content-Length: 200

    <html>

        <body>
            <h3> Auth OK </h3>
            <div id="loc"> 123</div>
            <script> window.location = (window.location.toString().replace("#", "?"));  window.location.close();</script>
        </body>
    </html>

        """
        message2 = """HTTP/1.1 200 OK
    Content-Type: text/html; charset=utf-8
    Content-Length: 200

    <html>

        <body>
            <h3> Auth OK </h3>

            <script>  window.close();</script>
        </body>
    </html>

        """

        conn.send(message)
        conn, addr = sock.accept()
        data =  conn.recv(3048)
        conn.send(message2)
        regexped = re.search(r"access_token=([0-9A-Za-z]*)&", data)
        token = regexped.group(1)
        print "token={}".format(token)

        vkapi.access_token = token
        print 'Authenticated'

    finally:
        conn.close()
        sock.close()
    return vkapi


def getLikesOfPhoto(photo, vkapi):
    try:
        time.sleep(0.3)
        return vkapi.likes.getList(type="photo", item_id=photo['id'])['count']
    except Exception:
        return getLikesOfPhoto(photo, vkapi)


def getMaxResolution(photo):
    hd = 0
    result = None
    for k,v in photo.items():
        regexped = re.search(r'photo_([0-9]*)', k)
        if regexped:
            resolution = regexped.group(1)
            if int(resolution) > hd:
                hd = int(resolution)
                result = v
    return result


def handlePhoto(photo, results, vkapi):
    if from_date is None or from_date < time.gmtime(photo['date']) < to_date:
            if "likes" in photo:
                likes = str(photo['likes']['count'])
            else:
                likes = str(getLikesOfPhoto(photo, vkapi))

            if likes in results:
                results[likes].append({"link": getMaxResolution(photo), "likes": likes})
            else:
                results[likes] = [{"link": getMaxResolution(photo), "likes": likes}]


def handleAlbum(album, vkapi, results):
    print u"handling '{}'...".format(unicode(album['title']))

    photos = vkapi.photos.get(album_id=album["id"])
    count = photos['count']
    i = 0

    for photo in photos['items']:
        progres_bar = "["
        for j in range(50):
            if j*2 < round(float(100)/count*i):
                progres_bar += "="
            else:
                progres_bar += "-"
        progres_bar += "]"
        if i != 0:

            print CURSOR_UP_ONE + ERASE_LINE + progres_bar + "{}%".format(round(float(100)/count*i, 2))
        else:
            print progres_bar + "{}%".format(round(float(100)/count*i, 2))
        handlePhoto(photo, results, vkapi)
        i += 1
    progres_bar = "["
    for j in range(50):
        progres_bar += "="
    progres_bar += "]"
    print CURSOR_UP_ONE + ERASE_LINE + progres_bar + "100%"


def getTop10(results):
    count = 0
    top10 = []
    for k, v in sorted(results.items(), key=lambda x:int(x[0]), reverse=True):
        for i in v:
            count += 1
            top10.append(i)
            if count == 10:
                return top10
    return top10



def generateTopHTML(top10, vkapi):
    print "Generating top10..."
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('localhost', 8003))

    message = """HTTP/1.1 200 OK
    Content-Type: text/html; charset=utf-8
    Content-Length: 3000
    <html>

        <body>
            {}
        </body>
    </html>
        """
    images = ""
    for top in top10:
        time.sleep(0.3)
        images += "<div><img src='{}'> </img> Likes: {}</div> ".format(top['link'], top['likes'])
    message = message.format(images)
    print message
    sock.listen(10)
    webbrowser.open_new("http://localhost:8003")
    conn, addr = sock.accept()
    print conn.recv(1024)
    conn.send(message)



def getProgressBar(now, maximum):
    progres_bar = "["
    for j in range(50):
        if j*2 < round(float(100)/maximum*now):
            progres_bar += "="
        else:
            progres_bar += "-"
    progres_bar += "]" + str(round(float(100)/maximum*now, 2))+"%"
    return progres_bar

def main(args):
    vkapi = authenticate(args.Login, args.Password)
    if args.period:
        globals()['from_date'] = time.strptime(args.period[0], '%d.%m.%Y')
        globals()['to_date'] = time.strptime(args.period[1], '%d.%m.%Y')
    else:
        globals()['from_date'] = None
        globals()['to_date'] = None
    results = {}
    if args.albums:
        if args.user:
            albums = vkapi.photos.getAlbums(owner_id=args.user)
        else:
            albums = vkapi.photos.getAlbums()
        for album in albums['items']:
            time.sleep(0.3)
            handleAlbum(album, vkapi, results)
    else:
        photos = []
        if args.user:
            count = vkapi.photos.getAll(owner_id=args.user)['count']
            i = 0
            print "Getting photos..."
            print
            while i < count:
                print CURSOR_UP_ONE + ERASE_LINE + getProgressBar(i, count)
                try:
                    photos += vkapi.photos.getAll(offset=i, owner_id=args.user, extended=1)['items']
                except Exception as e:
                    print e
                    continue
                i += 20
                time.sleep(0.3)
        else:
            count = vkapi.photos.getAll()['count']
            i = 0
            print
            while i < count:
                print CURSOR_UP_ONE + ERASE_LINE + getProgressBar(i, count)
                try:
                    photos += vkapi.photos.getAll(offset=i, extended=1)['items']
                except Exception as e:
                    print e
                    continue
                i += 20
                time.sleep(0.3)
        print CURSOR_UP_ONE + ERASE_LINE + getProgressBar(1, 1)
        print "handling photos..."
        print
        i = 0
        for photos in photos:
            print CURSOR_UP_ONE + ERASE_LINE + getProgressBar(i, count)
            i += 1
            handlePhoto(photos, results, vkapi)

    top10 = getTop10(results)
    print top10
    generateTopHTML(top10, vkapi)





if __name__ == "__main__":
    parser = argparse.ArgumentParser("VK TOP photos ")
    parser.add_argument("Login")
    parser.add_argument("Password")
    parser.add_argument("-u", "--user"  )
    parser.add_argument("-p", "--period",  nargs=2, help="example: 22.11.2014 20.05.2015")
    parser.add_argument("-a", "--albums",  help="only albums", action="store_true")
    args = parser.parse_args()
    main(args)

