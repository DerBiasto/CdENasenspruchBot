#!/usr/bin/env python3
import requests
import json
import time
import datetime
from datetime import timedelta
import urllib
from dbhelper import DBHelper

TOKEN = "451138903:AAFur2EMW82eKiiVXc0iWSyNiBpo7P_C2zs"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

db = DBHelper()

def getURL(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content
    
def getJsonFromURL(url):
    content = getURL(url)
    js = json.loads(content)
    return js
    
def getUpdates(offset=None,timeout=10):
    url = URL + "getUpdates?timeout={}".format(timeout)
    if offset:
        url += "&offset={}".format(offset)
    js = getJsonFromURL(url)
    return js
    
def getLastUpdateID(updates):
    updateIDs = []
    for update in updates["result"]:
        updateIDs.append(update["update_id"])
    return max(updateIDs)
    
def sendMessage(text, chatID, replyMarkup=None, parseMode="Markdown"):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}".format(text, chatID)
    if replyMarkup:
        url += "&reply_markup={}".format(replyMarkup)
    if parseMode:
        url += "&parse_mode={}".format(parseMode)
    getURL(url)
    
def editMessageText(text, chatID, messageID, replyMarkup=None, parseMode="Markdown"):
    text = urllib.parse.quote_plus(text)
    url = URL + "editMessageText?text={}&chat_id={}&message_id={}".format(text, chatID, messageID)
    if replyMarkup:
        url += "&reply_markup={}".format(replyMarkup)
    if parseMode:
        url += "&parse_mode={}".format(parseMode)
    getURL(url)
    
def buildInlineKeyboardDelete(userID):
    spruchlist = sorted(db.getSprueche(userID), key=lambda s: (s.active, s.time), reverse=False)
    if spruchlist == []:
        return
    else:
        keyboard = [[{"text": 'Alle Sprüche', "callback_data": '/delete {} all'.format(userID)}]]
        keyboard.append([{"text": 'Nichts löschen', "callback_data": '/delete {} stop'.format(userID)}])
        for s in spruchlist:
            keyboard.append([{"text": '{}{}'.format('(aktiv) ' if s.active == 1 else '', s.text), "callback_data": '/delete {} {}'.format(userID, s.time)}])
        replyMarkup = {"inline_keyboard": keyboard}
        return json.dumps(replyMarkup)

def buildInlineKeyboardActive(userID):
    spruchlist = sorted(db.getSprueche(userID), key=lambda s: (s.active, s.time), reverse = False)
    if spruchlist == []:
        return
    else:
        keyboard = [[{"text": 'Keinen Aktiven Spruch', "callback_data": '/active {} none'.format(userID)}]]
        for s in spruchlist:
            keyboard.append([{"text": '{}{}'.format('(aktiv) ' if s.active == 1 else '', s.text), "callback_data": '/active {} {}'.format(userID, s.time)}])
        replyMarkup = {"inline_keyboard": keyboard}
        return json.dumps(replyMarkup)
    
