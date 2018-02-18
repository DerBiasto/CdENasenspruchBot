#!/usr/bin/env python3
import requests
import json
import time
import datetime
from datetime import timedelta
import urllib.parse
from dbhelper import DBHelper
import configparser
from html import escape


class TClient:
    URL = "https://api.telegram.org/bot{}/{}"

    def __init__(self, token):
        self.token = token

    def _get_telegram_url(self, url):
        response = requests.get(self.URL.format(self.token, url))
        content = response.content.decode("utf8")
        return content

    def get_json_from_url(self, url):
        content = self._get_telegram_url(url)
        js = json.loads(content)
        return js

    def get_updates(self, offset=None, timeout=10):
        url = "getUpdates?timeout={}".format(timeout)
        if offset:
            url += "&offset={}".format(offset)
        # print(url)
        js = self.get_json_from_url(url)
        return js

    def send_message(self, text, chat_id, reply_markup=None, parse_mode="HTML"):
        text = urllib.parse.quote_plus(text)
        url = "sendMessage?text={}&chat_id={}".format(text, chat_id)
        if reply_markup:
            reply_markup = urllib.parse.quote_plus(reply_markup)
            url += "&reply_markup={}".format(reply_markup)
        if parse_mode:
            url += "&parse_mode={}".format(parse_mode)
        result = self.get_json_from_url(url)
        if not result["ok"]:
            print(result["description"])

    def edit_message_text(self, text, chat_id, message_id, reply_markup=None, parse_mode="HTML"):
        text = urllib.parse.quote_plus(text)
        url = "editMessageText?text={}&chat_id={}&message_id={}".format(text, chat_id, message_id)
        if reply_markup:
            reply_markup = urllib.parse.quote_plus(reply_markup)
            url += "&reply_markup={}".format(reply_markup)
        if parse_mode:
            url += "&parse_mode={}".format(parse_mode)
        result = self.get_json_from_url(url)
        if not result["ok"]:
            print(result["description"])


def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(update["update_id"])
    return max(update_ids)