def handleUpdates(updates):
    for update in updates["result"]:
        if "message" in update.keys():
            try:
                msg = update["message"]
                text = msg["text"]
                chatID = msg["chat"]["id"]
                userID = msg["from"]["id"]
                userName = msg["from"]["first_name"]
                
                args = text.split(' ', 1)
                
                command = args[0].replace('@cde_nasenspruch_bot','')
                
                if command.startswith('/'):
                    if command == '/start':
                        sendMessage('Hallo! Ich bin ein Bot, um dir zu helfen, dir deine Nasensprüche zu merken!', chatID)
                    elif command == '/help':
                        sendMessage(availableCommands, chatID, parseMode=None)
                    elif command == '/neuer_spruch':
                        if len(args) > 1:
                            sendMessage('Ich habe deinen neuen Spruch _{}_ gespeichert!'.format(args[1]), chatID)
                            db.addSpruch(userID, args[1])
                        else:
                            sendMessage('Bitte gib nach dem Befehl deinen neuen Spruch ein.', chatID)
                    elif command == '/mein_spruch':
                        spruch = db.getActiveSpruch(userID)
                        if spruch == []:
                            sendMessage('Ich habe noch keinen Nasenspruch von dir gespeichert, {}.'.format(userName), chatID)
                        else:
                            sendMessage('{}: _{}_'.format(userName, spruch[0].text), chatID)
                    elif command == '/alle_meine_sprueche':
                        spruchlist = sorted(db.getSprueche(userID), key=lambda s: (s.active, s.time), reverse=True)
                        if spruchlist == []:
                            sendMessage('Ich habe noch keinen Nasenspruch von dir gespeichert, {}.'.format(userName), userID)
                        else:
                            messageList = []
                            for spruch in spruchlist:
                                messageList.append('_{}_{}'.format(spruch.text, ' (aktiv)' if spruch.active == 1 else ''))
                            
                            message = '\n'.join(messageList)  
                            sendMessage(message, userID, parseMode="Markdown")
                    elif command == '/loesche_meine_sprueche':
                        keyboard = buildInlineKeyboardDelete(userID)
                        if keyboard == None:
                            sendMessage('Ich habe noch keinen Nasenspruch von dir gespeichert.', userID)
                            continue
                        sendMessage('Lass dir alle deine gepeicherten Sprüche mit /alle_meine_sprueche anzeigen.\nWelchen Spruch möchtest du löschen?', userID, keyboard, None)
                    elif command == '/setze_aktiven_spruch':
                        keyboard = buildInlineKeyboardActive(userID)
                        if keyboard == None:
                            sendMessage('Ich habe noch keinen Nasenspruch von dir gespeichert.', userID)
                            continue
                        sendMessage('Lass dir alle deine gespeicherten Sprüche mit /alle_meine_sprueche anzeigen.\nDein aktiver Spruch ist der, der mittels /mein_Spruch ausgegeben wird. Welchen Spruch möchtest du als aktiven Spruch auswählen?', userID, keyboard, None)
                        
                                
                        
            except KeyError:
                pass        
        elif "callback_query" in update.keys():
            #try:
                cq = update["callback_query"]
                
                text = cq["data"]
                userID = cq["from"]["id"]
                chatID = cq["message"]["chat"]["id"]
                msgID = cq["message"]["message_id"]
                args = text.split(' ', 2)
                
                command = args[0].replace('@cde_nasenspruch_bot', '')
                
                if command.startswith('/'):
                    if command == '/delete':
                        if len(args) == 3:
                            if args[2] == 'all':
                                db.deleteSprueche(args[1])
                                editMessageText('Alle gespeicherten Nasensprüche wurden gelöscht', chatID, msgID)
                            elif args[2] == 'stop':
                                editMessageText('Löschvorgang beendet.', chatID, msgID)
                            else:
                                db.deleteSpruch(args[1], args[2])
                                keyboard = buildInlineKeyboardDelete(userID)
                                if keyboard == None:
                                    editMessageText('Alle gespeicherten Nasensprüche wurden gelöscht', chatID, mdgID)
                                else:
                                    editMessageText('Der gespeicherte Nasenspruch ({}) wurde gelöscht.\nMöchtest du weitere Sprüche löschen?'.format(args[2]), chatID, msgID, keyboard)
                    elif command == '/active':
                        if len(args) == 3:
                            if args[2] == 'none':
                                db.setActiveSpruch(userID)
                                editMessageText('Es ist nun kein Spruch mehr aktiv.', chatID, msgID)
                            else:
                                db.setActiveSpruch(args[1], args[2])
                                editMessageText('Aktiver Spruch wurde geändert.', chatID, msgID)
                            
            
            
            
            #except KeyError as e:
                #print('KeyError: {}'.format(e))
                #pass           
    
def main():
    db.setup()
    lastUpdateID = None
    
    while True:
        updates = getUpdates(lastUpdateID)
        try:
            if len(updates["result"]) > 0:
                lastUpdateID = getLastUpdateID(updates) + 1
                handleUpdates(updates)
            time.sleep(0.5)
        except KeyError:
            pass
        
availableCommands = '/start - Initialisiere den Bot. Dies musst du tun, damit der Bot dir private Nachrichten schicken kann.\n/help - Zeige diese Liste an\n/neuer_spruch - Gib danach einfach deinen neuen Nasenspruch ein, der Bot wird ihn sich dann merken.\n/mein_spruch - Der Bot gibt deinen aktiven Nasenspruch wieder. Wenn du keinen Nasenspruch als aktiv gesetzt hast, gibt er den neuesten wieder.\n/alle_meine_sprueche - Der Bot schickt dir (privat) eine Liste aller deiner gespeicherten Sprüche. Initialisiere hierfür zunächst den Bot, indem du ihm eine direkte Privatnachricht mit /start schickst.\n/setze_aktiven_spruch - Der Bot schickt dir eine private Nachricht, in der du einen aktiven Spruch auswählen kannst. Initialisiere hierfür zunächst den Bot.'

if __name__ == "__main__":
    main()