class NasenspruchBot:
    def __init__(self, db, tclient, admins):
        """
        Initialize a NasenspruchBot object using the given database connector and telegram client object
        :param db: A DBHelper to connect to the SQLite database
        :type db: DBHelper
        :param tclient: A TClient to send messages to the Telegram API
        :type tclient: TClient
        :param admins: A list of chat_ids that have privileged access to execute management operations
        :type admins: [int]
        """
        self.db = db
        self.tclient = tclient
        self.admins = admins
        
    def dispatch_update(self, update):
        """
        Process an update received from the Telegram API in the context of this Bot.
        :param update: A Telegram update to be processed
        :type update: dict
        """
        command_handlers = {
            '/start': self._do_start,
            '/help': self._do_help,
            '/neuer_spruch': self._do_neuer_spruch,
            '/mein_spruch': self._do_mein_spruch,
            '/alle_meine_sprueche': self._do_alle_meine_sprueche,
            '/loesche_meine_sprueche': self._do_loesche_meine_sprüche,
            '/setze_aktiven_spruch': self._do_setze_aktiven_spruch
        }
        callback_handlers = {
            '/delete': self._callback_delete,
            '/active': self._callback_active
        }

        if "message" in update.keys():
            # Parse command
            args = update["message"]["text"].split(' ', 1)
            command = args[0].replace('@cde_nasenspruch_bot', '')
            chat_id = update["message"]["chat"]["id"]
            user_id = update["message"]["from"]["id"]

            # Call command handler function
            try:
                command_handlers[command](chat_id, user_id, args, update)
            except KeyError:
                if command.startswith('/'):
                    self.tclient.send_message('Unbekannter Befehl. Versuch es mal mit /help', chat_id)
                pass
        elif "callback_query" in update.keys():
            args = update["callback_query"]["data"].split(' ', 2)
            command = args[0].replace('@cde_nasenspruch_bot', '')
            chat_id = update["callback_query"]["from"]["id"]
            user_id = update["callback_query"]["from"]["id"]
            
            # Call callback handler function
            try:
                callback_handlers[command](chat_id, user_id, args, update)
            except KeyError:
                print('Unbekannter callback_query {}'.format(update["callback_query"]["data"]))
                pass
                
    def _do_start(self, chat_id, user_id, args, update):
        """
        Handle a /start command. Just send a hello to the user.
        """
        
        self.tclient.send_message('Hallo! Ich bin ein Bot, um dir zu helfen, dir deine Nasensprüche zu merken!', chat_id)
        
    def _do_help(self, chat_id, user_id, args, update):
        """
        Handle a /help command. Send a list of all available commands to the user.
        """
        
        self.tclient.send_message(
        '/start - Initialisiere den Bot. Dies musst du tun, damit der Bot dir private Nachrichten schicken kann.\n'
        '/help - Zeige diese Liste an\n'
        '/neuer_spruch - Gib danach einfach deinen neuen Nasenspruch ein, der Bot wird ihn sich dann merken.\n'
        '/mein_spruch - Der Bot gibt deinen aktiven Nasenspruch wieder. Wenn du keinen Nasenspruch als aktiv gesetzt hast, gibt er den neuesten wieder.\n'
        '/alle_meine_sprueche - Der Bot schickt dir (privat) eine Liste aller deiner gespeicherten Sprüche. Initialisiere hierfür zunächst den Bot, indem du ihm eine direkte Privatnachricht mit /start schickst.\n'
        '/loesche_meine_sprueche - Der Bot schickt dir eine private Nachricht, in der du auswählen kannst, welcher deiner gespeicherten Nasensprüche du löschen möchtest. Initialisiere hierfür zunächst den Bot.\n'
        '/setze_aktiven_spruch - Der Bot schickt dir eine private Nachricht, in der du einen aktiven Spruch auswählen kannst. Initialisiere hierfür zunächst den Bot.\n', chat_id)
    
    def _do_neuer_spruch(self, chat_id, user_id, args, update):
        """
        Handle a /neuer_spruch command.
        """
        if len(args) > 1:
            spruch = escape((args[1]))
            self.db.add_spruch(user_id, spruch)
            self.tclient.send_message('Ich habe deinen neuen Spruch <i>{}</i> gespeichert!'.format(spruch), chat_id)
        else:
            self.tclient.send_message('Bitte gib nach dem Befehl deinen neuen Spruch ein.', chat_id)
        
    def _do_mein_spruch(self, chat_id, user_id, args, update):
        """
        Handle a /mein_spruch command
        """
        spruch = self.db.get_active_spruch(user_id)
        user_name = update["message"]["from"]["first_name"]
        
        if not spruch:
            self.tclient.send_message('Ich habe noch keinen Nasenspruch von dir gespeichert, {}.'.format(user_name), chat_id)
        else:
            self.tclient.send_message('{}: <i>{}</i>'.format(user_name, spruch.text), chat_id)
        
    def _do_alle_meine_sprueche(self, chat_id, user_id, args, update):
        """
        Handle a /alle_meine_sprueche command.
        """
        spruchlist = sorted(self.db.get_sprueche(user_id), key=lambda s: (s.active, s.time), reverse=True)
        user_name = update["message"]["from"]["first_name"]
        
        if spruchlist == []:
            self.tclient.send_message('Ich habe noch keinen Nasenspruch von dir gespeichert, {}.'.format(user_name), user_id)
        else:
            messageList = []
            for spruch in spruchlist:
                messageList.append('<i>{}</i>{}'.format(spruch.text, ' (aktiv)' if spruch.active == 1 else ''))
            
            message = '\n'.join(messageList)  
            self.tclient.send_message(message, user_id)
            
    def _do_loesche_meine_sprüche(self, chat_id, user_id, args, update):
        """
        Handle a /loesche_meine_sprueche command
        """
                
        keyboard = self.build_inline_keyboard_delete(user_id)
        if keyboard == None:
            self.tclient.send_message('Ich habe noch keinen Nasenspruch von dir gespeichert.', user_id)
            return
        self.tclient.send_message('Lass dir alle deine gepeicherten Sprüche mit /alle_meine_sprueche anzeigen.\nWelchen Spruch möchtest du löschen?', user_id, keyboard)
    
    def build_inline_keyboard_delete(self, user_id):
        """
        Helper function that generates an inline-keyboard from which the user can choose one or more items to delete.
        """
        
        spruchlist = sorted(self.db.get_sprueche(user_id), key=lambda s: (s.active, s.time), reverse=False)
        if spruchlist == []:
            return
        else:
            keyboard = [[{"text": 'Alle Sprüche', "callback_data": '/delete {} all'.format(user_id)}]]
            keyboard.append([{"text": 'Nichts löschen', "callback_data": '/delete {} stop'.format(user_id)}])
            for s in spruchlist:
                keyboard.append([{"text": "{}{}".format('(aktiv) ' if s.active == 1 else '', s.text), "callback_data": '/delete {} {}'.format(user_id, s.id)}])
            reply_markup = {"inline_keyboard": keyboard}
            return json.dumps(reply_markup)
            
    def _callback_delete(self, chat_id, user_id, args, update):
        """
        Handle a /delete callback_query.
        """
        msg_id = update["callback_query"]["message"]["message_id"]
        
        if len(args) == 3 and args[1] == str(user_id):
            if args[2] == 'all':
                self.db.delete_sprueche(args[1])
                self.tclient.edit_message_text('Alle gespeicherten Nasensprüche wurden gelöscht', chat_id, msg_id)
            elif args[2] == 'stop':
                self.tclient.edit_message_text('Löschvorgang beendet.', chat_id, msg_id)
            else:
                self.db.delete_spruch(args[1], args[2])
                keyboard = self.build_inline_keyboard_delete(user_id)
                if keyboard == None:
                    self.tclient.edit_message_text('Alle gespeicherten Nasensprüche wurden gelöscht', chat_id, msg_id)
                else:
                    self.tclient.edit_message_text('Nasenspruch wurde gelöscht.\nMöchtest du weitere Sprüche löschen?'.format(args[2]), chat_id, msg_id, keyboard)
            
    def _do_setze_aktiven_spruch(self, chat_id, user_id, args, update):
        """
        Handle a /loesche_meine_sprueche command.
        """
        
        keyboard = self.build_inline_keyboard_active(user_id)
        if keyboard == None:
            self.tclient.send_message('Ich habe noch keinen Nasenspruch von dir gespeichert.', user_id)
            return
        self.tclient.send_message('Lass dir alle deine gespeicherten Sprüche mit /alle_meine_sprueche anzeigen.\nDein aktiver Spruch ist der, der mittels /mein_Spruch ausgegeben wird. Welchen Spruch möchtest du als aktiven Spruch auswählen?', user_id, keyboard)

    def build_inline_keyboard_active(self, user_id):
        """
        Helper function that generates an inline keyboard from which the user can chooe a Nasenspruch to set as active
        """
        
        spruchlist = sorted(self.db.get_sprueche(user_id), key=lambda s: (s.active, s.time), reverse = False)
        if spruchlist == []:
            return
        else:
            keyboard = [[{"text": 'Keinen Aktiven Spruch', "callback_data": '/active {} none'.format(user_id)}]]
            for s in spruchlist:
                keyboard.append([{"text": '{}{}'.format('(aktiv) ' if s.active == 1 else '', s.text), "callback_data": '/active {} {}'.format(user_id, s.id)}])
            reply_markup = {"inline_keyboard": keyboard}
            return json.dumps(reply_markup)
            
    def _callback_active(self, chat_id, user_id, args, update):
        """
        Handle a /active callback_query
        """
        msg_id = update["callback_query"]["message"]["message_id"]
        
        if len(args) == 3 and args[1] == str(user_id):
            if args[2] == 'none':
                self.db.set_active_spruch(user_id)
                self.tclient.edit_message_text('Es ist nun kein Spruch mehr aktiv.', chat_id, msg_id)
            else:
                self.db.set_active_spruch(args[1], args[2])
                self.tclient.edit_message_text('Aktiver Spruch wurde geändert.', chat_id, msg_id)
        
    def _do_delete_latest(self, chat_id, user_id, args, update):
        """
        Handle a /delete_latest command. Only really needed for debugging, when /loesche_meine_sprueche produces an error
        """
        spruchlist = sorted(self.db.get_sprueche(userID), key=lambda s: (s.time), reverse = True)
        self.db.delete_spruch(userID, spruchlist[0].id)
        
def main():
    # Setup DB
    db = DBHelper('nasensprueche.sqlite')
    db.setup()
    
    # Read configuration and setup Telegram client
    config = configparser.ConfigParser()
    config.read('config.ini')
    tclient = TClient(config['telegram']['token'])
    admins = [int(x) for x in config['telegram']['admins'].split()]
    nasenspruch_bot = NasenspruchBot(db, tclient, admins)

    last_update_id = None
    
    while True:
        updates = tclient.get_updates(last_update_id)
        try:
            # Process updates from Telegram
            if len(updates["result"]) > 0:
                last_update_id = get_last_update_id(updates) + 1
                for update in updates["result"]:
                    nasenspruch_bot.dispatch_update(update)

            # Sleep for half a second
            time.sleep(0.5)
        except KeyError:
            pass
        

if __name__ == "__main__":
    main()
